from dataclasses import dataclass
from dataclasses import field

from fastapi import WebSocket

from app.core.config import BYTES_PER_SAMPLE, CHANNELS, SAMPLE_RATE

@dataclass
class RealtimeSession:

    websocket: WebSocket

    session_id: str

    pipeline: object = None

    audio_buffer: bytes = b""

    partial_text: str = ""

    # Định danh client để phân tách đa người dùng.
    client_id: str = "default"

    # Luu VAD stream theo session de xu ly streaming o worker pool.
    vad_stream: object = None

    silence_count: int = 0

    last_partial_decode_ts: float = 0.0

    # Metadata audio tu client (co the khac 16k mono).
    sample_rate: int = SAMPLE_RATE

    channels: int = CHANNELS

    sample_width: int = BYTES_PER_SAMPLE

    is_running: bool = True

    tasks: list = field(default_factory=list)

    # [NEW] Ngôn ngữ nguồn để Whisper nhận diện đúng (vi / en)
    source_lang: str = "vi"

    # [NEW] Ngôn ngữ đích cho NLLB dịch (eng_Latn / vie_Latn)
    target_lang: str = "eng_Latn"