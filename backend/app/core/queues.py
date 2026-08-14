import asyncio

from app.core.config import (
    QUEUE_SIZE
)

class PipelineQueues:

    def __init__(self):

        self.stt_queue = asyncio.Queue(
            maxsize=QUEUE_SIZE
        )

        self.translate_queue = asyncio.Queue(
            maxsize=QUEUE_SIZE
        )

        self.tts_queue = asyncio.Queue(
            maxsize=QUEUE_SIZE
        )



GLOBAL_STT_QUEUE = asyncio.Queue(
    maxsize=QUEUE_SIZE
)

GLOBAL_TRANSLATE_QUEUE = asyncio.Queue(
    maxsize=QUEUE_SIZE
)

GLOBAL_TTS_QUEUE = asyncio.Queue(
    maxsize=QUEUE_SIZE
)