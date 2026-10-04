"""Owner-scoped Translation Memory/cache followed by serialized NLLB inference."""
import re
import threading
import time
from typing import Any, Optional, Tuple

import torch

from app.core.config import DEVICE, SOURCE_LANG, TARGET_LANG, settings
from app.services import translation_memory as tm
from app.services.translation_cache import GLOBAL_TRANSLATION_CACHE

# Tokenizer.src_lang is mutable and shared by both HTTP and websocket workers.
_inference_lock = threading.RLock()
_NLLB_LANGUAGES = {"vi": "vie_Latn", "en": "eng_Latn"}


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


def _translate_nllb(text: str, source_lang: str, target_lang: str) -> str:
    with _inference_lock:
        model, tokenizer = _get_nllb()
        tokenizer.src_lang = source_lang
        inputs = tokenizer(text, return_tensors="pt").to(DEVICE)
        target_token_id = tokenizer.convert_tokens_to_ids(target_lang)
        if target_token_id is None or target_token_id == getattr(tokenizer, "unk_token_id", None):
            raise ValueError(f"Invalid target language: {target_lang}")
        with torch.inference_mode():
            translated_tokens = model.generate(
                **inputs,
                forced_bos_token_id=target_token_id,
                max_new_tokens=128,
                num_beams=settings.TRANSLATION_BEAM_SIZE,
                no_repeat_ngram_size=3,
            )
        return tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0].lstrip("- ").strip()


def translate_text(
    text: str, context: str = "", source_lang: Optional[str] = None,
    target_lang: Optional[str] = None, client_id: Optional[str] = None,
    *, use_cache: bool = True,
) -> dict:
    start = time.monotonic()
    text = _normalize_stt_text(text)
    if not text:
        raise ValueError("No text to translate")
    resolved_source = source_lang or SOURCE_LANG
    resolved_target = target_lang or TARGET_LANG
    resolved_source = _NLLB_LANGUAGES.get(tm.normalize_lang_code(resolved_source), resolved_source)
    resolved_target = _NLLB_LANGUAGES.get(tm.normalize_lang_code(resolved_target), resolved_target)
    cache_owner = client_id or "global:anonymous"
    # Capture before TM/inference: a dictionary change cannot publish an old result
    # into the new version, even if generation completes after the change.
    snapshot = GLOBAL_TRANSLATION_CACHE.get_version_snapshot(cache_owner) if use_cache else None
    if use_cache:
        cached = GLOBAL_TRANSLATION_CACHE.get(cache_owner, resolved_source, resolved_target, text)
        if cached is not None:
            return {"translated_text": cached, "latency": round(max(0.015, time.monotonic() - start), 3), "source": "cache"}

    translated = tm.lookup(text, client_id, resolved_source, resolved_target) if client_id else None
    if translated is None:
        translated = tm.lookup(text, "global:approved", resolved_source, resolved_target)
    if translated is not None:
        source = "translation_memory"
    else:
        translated = tm.lookup_fuzzy(text, client_id, resolved_source, resolved_target) if client_id else None
        if translated is None:
            translated = tm.lookup_fuzzy(text, "global:approved", resolved_source, resolved_target)
        if translated is not None:
            source = "translation_memory_fuzzy"
        else:
            translated = _translate_nllb(text, resolved_source, resolved_target)
            source = "nllb_model"
    if use_cache and translated:
        GLOBAL_TRANSLATION_CACHE.put(
            cache_owner, resolved_source, resolved_target, text, translated,
            expected_version=snapshot,
        )
    return {"translated_text": translated, "latency": round(max(0.015, time.monotonic() - start), 3), "source": source}
