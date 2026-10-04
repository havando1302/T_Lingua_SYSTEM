import asyncio
import logging
from asyncio import QueueFull

import torch

from starlette.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosedError

logger = logging.getLogger(__name__)

from app.core.config import TRANSLATION_CONCURRENCY
from app.core.queues import GLOBAL_TRANSLATE_QUEUE, GLOBAL_TTS_QUEUE
from app.services.translation_service import translate_text
from app.core.gpu_manager import GPU_MANAGER
from app.core.telemetry import GLOBAL_TELEMETRY
from app.workers.runtime import finish_work

_translation_semaphore = asyncio.Semaphore(TRANSLATION_CONCURRENCY)
_NLLB_MAP = {
    "vi": "vie_Latn",
    "en": "eng_Latn",
    "vie_Latn": "vie_Latn",
    "eng_Latn": "eng_Latn",
}


def _stage_voice_audio_sync(client_id: str, audio_pcm: bytes | None) -> str | None:
    """Stage audio with a short TTL; only an explicit report promotes it to QA."""
    if not audio_pcm:
        return None
    try:
        from app.db.database import SessionLocal
        from app.services.audio_storage import stage_source_pcm
        with SessionLocal() as db:
            return stage_source_pcm(db, audio_pcm, client_id).file_name
    except Exception as error:
        logger.warning("Failed to stage realtime voice audio: %s", type(error).__name__, exc_info=error)
        return None


def _cache_enabled_sync():
    try:
        from app.db.database import SessionLocal
        from app.db.models import SystemSetting
        with SessionLocal() as db:
            setting = db.query(SystemSetting).filter(SystemSetting.key == "enable_cache").first()
            return setting is None or setting.value.strip().lower() == "true"
    except Exception:
        return False


async def _safe_send_json(websocket, payload: dict) -> bool:
    try:
        await websocket.send_json(payload)
        return True
    except (WebSocketDisconnect, ConnectionClosedError, RuntimeError):
        return False


async def translation_worker(worker_id: int = 0):
    _ = worker_id

    while True:
        item = await GLOBAL_TRANSLATE_QUEUE.get()

        session = item.get("session")
        websocket = item.get("websocket")
        turn = item.get("turn")
        text = item.get("text")
        msg_id = item.get("message_id")
        metric_id = item.get("metric_id", msg_id)
        forwarded = False

        try:
            if not session or not websocket or not text:
                continue
            if not session.is_running:
                continue

            if turn and hasattr(session, "is_turn_active") and not session.is_turn_active(turn.turn_id):
                continue

            status_msg = {
                "type": "status",
                "status": "processing_translation",
                "turn_id": turn.turn_id if turn else None,
            }
            if hasattr(session, "send_message"):
                ok = await session.send_message(status_msg)
            else:
                ok = await _safe_send_json(websocket, status_msg)
            if not ok:
                session.is_running = False
                continue

            source_code = turn.source_lang if turn else getattr(session, "source_lang", "vi")
            target_code = turn.target_lang if turn else getattr(session, "target_lang", "eng_Latn")
            speaker = turn.speaker if turn else getattr(session, "speaker", "me")

            nllb_source = _NLLB_MAP.get(source_code, "vie_Latn")
            nllb_target = _NLLB_MAP.get(target_code, "eng_Latn")

            GLOBAL_TELEMETRY.record_stage(metric_id, "translate_start")
            logger.info("translation_start source=%s target=%s chars=%d", source_code, target_code, len(text))
            use_cache = await asyncio.to_thread(_cache_enabled_sync)
            async with _translation_semaphore:
                result = await asyncio.to_thread(translate_text, text, "", source_lang=nllb_source,
                                                 target_lang=nllb_target, client_id=session.client_id, use_cache=use_cache)
            if not result.get("translated_text", "").strip():
                raise RuntimeError("Translation returned no text")

            logger.info(
                "translation_done chars=%d latency=%.3fs source=%s",
                len(result.get("translated_text", "")),
                result.get("latency", 0.0),
                result.get("source", "nllb_realtime"),
            )

            GLOBAL_TELEMETRY.record_stage(metric_id, "translate_done")

            if turn and hasattr(session, "is_turn_active") and not session.is_turn_active(turn.turn_id):
                continue

            qa_audio_token = await asyncio.to_thread(
                _stage_voice_audio_sync, session.client_id, item.get("audio_pcm"),
            )
            if qa_audio_token is not None:
                result = {**result, "qa_audio_token": qa_audio_token}

            trans_payload = {
                "type": "translation",
                "message_id": msg_id,
                "turn_id": turn.turn_id if turn else None,
                "turn_index": turn.turn_index if turn else None,
                "speaker": speaker,
                "source_lang": source_code,
                "target_lang": target_code,
                "data": result,
            }
            if hasattr(session, "send_message"):
                ok = await session.send_message(trans_payload)
            else:
                ok = await _safe_send_json(websocket, trans_payload)
            if not ok:
                session.is_running = False
                continue

            tts_item = {
                "websocket": websocket,
                "session": session,
                "turn": turn,
                "text": result["translated_text"],
                "message_id": msg_id,
                "metric_id": metric_id,
                "work_reserved": item.get("work_reserved", False),
            }
            try:
                GLOBAL_TTS_QUEUE.put_nowait(tts_item)
            except QueueFull:
                await GLOBAL_TTS_QUEUE.put(tts_item)
            forwarded = True

        except (WebSocketDisconnect, ConnectionClosedError):
            continue
        except Exception as e:
            GLOBAL_TELEMETRY.discard_turn(metric_id, error=type(e).__name__)
            logger.error("translation_failed error_type=%s", type(e).__name__)
            if session and session.is_running:
                payload = {"type": "error", "code": "translation_unavailable",
                           "message": "Translation is temporarily unavailable", "turn_id": turn.turn_id if turn else None}
                if hasattr(session, "send_message"):
                    await session.send_message(payload)
                else:
                    await _safe_send_json(websocket, payload)
        finally:
            if not forwarded:
                GLOBAL_TELEMETRY.discard_turn(metric_id)
                await finish_work(item)
            GPU_MANAGER.adaptive_cleanup()
            GLOBAL_TRANSLATE_QUEUE.task_done()
