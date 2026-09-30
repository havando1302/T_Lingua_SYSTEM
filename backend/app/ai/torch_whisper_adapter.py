"""GPU Whisper adapter with the small interface used by whisper_service."""

from types import SimpleNamespace

import torch
from transformers import WhisperForConditionalGeneration, WhisperProcessor


class TorchWhisperModel:
    def __init__(self, model_id: str, device: str, *, local_files_only: bool = False):
        def load_cached_first(loader, **kwargs):
            try:
                return loader.from_pretrained(model_id, local_files_only=True, **kwargs)
            except OSError:
                if local_files_only:
                    raise
                return loader.from_pretrained(model_id, local_files_only=False, **kwargs)

        self.processor = load_cached_first(WhisperProcessor)
        dtype = torch.float16 if device == "cuda" else torch.float32
        self.model = load_cached_first(WhisperForConditionalGeneration, dtype=dtype).to(device).eval()
        self.model.generation_config.max_length = None
        self.device = device
        self.dtype = dtype

    def transcribe(self, audio, *, language="vi", beam_size=1, initial_prompt="", **_options):
        features = self.processor(audio, sampling_rate=16000, return_tensors="pt").input_features
        features = features.to(device=self.device, dtype=self.dtype)
        options = {"language": language, "task": "transcribe", "num_beams": beam_size,
                   "max_new_tokens": 224, "return_timestamps": False}
        if initial_prompt:
            options["prompt_ids"] = self.processor.get_prompt_ids(initial_prompt, return_tensors="pt").to(self.device)
        with torch.inference_mode():
            token_ids = self.model.generate(features, **options)
        text = self.processor.batch_decode(token_ids, skip_special_tokens=True,
                                           clean_up_tokenization_spaces=False)[0].strip()
        return [SimpleNamespace(text=text, no_speech_prob=0.0)], SimpleNamespace(language=language)
