import asyncio

from app.workers.stt_worker import stt_worker
from app.workers.translation_worker import translation_worker
from app.workers.tts_worker import tts_worker


async def start_workers():

    asyncio.create_task(stt_worker())

    asyncio.create_task(translation_worker())

    asyncio.create_task(tts_worker())