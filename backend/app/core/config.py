"""Application configuration. Auth and ingress policy also work without AI imports."""
import os
from pydantic import Field
from typing import Literal
from app.core.auth_settings import AuthSettings
from app.core.policy_settings import PolicySettings


class Settings(AuthSettings, PolicySettings):
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    DEVICE: str = "auto"
    WHISPER_MODEL: str = "small"
    WHISPER_BACKEND: Literal["auto", "ctranslate2", "transformers"] = "auto"
    WHISPER_TORCH_MODEL: str = "openai/whisper-large-v3-turbo"
    WHISPER_TORCH_LOCAL_ONLY: bool = False
    WHISPER_DEVICE: Literal["auto", "cpu", "cuda"] = "auto"
    WHISPER_CPU_THREADS: int = Field(default=4, ge=1, le=32)
    WHISPER_COMPUTE_TYPE: str = "auto"
    WHISPER_BEAM_SIZE: int = Field(default=3, ge=1, le=10)
    NLLB_MODEL: str = "facebook/nllb-200-distilled-1.3B"
    TRANSLATION_BEAM_SIZE: int = Field(default=1, ge=1, le=10)
    TTS_MODEL_ENG: str = "facebook/mms-tts-eng"
    TTS_MODEL_VIE: str = "facebook/mms-tts-vie"
    HF_TOKEN: str = ""
    ENABLE_DEEPFILTER: bool = True
    DENOISE_ATTENUATION_DB: float = Field(default=12.0, ge=0.0, le=60.0)
    DENOISE_MIN_AUDIO_SECONDS: float = Field(default=3.0, ge=0.0, le=10.0)
    PREWARM_MODELS: bool = True
    STT_WORKER_POOL_SIZE: int = Field(default=2, ge=1, le=8)
    TRANSLATION_WORKER_POOL_SIZE: int = Field(default=2, ge=1, le=8)
    TTS_WORKER_POOL_SIZE: int = Field(default=1, ge=1, le=8)


settings = Settings()

# Compatibility constants preserve existing AI/worker behavior.
import torch

HOST = settings.API_HOST
PORT = settings.API_PORT

# Device resolution
if settings.DEVICE == "auto":
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
else:
    DEVICE = settings.DEVICE

# Audio constants (không cần config, giữ hardcode)
SAMPLE_RATE = 16000
CHANNELS = 1
BYTES_PER_SAMPLE = 2
CHUNK_MS = 60
MIN_AUDIO_SECONDS = 0.1
MAX_AUDIO_SECONDS = 30
PARTIAL_AUDIO_SECONDS = 2.0

# WebRTC VAD settings
VAD_FRAME_MS = 30
VAD_AGGRESSIVENESS = 2
VAD_SPEECH_PAD_MS = 120
VAD_SILENCE_MS = 700

# Partial decode
PARTIAL_DECODE_INTERVAL_MS = 800

# Derived buffer sizes
MIN_BUFFER_BYTES = int(SAMPLE_RATE * BYTES_PER_SAMPLE * MIN_AUDIO_SECONDS)
MAX_BUFFER_BYTES = int(SAMPLE_RATE * BYTES_PER_SAMPLE * MAX_AUDIO_SECONDS)
PARTIAL_BUFFER_BYTES = int(SAMPLE_RATE * BYTES_PER_SAMPLE * PARTIAL_AUDIO_SECONDS)

# AI model names (backward compat)
WHISPER_MODEL = settings.WHISPER_MODEL
WHISPER_COMPUTE_TYPE = (
    settings.WHISPER_COMPUTE_TYPE
    if settings.WHISPER_COMPUTE_TYPE != "auto"
    else ("float16" if DEVICE == "cuda" else "int8")
)
CPU_THREADS = 4
NLLB_MODEL = settings.NLLB_MODEL
SOURCE_LANG = "vie_Latn"
TARGET_LANG = "eng_Latn"
TTS_MODEL_ENG = settings.TTS_MODEL_ENG
TTS_MODEL_VIE = settings.TTS_MODEL_VIE

# Queue / Worker
QUEUE_SIZE = 500
STT_CONCURRENCY = 1
TRANSLATION_CONCURRENCY = 1
TTS_CONCURRENCY = 1
STT_WORKER_POOL_SIZE = settings.STT_WORKER_POOL_SIZE
TRANSLATION_WORKER_POOL_SIZE = settings.TRANSLATION_WORKER_POOL_SIZE
TTS_WORKER_POOL_SIZE = settings.TTS_WORKER_POOL_SIZE

# Audio TTL
TTS_AUDIO_TTL_SECONDS = settings.TTS_AUDIO_TTL_SECONDS

# Directories
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(__file__))
)
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
TEMP_DIR = os.path.join(BASE_DIR, "temp")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
