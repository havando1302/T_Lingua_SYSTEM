"""Owner-scoped Translation Memory/cache followed by serialized NLLB inference."""
import re
import threading
import time
from collections import Counter
from contextvars import ContextVar
from typing import Any, Optional, Tuple

import torch

from app.core.config import DEVICE, SOURCE_LANG, TARGET_LANG, settings
from app.services import translation_memory as tm
from app.services.translation_cache import GLOBAL_TRANSLATION_CACHE
from app.utils.translation_safety import INTERNAL_PLACEHOLDER, PROTECTED_ENTITY, has_internal_placeholder, is_glossary_term

# Tokenizer.src_lang is mutable and shared by both HTTP and websocket workers.
_inference_lock = threading.RLock()
TRANSLATION_POLICY_VERSION = "source-fidelity-v2.1"
_request_glossary: ContextVar[list[dict[str, str | None]] | None] = ContextVar(
    "translation_request_glossary", default=None,
)
_last_quality_result: ContextVar[tuple[list[str], bool]] = ContextVar(
    "translation_quality_result", default=([], False),
)
_NLLB_LANGUAGES = {"vi": "vie_Latn", "en": "eng_Latn"}
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")
# Numbers/codes are validated after natural decoding. ASCII placeholders are
# reserved for a constrained retry because they can disrupt sentence meaning.
_PROTECTED_ENTITY = PROTECTED_ENTITY
_PLACEHOLDER_PREFIX = "ZXQTLENTITY"
_GLOSSARY_PLACEHOLDER_PREFIX = "ZXQTLGLOSSARY"
_UNRESOLVED_PLACEHOLDER = INTERNAL_PLACEHOLDER
_NEGATION_PATTERNS = {
    "vie_Latn": re.compile(r"(?<!\w)(?:không|chưa|chẳng|chả|đừng)(?!\w)", re.IGNORECASE),
    "eng_Latn": re.compile(
        r"(?<!\w)(?:not|no|never|without|cannot|\w+n['’]t)(?!\w)",
        re.IGNORECASE,
    ),
}


def _get_nllb() -> Tuple[Any, Any]:
    from app.ai.model_manager import model_manager
    if model_manager.nllb_model is None or model_manager.nllb_tokenizer is None:
        raise RuntimeError("NLLB model and tokenizer have not been loaded")
    return model_manager.nllb_model, model_manager.nllb_tokenizer


def _normalize_stt_text(text: str) -> str:
    if not text:
        return text
    text = re.sub(r"\s+", " ", text)
    # Preserve decimal commas (1,5) while cleaning STT punctuation artifacts.
    text = re.sub(r"(?<!\d)\s*,\s*|\s*,\s*(?!\d)", ", ", text)
    text = re.sub(r",\s*,+", ", ", text)
    text = re.sub(r"([,.!?])\1+", r"\1", text)
    return text.strip()


def _split_translation_segments(text: str) -> list[str]:
    """Split only at real sentence boundaries, never inside values like 3.1."""
    segments = [part.strip() for part in _SENTENCE_BOUNDARY.split(text) if part.strip()]
    # Bound long unpunctuated speech without discarding any words.
    return [" ".join(words[start:start + 80])
            for segment in (segments or [text]) for words in [segment.split()]
            for start in range(0, len(words), 80)]


