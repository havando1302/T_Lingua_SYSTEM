import asyncio
import logging
import uuid
from asyncio import QueueFull


from starlette.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosedError

logger = logging.getLogger(__name__)

from app.utils.audio_utils import (
    pcm_bytes_to_mono_16k_bytes,
    pcm_to_numpy,
    preprocess_audio_numpy
)
from app.services.whisper_service import transcribe_audio
from app.services.whisper_service import should_process_audio
from app.services.vad_service import WebRtcVadStream
from app.services.semantic_service import correct_text_semantics
from app.services import translation_memory as tm
from app.core.queues import GLOBAL_STT_QUEUE, GLOBAL_TRANSLATE_QUEUE
from app.core.config import MAX_BUFFER_BYTES, MIN_BUFFER_BYTES, STT_CONCURRENCY, settings
from app.services.deepfilter_service import denoise_numpy
from app.core.gpu_manager import GPU_MANAGER
from app.core.telemetry import GLOBAL_TELEMETRY
from app.workers.runtime import finish_work

_stt_semaphore = asyncio.Semaphore(STT_CONCURRENCY)


async def _safe_send_json(websocket, payload: dict) -> bool:
    try:
        await websocket.send_json(payload)
        return True
    except (WebSocketDisconnect, ConnectionClosedError, RuntimeError):
        return False


