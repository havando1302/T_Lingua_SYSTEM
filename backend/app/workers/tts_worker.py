import asyncio
import base64
import logging


from starlette.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosedError

logger = logging.getLogger(__name__)

from app.core.config import TTS_CONCURRENCY
from app.core.queues import GLOBAL_TTS_QUEUE
from app.services.tts_service import generate_speech_bytes
from app.utils.text_utils import split_text_for_streaming
from app.core.gpu_manager import GPU_MANAGER
from app.core.telemetry import GLOBAL_TELEMETRY
from app.workers.runtime import finish_work

_tts_semaphore = asyncio.Semaphore(TTS_CONCURRENCY)


async def _safe_send_json(websocket, payload: dict) -> bool:
    try:
        await websocket.send_json(payload)
        return True
    except (WebSocketDisconnect, ConnectionClosedError, RuntimeError):
        return False


async def tts_worker(worker_id: int = 0):
    _ = worker_id

    while True:
        item = await GLOBAL_TTS_QUEUE.get()

        session = item.get("session")
        websocket = item.get("websocket")
        turn = item.get("turn")
        text = item.get("text")
        msg_id = item.get("message_id")
        metric_id = item.get("metric_id", msg_id)
        completed = False

        try:
            if not session or not websocket or not text:
                continue
            if not session.is_running:
                continue

            if turn and hasattr(session, "is_turn_active") and not session.is_turn_active(turn.turn_id):
                continue

            status_msg = {
                "type": "status",
                "status": "processing_tts",
                "turn_id": turn.turn_id if turn else None,
            }
            if hasattr(session, "send_message"):
                ok = await session.send_message(status_msg)
            else:
                ok = await _safe_send_json(websocket, status_msg)
            if not ok:
                session.is_running = False
                continue

            chunks = split_text_for_streaming(text)
            if not chunks:
                chunks = [text]

            target_lang = turn.target_lang if turn else getattr(session, "target_lang", "eng_Latn")
            logger.info("tts_start language=%s chunks=%d chars=%d", target_lang, len(chunks), len(text))
            GLOBAL_TELEMETRY.record_stage(metric_id, "tts_start")

            for idx, chunk_text in enumerate(chunks):
                if not session.is_running:
                    break
                if turn and hasattr(session, "is_turn_active") and not session.is_turn_active(turn.turn_id):
                    break

                async with _tts_semaphore:
                    wav_bytes = await asyncio.to_thread(
                        generate_speech_bytes,
                        chunk_text,
                        target_lang,
                    )

                # Cancellation can arrive while the model runs in its thread.
                # Drop this result without stopping the user's newer turn/session.
                if not session.is_running or (turn and hasattr(session, "is_turn_active") and not session.is_turn_active(turn.turn_id)):
                    break

                if not wav_bytes:
                    raise RuntimeError("Speech synthesis returned no audio")

                logger.info(
                    "🔊 [TTS] Đã tạo đoạn âm thanh #%d/%d (%d KB) cho turn_id=%s",
                    idx + 1,
                    len(chunks),
                    len(wav_bytes) // 1024,
                    turn.turn_id if turn else None,
                )

                if idx == 0:
                    GLOBAL_TELEMETRY.record_stage(metric_id, "tts_chunk_0")

                audio_b64 = base64.b64encode(wav_bytes).decode("ascii")

                chunk_payload = {
                    "type": "audio_chunk",
                    "index": idx,
                    "total": len(chunks),
                    "turn_id": turn.turn_id if turn else None,
                    "message_id": msg_id,
                    "audio_data": audio_b64,
                }
                if hasattr(session, "send_message"):
                    ok = await session.send_message(chunk_payload)
                else:
                    ok = await _safe_send_json(websocket, chunk_payload)
                if not ok:
                    session.is_running = False
                    break

            else:
                # Complete only after every chunk was sent; cancellation never counts as success.
                if session.is_running and (not turn or session.is_turn_active(turn.turn_id)):
                    done = {"type": "audio_done", "turn_id": turn.turn_id if turn else None, "message_id": msg_id}
                    ok = await session.send_message(done) if hasattr(session, "send_message") else await _safe_send_json(websocket, done)
                    if ok:
                        GLOBAL_TELEMETRY.record_stage(metric_id, "tts_done")
                        GLOBAL_TELEMETRY.complete_turn(metric_id)
                        completed = True

        except (WebSocketDisconnect, ConnectionClosedError):
            continue
        except Exception as e:
            GLOBAL_TELEMETRY.discard_turn(metric_id, error=type(e).__name__)
            logger.error("tts_failed error_type=%s", type(e).__name__)
            if session and session.is_running and hasattr(session, "send_message"):
                await session.send_message({"type": "error", "code": "tts_unavailable", "message": "Speech synthesis is temporarily unavailable", "turn_id": turn.turn_id if turn else None})
        finally:
            if not completed:
                GLOBAL_TELEMETRY.discard_turn(metric_id)
            await finish_work(item)
            GPU_MANAGER.adaptive_cleanup()
            GLOBAL_TTS_QUEUE.task_done()
