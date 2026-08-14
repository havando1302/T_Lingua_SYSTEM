import asyncio
from asyncio import QueueFull

import torch

from starlette.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosedError

from app.core.config import TRANSLATION_CONCURRENCY
from app.core.queues import GLOBAL_TRANSLATE_QUEUE, GLOBAL_TTS_QUEUE
from app.services.translation_service import (
    translate_text
)

_translation_semaphore = asyncio.Semaphore(TRANSLATION_CONCURRENCY)


async def _safe_send_json(websocket, payload: dict) -> bool:
    try:
        await websocket.send_json(payload)
        return True
    except (WebSocketDisconnect, ConnectionClosedError, RuntimeError):
        return False

def _maybe_empty_cache() -> None:
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


async def translation_worker(worker_id: int = 0):
    _ = worker_id

    while True:

        item = await GLOBAL_TRANSLATE_QUEUE.get()

        session = item.get("session")
        websocket = item.get("websocket")
        text = item.get("text")
        msg_id = item.get("message_id")

        try:
            if not session or not websocket or not text:
                continue
            if not session.is_running:
                continue

            # Limit concurrent translation to protect CPU/GPU resources.
            ok = await _safe_send_json(websocket, {
                "type": "status",
                "status": "processing_translation"
            })
            if not ok:
                session.is_running = False
                continue

            async with _translation_semaphore:
                # [NEW] Chuyển đổi mã ngôn ngữ ngắn (vi/en) sang mã NLLB (vie_Latn/eng_Latn)
                source_lang_map = {"vi": "vie_Latn", "en": "eng_Latn"}
                nllb_source = source_lang_map.get(session.source_lang, "vie_Latn")

                result = await asyncio.to_thread(
                    translate_text,
                    text,
                    "",
                    source_lang=nllb_source,           # [NEW]
                    target_lang=session.target_lang     # [NEW]
                )

            ok = await _safe_send_json(websocket, {
                "type": "translation",
                "message_id": msg_id,
                "data": result
            })
            if not ok:
                session.is_running = False
                continue

            print(
                f"[NLLB KẾT QUẢ] Bản dịch: \"{result.get('translated_text', '')}\""
            )

            # Backpressure: chi xu ly bat buoc cho final.
            try:
                GLOBAL_TTS_QUEUE.put_nowait({
                    "websocket": websocket,
                    "session": session,
                    "text": result["translated_text"]
                })
            except QueueFull:
                await GLOBAL_TTS_QUEUE.put({
                    "websocket": websocket,
                    "session": session,
                    "text": result["translated_text"]
                })

        except (WebSocketDisconnect, ConnectionClosedError):
            continue

        except Exception as e:

            print("Lỗi dịch thuật:", e)

        finally:
            _maybe_empty_cache()
            GLOBAL_TRANSLATE_QUEUE.task_done()