def _protect_translation_entities(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Replace number/code tokens with stable neutral placeholders."""
    protected: list[tuple[str, str]] = []

    def replace(match: re.Match[str]) -> str:
        # Glossary placeholders contain an index too. Protecting them a second
        # time hides them from restoration and leaks the glossary marker.
        if has_internal_placeholder(match.group(0)):
            return match.group(0)
        marker = f"{_PLACEHOLDER_PREFIX}{len(protected)}Q"
        protected.append((marker, match.group(0)))
        return marker

    return _PROTECTED_ENTITY.sub(replace, text), protected


def _restore_translation_entities(
    translated: str, protected: list[tuple[str, str]],
) -> str:
    restored = translated
    for marker, original in protected:
        restored = re.sub(
            _tolerant_marker_pattern(marker), lambda _match: original,
            restored, flags=re.IGNORECASE,
        )
    return restored


def _tolerant_marker_pattern(marker: str) -> str:
    """Match harmless spacing/punctuation mutations introduced by NLLB."""
    return r"[\s._-]*".join(re.escape(char) for char in marker)


def _protect_glossary_entities(
    text: str,
    glossary_entries: list[dict[str, str | None]],
) -> tuple[str, list[tuple[str, str, str]]]:
    """Replace approved terms with placeholders carrying canonical targets."""
    protected: list[tuple[str, str, str]] = []
    updated = text
    entries = sorted(
        glossary_entries,
        key=lambda row: len(str(row.get("source_text") or "")),
        reverse=True,
    )
    for row in entries:
        source = str(row.get("source_text") or "").strip()
        target = str(row.get("translated_text") or "").strip()
        if not is_glossary_term(source) or not target or has_internal_placeholder(target):
            continue
        pattern = re.compile(rf"(?<!\w){re.escape(source)}(?!\w)", re.IGNORECASE)
        if not pattern.search(updated):
            continue
        marker = f"{_GLOSSARY_PLACEHOLDER_PREFIX}{len(protected)}Q"
        updated = pattern.sub(marker, updated)
        protected.append((marker, source, target))
    return updated, protected


def _vietnamese_proper_names(text: str, source_lang: str) -> list[dict[str, str]]:
    """Preserve consecutive capitalized Vietnamese name words from the source.

    This deliberately excludes single words and English title-case phrases.
    Explicit approved glossary translations take precedence over these hints.
    """
    if tm.normalize_lang_code(source_lang) != "vi":
        return []
    tokens = list(re.finditer(r"[^\W\d_]+", text, flags=re.UNICODE))
    groups: list[list[re.Match[str]]] = []
    for token in tokens:
        word = token.group()
        if not word[0].isupper() or len(word) < 2 or word.isupper():
            continue
        if groups and text[groups[-1][-1].end():token.start()].isspace():
            groups[-1].append(token)
        else:
            groups.append([token])
    names = []
    for group in groups:
        if not 2 <= len(group) <= 6:
            continue
        name = text[group[0].start():group[-1].end()]
        names.append({"source_text": name, "translated_text": name})
    return names


def _restore_glossary_entities(
    translated: str, protected: list[tuple[str, str, str]],
) -> str:
    restored = translated
    for marker, _source, target in protected:
        restored = re.sub(
            _tolerant_marker_pattern(marker), lambda _match: target,
            restored, flags=re.IGNORECASE,
        )
    return restored


def _translation_quality_issues(
    source_text: str,
    translated_text: str,
    source_lang: str,
    target_lang: str,
    glossary_entities: list[tuple[str, str, str]],
) -> list[str]:
    """Return deterministic high-risk losses suitable for retry/audit."""
    issues: list[str] = []
    expected_entities = Counter(value.casefold() for value in _PROTECTED_ENTITY.findall(source_text))
    actual_entities = Counter(value.casefold() for value in _PROTECTED_ENTITY.findall(translated_text))
    if expected_entities - actual_entities:
        issues.append("missing_number_or_code")
    for _marker, _source, target in glossary_entities:
        if target.casefold() not in translated_text.casefold():
            issues.append("missing_glossary_term")
            break
    negation_matches = list(_NEGATION_PATTERNS.get(source_lang, re.compile(r"$^")).finditer(source_text))
    if source_lang == "vie_Latn":
        # Final "... chưa?" asks "... yet?"; it does not require English "not".
        negation_matches = [match for match in negation_matches
                            if not (match.group().casefold() == "chưa" and not source_text[match.end():].strip(" .!?"))]
    source_has_negation = bool(negation_matches)
    target_has_negation = bool(
        _NEGATION_PATTERNS.get(target_lang, re.compile(r"$^")).search(translated_text)
    )
    if source_has_negation and not target_has_negation:
        issues.append("missing_negation")
    if _UNRESOLVED_PLACEHOLDER.search(translated_text):
        issues.append("unresolved_placeholder")
    return issues


def _translation_token_budget(input_ids: Any, attention_mask: Any = None) -> int:
    """Bound decoding to the longest unpadded input in the current batch."""
    if input_ids is None:
        # Compatibility with lightweight/custom tokenizer adapters which do
        # not expose tensor metadata. The normal Hugging Face path is dynamic.
        return 64
    if attention_mask is not None:
        source_tokens = int(attention_mask.sum(dim=1).max().item())
    else:
        source_tokens = int(input_ids.shape[-1])
    return min(512, max(32, int(source_tokens * 2.0) + 16))


def _repair_vietnamese_fragment(model, tokenizer, source, translated, target_token_id, token_budget):
    """Repair rare VI→EN noun-phrase outputs without a phrase dictionary."""
    from app.services.translation_fidelity import (
        looks_like_english_fragment, reverse_source_scores, select_fragment_repair,
        vietnamese_aspect_variants,
    )
    if not looks_like_english_fragment(translated):
        return translated
    variants = vietnamese_aspect_variants(source)
    if not variants:
        return translated
    inputs = tokenizer(variants, return_tensors="pt", padding=True, truncation=False).to(DEVICE)
    with torch.inference_mode():
        output = model.generate(
            **inputs, forced_bos_token_id=target_token_id, max_length=None,
            max_new_tokens=token_budget, num_beams=3, num_return_sequences=3,
            length_penalty=getattr(settings, "TRANSLATION_LENGTH_PENALTY", 1.2), use_cache=True,
        )
    decoded = tokenizer.batch_decode(output, skip_special_tokens=True)
    candidates = list(dict.fromkeys([translated, *(value.strip() for value in decoded if value.strip())]))
    risks = [_quality_risk(_translation_quality_issues(source, value, "vie_Latn", "eng_Latn", []))
             for value in candidates]
    reverse = reverse_source_scores(model, tokenizer, source, candidates, "vie_Latn", "eng_Latn", DEVICE)
    chosen = select_fragment_repair(candidates, reverse, risks)
    return candidates[chosen]


def _translate_nllb_candidate(
    text: str,
    source_lang: str,
    target_lang: str,
    glossary_entries: list[dict[str, str | None]],
    beam_size: int,
    *, protect_names: bool = True, mask_terms: bool = False, mask_numbers: bool = True,
) -> tuple[str, list[tuple[str, str, str]]]:
    with _inference_lock:
        model, tokenizer = _get_nllb()
        tokenizer.src_lang = source_lang
        target_token_id = tokenizer.convert_tokens_to_ids(target_lang)
        if target_token_id is None or target_token_id == getattr(tokenizer, "unk_token_id", None):
            raise ValueError(f"Invalid target language: {target_lang}")
        # Protect full glossary phrases before their embedded numbers/codes.
        approved_sources = {str(row.get("source_text") or "").strip().casefold() for row in glossary_entries}
        name_entries = [row for row in (_vietnamese_proper_names(text, source_lang) if protect_names else [])
                        if row["source_text"].casefold() not in approved_sources]
        protected_text, glossary_entities = _protect_glossary_entities(
            text, glossary_entries + name_entries,
        )
        # Natural encoder input preserves subjects, predicates and grammar.
        # Arbitrary ASCII markers can be dropped or translated as ordinary words.
        if mask_terms:
            if mask_numbers:
                protected_text, protected_entities = _protect_translation_entities(protected_text)
            else:
                protected_entities = []
        else:
            protected_text, protected_entities = text, []
        segments = _split_translation_segments(protected_text)
        batch_size = getattr(settings, "TRANSLATION_SENTENCE_BATCH_SIZE", 4)
        translated_segments: list[str] = []
        for start in range(0, len(segments), batch_size):
            batch = segments[start:start + batch_size]
            inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=False).to(DEVICE)
            input_ids = getattr(inputs, "input_ids", None)
            attention_mask = getattr(inputs, "attention_mask", None)
            if isinstance(inputs, dict):
                input_ids = input_ids if input_ids is not None else inputs.get("input_ids")
                attention_mask = attention_mask if attention_mask is not None else inputs.get("attention_mask")
            token_budget = _translation_token_budget(input_ids, attention_mask)
            if input_ids is not None and input_ids.shape[-1] > 512:
                raise ValueError("Translation segment exceeds 512 tokens; split at sentence boundaries")
            rerank = (not mask_terms and beam_size > 1
                      and getattr(settings, "TRANSLATION_FIDELITY_RERANK", True)
                      and hasattr(model, "forward") and hasattr(tokenizer, "tgt_lang"))
            generation_options = {"length_penalty": getattr(settings, "TRANSLATION_LENGTH_PENALTY", 1.2)}
            if rerank:
                generation_options.update(num_return_sequences=min(3, beam_size),
                                          return_dict_in_generate=True, output_scores=True)
            with torch.inference_mode():
                translated_tokens = model.generate(
                    **inputs,
                    forced_bos_token_id=target_token_id,
                    max_length=None,
                    max_new_tokens=token_budget,
                    num_beams=beam_size,
                    use_cache=True,
                    **generation_options,
                )
            if rerank:
                from app.services.translation_fidelity import reverse_source_scores, select_faithful_candidate
                count = min(3, beam_size)
                decoded_all = tokenizer.batch_decode(translated_tokens.sequences, skip_special_tokens=True)
                forward = translated_tokens.sequences_scores.float().cpu().tolist()
                del translated_tokens
                decoded = []
                for index, segment in enumerate(batch):
                    candidates = decoded_all[index * count:(index + 1) * count]
                    risks = [_quality_risk(_translation_quality_issues(segment, value, source_lang, target_lang, []))
                             for value in candidates]
                    reverse = reverse_source_scores(model, tokenizer, segment, candidates, source_lang, target_lang, DEVICE)
                    chosen = select_faithful_candidate(candidates, forward[index * count:(index + 1) * count], reverse, risks)
                    selected = candidates[chosen]
                    if source_lang == "vie_Latn" and target_lang == "eng_Latn":
                        selected = _repair_vietnamese_fragment(
                            model, tokenizer, segment, selected, target_token_id, token_budget,
                        )
                    decoded.append(selected)
            else:
                decoded = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)
            translated_segments.extend(part.lstrip("- ").strip() for part in decoded if part.strip())
        if len(translated_segments) != len(segments):
            raise RuntimeError("NLLB returned an incomplete sentence batch")
        restored = " ".join(translated_segments)
        if mask_terms:
            restored = _restore_glossary_entities(restored, glossary_entities)
            restored = _restore_translation_entities(restored, protected_entities)
            if (protected_entities or glossary_entities) and re.search(r"\bQ\b", restored) and not re.search(r"\bQ\b", text):
                raise RuntimeError("NLLB returned a fragment of an internal placeholder")
        return restored, glossary_entities


def _quality_risk(issues):
    return ("unresolved_placeholder" in issues, "missing_number_or_code" in issues,
            "missing_negation" in issues, "missing_glossary_term" in issues, len(issues))


def _translate_nllb_with_quality(
    text: str,
    source_lang: str,
    target_lang: str,
    glossary_entries: list[dict[str, str | None]] | None = None,
) -> tuple[str, list[str], bool]:
    glossary_entries = glossary_entries or []
    first, entities = _translate_nllb_candidate(
        text, source_lang, target_lang, glossary_entries, settings.TRANSLATION_BEAM_SIZE,
    )
    first_issues = _translation_quality_issues(
        text, first, source_lang, target_lang, entities,
    )
    retry_beam = getattr(settings, "TRANSLATION_RETRY_BEAM_SIZE", 3)
    if not first_issues:
        return first, first_issues, False
    try:
        retry, retry_entities = _translate_nllb_candidate(
            text, source_lang, target_lang, glossary_entries, max(retry_beam, settings.TRANSLATION_BEAM_SIZE),
            protect_names=True, mask_terms=True, mask_numbers="missing_number_or_code" in first_issues,
        )
    except RuntimeError:
        if "unresolved_placeholder" in first_issues or "missing_number_or_code" in first_issues:
            raise
        return first, [*first_issues, "constraint_retry_failed"], True
    retry_issues = _translation_quality_issues(
        text, retry, source_lang, target_lang, retry_entities,
    )
    if _quality_risk(retry_issues) < _quality_risk(first_issues):
        selected, selected_issues = retry, retry_issues
    else:
        selected, selected_issues = first, first_issues
    if "unresolved_placeholder" in selected_issues:
        raise RuntimeError("NLLB returned an unresolved internal placeholder")
    if "missing_number_or_code" in selected_issues:
        raise RuntimeError("NLLB could not preserve source numbers or codes")
    return selected, selected_issues, True


def _translate_nllb(text: str, source_lang: str, target_lang: str) -> str:
    """Stable inference seam with approved glossary and quality validation."""
    from app.services.semantic_service import get_runtime_glossary

    glossary = _request_glossary.get()
    if glossary is None:
        glossary = get_runtime_glossary(None, source_lang, target_lang)
    translated, issues, retried = _translate_nllb_with_quality(
        text, source_lang, target_lang,
        glossary,
    )
    _last_quality_result.set((issues, retried))
    return translated


def translate_text(
    text: str, context: str = "", source_lang: Optional[str] = None,
    target_lang: Optional[str] = None, client_id: Optional[str] = None,
    *, use_cache: bool = True,
) -> dict:
    start = time.monotonic()
    text = _normalize_stt_text(text)
    if not text:
        raise ValueError("No text to translate")
    if has_internal_placeholder(text):
        raise ValueError("Source text contains an internal translation placeholder")
    resolved_source = source_lang or SOURCE_LANG
    resolved_target = target_lang or TARGET_LANG
    resolved_source = _NLLB_LANGUAGES.get(tm.normalize_lang_code(resolved_source), resolved_source)
    resolved_target = _NLLB_LANGUAGES.get(tm.normalize_lang_code(resolved_target), resolved_target)
    cache_owner = client_id or "global:anonymous"
    repository = tm.get_tm_repository()
    # Capture before TM/inference: a dictionary change cannot publish an old result
    # into the new version, even if generation completes after the change.
    snapshot = GLOBAL_TRANSLATION_CACHE.get_version_snapshot(cache_owner) if use_cache else None
    if use_cache:
        cached = GLOBAL_TRANSLATION_CACHE.get(cache_owner, resolved_source, resolved_target, text)
        if cached is not None and not has_internal_placeholder(cached):
            return {"translated_text": cached, "latency": round(max(0.015, time.monotonic() - start), 3),
                    "source": "cache", "translation_policy": TRANSLATION_POLICY_VERSION}

    translated = repository.lookup(text, client_id, resolved_source, resolved_target) if client_id else None
    if translated is None or has_internal_placeholder(translated):
        translated = repository.lookup(text, "global:approved", resolved_source, resolved_target)
    if translated is not None and has_internal_placeholder(translated):
        translated = None
    if translated is not None:
        source = "translation_memory"
    else:
        fuzzy_threshold = getattr(settings, "TRANSLATION_FUZZY_THRESHOLD", 0.97)
        translated = repository.lookup_fuzzy(
            text, client_id, resolved_source, resolved_target,
            threshold=fuzzy_threshold,
        ) if client_id else None
        if translated is None or has_internal_placeholder(translated):
            translated = repository.lookup_fuzzy(
                text, "global:approved", resolved_source, resolved_target,
                threshold=fuzzy_threshold,
            )
        if translated is not None and has_internal_placeholder(translated):
            translated = None
        if translated is not None:
            source = "translation_memory_fuzzy"
        else:
            # Keep the public inference seam stable for cache/runtime callers.
            # The wrapper performs glossary protection, validation, and retry.
            from app.services.semantic_service import get_runtime_glossary

            token = _request_glossary.set(
                get_runtime_glossary(client_id, resolved_source, resolved_target),
            )
            _last_quality_result.set(([], False))
            try:
                translated = _translate_nllb(text, resolved_source, resolved_target)
                quality_warnings, quality_retried = _last_quality_result.get()
            finally:
                _request_glossary.reset(token)
            source = "nllb_model"
    if translated and has_internal_placeholder(translated):
        raise RuntimeError("Translation returned an unresolved internal placeholder")
    if use_cache and translated and (source != "nllb_model" or not quality_warnings):
        GLOBAL_TRANSLATION_CACHE.put(
            cache_owner, resolved_source, resolved_target, text, translated,
            expected_version=snapshot,
        )
    result = {
        "translated_text": translated,
        "latency": round(max(0.015, time.monotonic() - start), 3),
        "source": source,
        "translation_policy": TRANSLATION_POLICY_VERSION,
    }
    if source == "nllb_model":
        result["quality_warnings"] = quality_warnings
        result["quality_retried"] = quality_retried
    return result
