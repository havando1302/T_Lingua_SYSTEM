"""
Inference Layer Interfaces (Phase 7 Clean Architecture - Adapter Pattern)
Định nghĩa các giao diện trừu tượng cho tầng AI Model.
Cho phép thay thế các model (Whisper, NLLB, VITS) hoặc dùng Mock trong kiểm thử mà không cần GPU.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import numpy as np


class ISTTAdapter(ABC):
    @abstractmethod
    def transcribe(
        self,
        audio_data: np.ndarray,
        language: str = "vi",
        context_prompt: Optional[str] = None,
        beam_size: int = 1,
    ) -> Dict[str, Any]:
        """Trả về dict chứa {'text': str, 'language': str, 'latency': float}"""
        pass


class ITranslationAdapter(ABC):
    @abstractmethod
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        client_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Trả về dict chứa {'translated_text': str, 'latency': float, 'source': str}"""
        pass


class ITTSAdapter(ABC):
    @abstractmethod
    def synthesize(
        self,
        text: str,
        language: str,
    ) -> bytes:
        """Trả về raw audio bytes (PCM WAV)"""
        pass


class IDenoiseAdapter(ABC):
    @abstractmethod
    def denoise(self, audio_data: np.ndarray) -> np.ndarray:
        """Khử nhiễu mảng âm thanh numpy"""
        pass