async def stt_worker(worker_id: int = 0):
    _ = worker_id

    while True:
        item = await GLOBAL_STT_QUEUE.get()
        forwarded = False
        metric_id = item.get("metric_id")
        session = None
        try:
            session = item.get("session")
            websocket = item.get("websocket")
            audio = item.get("audio", b"")

            if not session or not websocket or not audio:
                continue
            if not session.is_running:
                continue

            try:
                audio = await asyncio.to_thread(
                    pcm_bytes_to_mono_16k_bytes,
                    audio,
                    session.sample_rate,
                    session.channels,
                    session.sample_width
                )
            except ValueError:
                err_msg = {"type": "error", "message": "Siêu dữ liệu âm thanh không hợp lệ"}
                if hasattr(session, "send_message"):
                    await session.send_message(err_msg)
                else:
                    await _safe_send_json(websocket, err_msg)
                session.is_running = False
                continue

            turn = item.get("turn") or getattr(session, "current_turn", None)
            if turn and hasattr(session, "is_turn_active") and not session.is_turn_active(turn.turn_id):
                continue

            if session.vad_stream is None:
                session.vad_stream = WebRtcVadStream()

            if not hasattr(session, "vad_lock"):
                session.vad_lock = asyncio.Lock()

            async with session.vad_lock:
                if item.get("is_final"):
                    final_utterances = [audio]
                    in_speech = False
                else:
                    final_utterances, _current_audio, in_speech = session.vad_stream.process(audio)

            if not in_speech and not final_utterances and audio.count(0) == len(audio):
                continue

            for utterance in final_utterances:
                if turn and hasattr(session, "is_turn_active") and not session.is_turn_active(turn.turn_id):
                    break

                if len(utterance) < MIN_BUFFER_BYTES:
                    continue

                if len(utterance) > MAX_BUFFER_BYTES:
                    utterance = utterance[-MAX_BUFFER_BYTES:]

                metric_id = item.get("metric_id") or str(uuid.uuid4())
                GLOBAL_TELEMETRY.start_turn(metric_id, session.client_id, len(utterance) / 32000, turn.source_lang if turn else session.source_lang, turn.target_lang if turn else session.target_lang)
                GLOBAL_TELEMETRY.record_stage(metric_id, "queue_out")
                GLOBAL_TELEMETRY.record_stage(metric_id, "stt_start")
                audio_np = pcm_to_numpy(utterance)
                audio_np = await asyncio.to_thread(preprocess_audio_numpy, audio_np)

                try:
                    audio_np = await asyncio.to_thread(
                        denoise_numpy, audio_np,
                        atten_lim_db=settings.DENOISE_ATTENUATION_DB,
                        min_duration_seconds=getattr(settings, "DENOISE_MIN_AUDIO_SECONDS", 3.0))
                except Exception as e:
                    print("DeepFilter failed:", type(e).__name__)

                if not await asyncio.to_thread(should_process_audio, audio_np):
                    GLOBAL_TELEMETRY.discard_turn(metric_id)
                    if hasattr(session, "send_message"):
                        await session.send_message({"type": "error", "code": "no_speech_detected", "message": "No intelligible speech was detected. Please record again.", "turn_id": turn.turn_id if turn else None})
                    continue

                status_msg = {
                    "type": "status",
                    "status": "processing_stt",
                    "stage": "final",
                    "turn_id": turn.turn_id if turn else None,
                }
                if hasattr(session, "send_message"):
                    ok = await session.send_message(status_msg)
                else:
                    ok = await _safe_send_json(websocket, status_msg)
                if not ok:
                    session.is_running = False
                    break

                source_lang = turn.source_lang if turn else getattr(session, "source_lang", "vi")
                whisper_lang = {"vi": "vi", "en": "en", "vie_Latn": "vi", "eng_Latn": "en"}.get(source_lang, "vi")
                target_lang = turn.target_lang if turn else getattr(session, "target_lang", "eng_Latn")
                speaker = turn.speaker if turn else getattr(session, "speaker", "me")


                logger.info(
                    "🎙️ [VAD] Phát hiện câu nói (%.2fs) -> Đang nhận diện Whisper (%s)...",
                    len(utterance) / 32000,
                    whisper_lang,
                )
                async with _stt_semaphore:
                    cid = getattr(session, "client_id", getattr(session, "owner_id", "default"))
                    glossary_prompt = tm.get_glossary_prompt(cid)
                    final_result = await asyncio.to_thread(
                        transcribe_audio,
                        audio_np,
                        beam_size=settings.WHISPER_BEAM_SIZE,
                        temperature=0.0,
                        condition_on_previous_text=False,
                        use_vad=False,
                        context_prompt=glossary_prompt,
                        language=whisper_lang,
                    )

                GLOBAL_TELEMETRY.record_stage(metric_id, "stt_done")

                raw_text = final_result.get("text")
                final_text: str = str(raw_text or "").strip()
                if final_text:
                    final_text = await asyncio.to_thread(correct_text_semantics, final_text, "")
                    logger.info("stt_done chars=%d language=%s latency=%.3fs", len(final_text), whisper_lang, final_result.get("latency", 0.0))
                    if turn and hasattr(session, "is_turn_active") and not session.is_turn_active(turn.turn_id):
                        break

                    msg_id = item.get("message_id") or metric_id
                    stt_payload = {
                        "type": "stt",
                        "stage": "final",
                        "message_id": msg_id,
                        "turn_id": turn.turn_id if turn else None,
                        "turn_index": turn.turn_index if turn else None,
                        "speaker": speaker,
                        "source_lang": source_lang,
                        "target_lang": target_lang,
                        "data": {
                            "text": final_text,
                            "language": final_result.get("language"),
                            "latency": final_result.get("latency")
                        }
                    }
                    if hasattr(session, "send_message"):
                        ok = await session.send_message(stt_payload)
                    else:
                        ok = await _safe_send_json(websocket, stt_payload)
                    if not ok:
                        session.is_running = False
                        break

                    translate_item = {
                        "websocket": websocket,
                        "session": session,
                        "turn": turn,
                        "text": final_text,
                        # Preserve the exact utterance Whisper received so the
                        # matching QA row can carry real source audio.
                        "audio_pcm": utterance,
                        "message_id": msg_id,
                        "metric_id": metric_id,
                        "work_reserved": item.get("work_reserved", False),
                    }
                    try:
                        GLOBAL_TRANSLATE_QUEUE.put_nowait(translate_item)
                    except QueueFull:
                        await GLOBAL_TRANSLATE_QUEUE.put(translate_item)
                    forwarded = True
                else:
                    GLOBAL_TELEMETRY.discard_turn(metric_id)
                    if hasattr(session, "send_message"):
                        await session.send_message({"type": "error", "code": "no_speech_detected", "message": "No intelligible speech was detected. Please record again.", "turn_id": turn.turn_id if turn else None})

                GPU_MANAGER.adaptive_cleanup()

            if not session.is_running:
                continue

        except (WebSocketDisconnect, ConnectionClosedError):
            continue
        except Exception as error:
            GLOBAL_TELEMETRY.discard_turn(metric_id, error=type(error).__name__)
            logger.error("stt_failed error_type=%s", type(error).__name__)
            if session and session.is_running and hasattr(session, "send_message"):
                await session.send_message({"type": "error", "code": "stt_unavailable", "message": "Speech recognition is temporarily unavailable", "turn_id": item.get("turn").turn_id if item.get("turn") else None})
        finally:
            if not forwarded:
                GLOBAL_TELEMETRY.discard_turn(metric_id)
                await finish_work(item)
            GLOBAL_STT_QUEUE.task_done()
