"""GPU Whisper adapter with the small interface used by whisper_service."""

from json import JSONDecodeError
from types import SimpleNamespace

import torch
from safetensors import SafetensorError
from transformers import WhisperForConditionalGeneration, WhisperProcessor


def max_decode_tokens(sample_count: int, sample_rate: int = 16000) -> int:
    """Return a conservative Whisper decode cap for the supplied audio length."""
    duration_seconds = max(0.0, sample_count / sample_rate)
    return min(224, max(32, int(duration_seconds * 8) + 16))


def load_cached_first(loader, model_id: str, *, local_files_only: bool = False, **kwargs):
    """Prefer the cache, then replace a missing or corrupt cached artifact."""
    try:
        return loader.from_pretrained(model_id, local_files_only=True, **kwargs)
    except (OSError, SafetensorError, JSONDecodeError, UnicodeDecodeError, TypeError, ValueError):
        if local_files_only:
            raise
        return loader.from_pretrained(
            model_id,
            local_files_only=False,
            force_download=True,
            **kwargs,
        )


class TorchWhisperModel:
    def __init__(self, model_id: str, device: str, *, revision: str, local_files_only: bool = False):
        self.processor = load_cached_first(
            WhisperProcessor,
            model_id,
            local_files_only=local_files_only,
            revision=revision,
        )
        dtype = torch.float16 if device == "cuda" else torch.float32
        self.model = load_cached_first(
            WhisperForConditionalGeneration,
            model_id,
            local_files_only=local_files_only,
            revision=revision,
            dtype=dtype,
        ).to(device).eval()
        self.model.generation_config.max_length = None
        self.device = device
        self.dtype = dtype

    def transcribe(self, audio, *, language="vi", beam_size=1, initial_prompt="", **_options):
        features = self.processor(audio, sampling_rate=16000, return_tensors="pt").input_features
        features = features.to(device=self.device, dtype=self.dtype)
        # Bound decoding to the amount of speech supplied.  Normal utterances
        # stop at EOS, while this cap prevents noise/hallucinations from running
        # all the way to the old fixed 224-token limit.  Eight tokens/second is
        # deliberately generous for both Vietnamese and English.
        max_new_tokens = max_decode_tokens(len(audio))
        options = {"language": language, "task": "transcribe", "num_beams": beam_size,
                   "max_length": None, "max_new_tokens": max_new_tokens,
                   "return_timestamps": False}
        if initial_prompt:
            options["prompt_ids"] = self.processor.get_prompt_ids(initial_prompt, return_tensors="pt").to(self.device)
        with torch.inference_mode():
            token_ids = self.model.generate(features, **options)
        text = self.processor.batch_decode(token_ids, skip_special_tokens=True,
                                           clean_up_tokenization_spaces=False)[0].strip()
        return [SimpleNamespace(text=text, no_speech_prob=0.0)], SimpleNamespace(language=language)
