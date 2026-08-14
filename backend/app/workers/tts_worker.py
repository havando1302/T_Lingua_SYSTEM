import asyncio

import torch

from starlette.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosedError

from app.core.config import TTS_AUDIO_TTL_SECONDS, TTS_CONCURRENCY
from app.core.queues import GLOBAL_TTS_QUEUE
from app.services.tts_service import (
    delete_audio_file,
    synthesize_audio
)

_tts_semaphore = asyncio.Semaphore(TTS_CONCURRENCY)


async def _safe_send_json(websocket, payload: dict) -> bool:
    try:
        await websocket.send_json(payload)
        return True
    except (WebSocketDisconnect, ConnectionClosedError, RuntimeError):
        return False


async def _schedule_audio_cleanup(filename: str) -> None:
    # Delay cleanup to allow client to fetch the file.
    await asyncio.sleep(TTS_AUDIO_TTL_SECONDS)
    await asyncio.to_thread(delete_audio_file, filename)

def _maybe_empty_cache() -> None:
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


async def tts_worker(worker_id: int = 0):
    _ = worker_id

    while True:

        item = await GLOBAL_TTS_QUEUE.get()

        session = item.get("session")
        websocket = item.get("websocket")
        text = item.get("text")

        try:
            if not session or not websocket or not text:
                continue
            if not session.is_running:
                continue

            # Limit concurrent TTS to avoid overload.
            ok = await _safe_send_json(websocket, {
                "type": "status",
                "status": "processing_tts"
            })
            if not ok:
                session.is_running = False
                continue

            async with _tts_semaphore:
                filename = await asyncio.to_thread(
                    synthesize_audio,
                    text,
                    session.target_lang
                )

            ok = await _safe_send_json(websocket, {
                "type": "audio",
                "audio_url": f"/audio/{filename}"
            })
            if not ok:
                session.is_running = False
                continue

            asyncio.create_task(_schedule_audio_cleanup(filename))

        except (WebSocketDisconnect, ConnectionClosedError):
            continue

        except Exception as e:

            print("Lỗi TTS:", e)

        finally:
            _maybe_empty_cache()
            GLOBAL_TTS_QUEUE.task_done()