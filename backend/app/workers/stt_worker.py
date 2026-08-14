import asyncio
import traceback
import uuid
from asyncio import QueueFull

import torch

from starlette.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosedError

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
from app.core.config import MAX_BUFFER_BYTES, MIN_BUFFER_BYTES, STT_CONCURRENCY
from app.services.deepfilter_service import denoise_numpy

_stt_semaphore = asyncio.Semaphore(STT_CONCURRENCY)


async def _safe_send_json(websocket, payload: dict) -> bool:
    try:
        await websocket.send_json(payload)
        return True
    except (WebSocketDisconnect, ConnectionClosedError, RuntimeError):
        return False

def _maybe_empty_cache() -> None:
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


async def stt_worker(worker_id: int = 0):
    _ = worker_id

    while True:
        item = await GLOBAL_STT_QUEUE.get()
        # KỸ THUẬT DRAIN QUEUE
        items = [item]
        deferred: list[dict] = []
        try:
            session = item.get("session")
            websocket = item.get("websocket")

            while not GLOBAL_STT_QUEUE.empty():
                try:
                    queued_item = GLOBAL_STT_QUEUE.get_nowait()
                    if queued_item.get("session") is session:
                        items.append(queued_item)
                    else:
                        deferred.append(queued_item)
                    GLOBAL_STT_QUEUE.task_done()
                except asyncio.QueueEmpty:
                    break

            # Tra lai cac goi cua session khac ve hang doi.
            for deferred_item in deferred:
                try:
                    GLOBAL_STT_QUEUE.put_nowait(deferred_item)
                except QueueFull:
                    await GLOBAL_STT_QUEUE.put(deferred_item)

            audio = b"".join([i.get("audio", b"") for i in items])
            if not session or not websocket or not audio:
                continue
            if not session.is_running:
                continue

            # Chuyen ve PCM 16k mono de VAD va STT xu ly on dinh.
            try:
                audio = await asyncio.to_thread(
                    pcm_bytes_to_mono_16k_bytes,
                    audio,
                    session.sample_rate,
                    session.channels,
                    session.sample_width
                )
            except ValueError:
                ok = await _safe_send_json(websocket, {
                    "type": "error",
                    "message": "Siêu dữ liệu âm thanh không hợp lệ"
                })
                if not ok:
                    session.is_running = False
                continue

            # Khoi tao VAD stream theo session de giu trang thai.
            if session.vad_stream is None:
                session.vad_stream = WebRtcVadStream()

            final_utterances, _current_audio, in_speech = session.vad_stream.process(audio)

            # FIX BUG: chi bo qua silence sau khi VAD da xu ly.
            if not in_speech and not final_utterances and audio.count(0) == len(audio):
                continue

            # Final decode: chi xu ly khi nguoi dung ngat cau.
            for utterance in final_utterances:
                if len(utterance) < MIN_BUFFER_BYTES:
                    continue

                if len(utterance) > MAX_BUFFER_BYTES:
                    utterance = utterance[-MAX_BUFFER_BYTES:]

                # Bien doi bytes -> numpy -> tien xu ly DSP tren server.
                audio_np = pcm_to_numpy(utterance)

                audio_np = await asyncio.to_thread(
                    preprocess_audio_numpy,
                    audio_np
                )

                # Loai bo doan nhieu bang DeepFilterNet
                try:
                    audio_np = await asyncio.to_thread(
                        denoise_numpy,
                        audio_np
                    )
                except Exception as e:
                    print(f"[DeepFilterNet] {e}")

                # Loai bo doan nhieu bang Silero VAD (neu bat).
                if not await asyncio.to_thread(should_process_audio, audio_np):
                    continue
                
                # Chống quá tải hệ thống bằng cách giới hạn số luồng STT chạy đồng thời
                ok = await _safe_send_json(websocket, {
                    "type": "status",
                    "status": "processing_stt",
                    "stage": "final"
                })
                if not ok:
                    session.is_running = False
                    break

                async with _stt_semaphore:
                    glossary_prompt = tm.get_glossary_prompt(session.client_id)
                    final_result = await asyncio.to_thread(
                        transcribe_audio,
                        audio_np,
                        beam_size=5,
                        temperature=0.0,
                        condition_on_previous_text=False,
                        use_vad=True,
                        context_prompt=glossary_prompt,
                        language=session.source_lang  # Dùng ngôn ngữ từ session
                    )

                final_text = final_result["text"]

                # Hiệu đính ngữ nghĩa dựa trên ngữ cảnh gần nhất (Bỏ qua context sliding, chỉ dùng kết quả STT độc lập)
                final_text = await asyncio.to_thread(
                    correct_text_semantics,
                    final_text,
                    ""
                )

                if final_text:
                    print(f"[STT KẾT QUẢ] Văn bản nhận diện được: \"{final_text}\"")

                    msg_id = str(uuid.uuid4())

                    ok = await _safe_send_json(websocket, {
                        "type": "stt",
                        "stage": "final",
                        "message_id": msg_id,
                        "data": {
                            "text": final_text,
                            "language": final_result.get("language"),
                            "latency": final_result.get("latency")
                        }
                    })
                    if not ok:
                        session.is_running = False
                        break

                    # Backpressure: neu queue qua tai thi bat buoc xu ly cho final.
                    try:
                        GLOBAL_TRANSLATE_QUEUE.put_nowait({
                            "websocket": websocket,
                            "session": session,
                            "text": final_text,
                            "message_id": msg_id
                        })
                    except QueueFull:
                        await GLOBAL_TRANSLATE_QUEUE.put({
                            "websocket": websocket,
                            "session": session,
                            "text": final_text,
                            "message_id": msg_id
                        })

                # Giai phong VRAM sau khi xu ly final.
                _maybe_empty_cache()

            if not session.is_running:
                continue

        except (WebSocketDisconnect, ConnectionClosedError):
            continue
        except Exception:
            print("Lỗi luồng xử lý STT:")
            traceback.print_exc()
        finally:
            GLOBAL_STT_QUEUE.task_done()