"""Owner-scoped Translation Memory/cache followed by serialized NLLB inference."""
import re
import threading
import time
from contextvars import ContextVar
from typing import Any, Optional, Tuple

import torch

from app.core.config import DEVICE, SOURCE_LANG, TARGET_LANG, settings
from app.services import translation_memory as tm
from app.services.translation_cache import GLOBAL_TRANSLATION_CACHE
from app.utils.translation_safety import INTERNAL_PLACEHOLDER, has_internal_placeholder, is_glossary_term

# Tokenizer.src_lang is mutable and shared by both HTTP and websocket workers.
_inference_lock = threading.RLock()
_request_glossary: ContextVar[list[dict[str, str | None]] | None] = ContextVar(
    "translation_request_glossary", default=None,
)
_last_quality_result: ContextVar[tuple[list[str], bool]] = ContextVar(
    "translation_quality_result", default=([], False),
)
_NLLB_LANGUAGES = {"vi": "vie_Latn", "en": "eng_Latn"}
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")
# NLLB is good at preserving neutral ASCII placeholders, but can translate or
# omit identifiers such as H3, RX11, 4.0 and 08:30 when they are left in the
# sentence.  Protect only tokens that contain digits; ordinary words and names
# still receive normal grammatical translation.
_PROTECTED_ENTITY = re.compile(
    r"(?<!\w)[A-Za-z]*\d+(?:[.,:/-]\d+)*[A-Za-z%]*(?!\w)", re.IGNORECASE
)
_PLACEHOLDER_PREFIX = "ZXQTLENTITY"
_GLOSSARY_PLACEHOLDER_PREFIX = "ZXQTLGLOSSARY"
_UNRESOLVED_PLACEHOLDER = INTERNAL_PLACEHOLDER
_NEGATION_PATTERNS = {
    "vie_Latn": re.compile(r"(?<!\w)(?:không|chưa|chẳng|chả|đừng)(?!\w)", re.IGNORECASE),
    "eng_Latn": re.compile(
        r"(?<!\w)(?:not|no|never|without|cannot|can't|won't|don't|didn't|isn't|aren't)(?!\w)",
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
    return segments or [text]


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
    expected_entities = [value.casefold() for value in _PROTECTED_ENTITY.findall(source_text)]
    actual_entities = [value.casefold() for value in _PROTECTED_ENTITY.findall(translated_text)]
    if any(value not in actual_entities for value in expected_entities):
        issues.append("missing_number_or_code")
    for _marker, _source, target in glossary_entities:
        if target.casefold() not in translated_text.casefold():
            issues.append("missing_glossary_term")
            break
    source_has_negation = bool(
        _NEGATION_PATTERNS.get(source_lang, re.compile(r"$^")).search(source_text)
    )
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
    return min(128, max(24, int(source_tokens * 1.6) + 12))


def _translate_nllb_candidate(
    text: str,
    source_lang: str,
    target_lang: str,
    glossary_entries: list[dict[str, str | None]],
    beam_size: int,
) -> tuple[str, list[tuple[str, str, str]]]:
    with _inference_lock:
        model, tokenizer = _get_nllb()
        tokenizer.src_lang = source_lang
        target_token_id = tokenizer.convert_tokens_to_ids(target_lang)
        if target_token_id is None or target_token_id == getattr(tokenizer, "unk_token_id", None):
            raise ValueError(f"Invalid target language: {target_lang}")
        # Protect full glossary phrases before their embedded numbers/codes.
        protected_text, glossary_entities = _protect_glossary_entities(
            text, glossary_entries,
        )
        protected_text, protected_entities = _protect_translation_entities(protected_text)
        segments = _split_translation_segments(protected_text)
        batch_size = getattr(settings, "TRANSLATION_SENTENCE_BATCH_SIZE", 4)
        translated_segments: list[str] = []
        for start in range(0, len(segments), batch_size):
            batch = segments[start:start + batch_size]
            inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True).to(DEVICE)
            input_ids = getattr(inputs, "input_ids", None)
            attention_mask = getattr(inputs, "attention_mask", None)
            if isinstance(inputs, dict):
                input_ids = input_ids if input_ids is not None else inputs.get("input_ids")
                attention_mask = attention_mask if attention_mask is not None else inputs.get("attention_mask")
            token_budget = _translation_token_budget(input_ids, attention_mask)
            with torch.inference_mode():
                translated_tokens = model.generate(
                    **inputs,
                    forced_bos_token_id=target_token_id,
                    max_length=None,
                    max_new_tokens=token_budget,
                    num_beams=beam_size,
                    use_cache=True,
                )
            decoded = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)
            translated_segments.extend(part.lstrip("- ").strip() for part in decoded if part.strip())
        if len(translated_segments) != len(segments):
            raise RuntimeError("NLLB returned an incomplete sentence batch")
        restored = _restore_glossary_entities(" ".join(translated_segments), glossary_entities)
        restored = _restore_translation_entities(restored, protected_entities)
        return restored, glossary_entities


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
    if not first_issues or retry_beam <= settings.TRANSLATION_BEAM_SIZE:
        if "unresolved_placeholder" in first_issues:
            raise RuntimeError("NLLB returned an unresolved internal placeholder")
        return first, first_issues, False
    retry, retry_entities = _translate_nllb_candidate(
        text, source_lang, target_lang, glossary_entries, retry_beam,
    )
    retry_issues = _translation_quality_issues(
        text, retry, source_lang, target_lang, retry_entities,
    )
    if ("unresolved_placeholder" in first_issues and "unresolved_placeholder" not in retry_issues) or (
        ("unresolved_placeholder" in retry_issues) == ("unresolved_placeholder" in first_issues)
        and len(retry_issues) < len(first_issues)
    ):
        selected, selected_issues = retry, retry_issues
    else:
        selected, selected_issues = first, first_issues
    if "unresolved_placeholder" in selected_issues:
        raise RuntimeError("NLLB returned an unresolved internal placeholder")
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
            return {"translated_text": cached, "latency": round(max(0.015, time.monotonic() - start), 3), "source": "cache"}

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
    if use_cache and translated:
        GLOBAL_TRANSLATION_CACHE.put(
            cache_owner, resolved_source, resolved_target, text, translated,
            expected_version=snapshot,
        )
    result = {
        "translated_text": translated,
        "latency": round(max(0.015, time.monotonic() - start), 3),
        "source": source,
    }
    if source == "nllb_model":
        result["quality_warnings"] = quality_warnings
        result["quality_retried"] = quality_retried
    return result
