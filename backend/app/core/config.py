import os
import torch

HOST = "0.0.0.0"

PORT = 8000

DEVICE = (
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)

SAMPLE_RATE = 16000

CHANNELS = 1

BYTES_PER_SAMPLE = 2

CHUNK_MS = 60

MIN_AUDIO_SECONDS = 0.1

MAX_AUDIO_SECONDS = 30

# Partial STT window (seconds) to reduce repeated decoding cost.
PARTIAL_AUDIO_SECONDS = 2.0

# WebRTC VAD settings for real-time streaming.
VAD_FRAME_MS = 30
VAD_AGGRESSIVENESS = 2
VAD_SPEECH_PAD_MS = 120
VAD_SILENCE_MS = 700

# Minimum interval between partial decodes.
PARTIAL_DECODE_INTERVAL_MS = 800

MIN_BUFFER_BYTES = int(
    SAMPLE_RATE *
    BYTES_PER_SAMPLE *
    MIN_AUDIO_SECONDS
)

MAX_BUFFER_BYTES = int(
    SAMPLE_RATE *
    BYTES_PER_SAMPLE *
    MAX_AUDIO_SECONDS
)

PARTIAL_BUFFER_BYTES = int(
    SAMPLE_RATE *
    BYTES_PER_SAMPLE *
    PARTIAL_AUDIO_SECONDS
)

WHISPER_MODEL = "medium"  # Options: tiny, base, small, medium, large

WHISPER_COMPUTE_TYPE = (
    "float16"
    if DEVICE == "cuda"
    else "int8"
)

CPU_THREADS = 4

NLLB_MODEL = (
    "facebook/nllb-200-distilled-1.3B"
)

SOURCE_LANG = "vie_Latn"

TARGET_LANG = "eng_Latn"

TTS_MODEL_ENG = "facebook/mms-tts-eng"
TTS_MODEL_VIE = "facebook/mms-tts-vie"


QUEUE_SIZE = 20

# Concurrency limits for AI model inference.
STT_CONCURRENCY = 1
TRANSLATION_CONCURRENCY = 1
TTS_CONCURRENCY = 1

# Worker pool sizes for shared queues.
STT_WORKER_POOL_SIZE = 2
TRANSLATION_WORKER_POOL_SIZE = 2
TTS_WORKER_POOL_SIZE = 1

# Audio cleanup TTL for synthesized files.
TTS_AUDIO_TTL_SECONDS = 300

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "outputs"
)

TEMP_DIR = os.path.join(
    BASE_DIR,
    "temp"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

os.makedirs(
    TEMP_DIR,
    exist_ok=True
)