import uuid
import json
import asyncio

from asyncio import QueueFull

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect
)
from websockets.exceptions import ConnectionClosedError

from app.core.queues import (
    GLOBAL_STT_QUEUE
)

from app.core.config import BYTES_PER_SAMPLE

from app.models.session_model import (
    RealtimeSession
)

_SOURCE_LANGUAGE_MAP = {
    "vie_latn": "vi",
    "eng_latn": "en",
    "vi": "vi",
    "en": "en",
}

def _resolve_source_lang(code: str) -> str:
    if not code:
        return "vi"
    normalized = code.strip().lower()
    return _SOURCE_LANGUAGE_MAP.get(normalized, "vi")

_TARGET_LANGUAGE_MAP = {
    "vi": "vie_Latn",
    "en": "eng_Latn",
    "vie_latn": "vie_Latn",
    "eng_latn": "eng_Latn",
}

def _resolve_target_lang(code: str) -> str:
    if not code:
        return "eng_Latn"
    normalized = code.strip().lower()
    return _TARGET_LANGUAGE_MAP.get(normalized, "eng_Latn")

router = APIRouter()


async def _safe_send_json(websocket: WebSocket, payload: dict) -> bool:
    try:
        await websocket.send_json(payload)
        return True
    except (WebSocketDisconnect, ConnectionClosedError, RuntimeError):
        return False


async def _heartbeat_loop(websocket: WebSocket, interval_seconds: float) -> None:
    while True:
        await asyncio.sleep(interval_seconds)
        ok = await _safe_send_json(websocket, {
            "type": "status",
            "status": "heartbeat"
        })
        if not ok:
            return

@router.websocket("/ws/realtime")
async def realtime_translation(
    websocket: WebSocket
):

    await websocket.accept()

    session_id = str(uuid.uuid4())

    print(f"Máy khách đã kết nối: {session_id}")

    session = RealtimeSession(
        websocket=websocket,
        session_id=session_id
    )

    try:
        # Require a config message before streaming to validate audio metadata.
        init_payload = await websocket.receive_json()
        if init_payload.get("type") != "config":
            await _safe_send_json(websocket, {
                "type": "error",
                "message": "Cần gửi thông điệp cấu hình làm payload đầu tiên"
            })
            await websocket.close()
            return

        try:
            sample_rate = int(init_payload.get("sample_rate"))
            channels = int(init_payload.get("channels"))
            sample_width = int(init_payload.get("sample_width"))
        except (TypeError, ValueError):
            await _safe_send_json(websocket, {
                "type": "error",
                "message": "Siêu dữ liệu âm thanh không hợp lệ"
            })
            await websocket.close()
            return

        if sample_width != BYTES_PER_SAMPLE:
            await _safe_send_json(websocket, {
                "type": "error",
                "message": "Siêu dữ liệu âm thanh không hợp lệ",
                "expected": {
                    "sample_width": BYTES_PER_SAMPLE
                }
            })
            await websocket.close()
            return

        session.sample_rate = int(sample_rate)
        session.channels = int(channels)
        session.sample_width = int(sample_width)

        # [NEW] Lưu client_id và cấu hình ngôn ngữ từ client vào session
        session.client_id = init_payload.get("client_id", "default")
        session.source_lang = _resolve_source_lang(init_payload.get("source_lang", "vi"))
        session.target_lang = _resolve_target_lang(init_payload.get("target_lang", "eng_Latn"))
        print(f"Cấu hình Client: {session.client_id} | Ngôn ngữ: {session.source_lang} -> {session.target_lang}")
    except (WebSocketDisconnect, ConnectionClosedError):
        print(f"Máy khách ngắt kết nối trước khi cấu hình: {session_id}")
        return
    except Exception:
        await _safe_send_json(websocket, {
            "type": "error",
            "message": "Thông điệp cấu hình không hợp lệ hoặc bị thiếu"
        })
        await websocket.close()
        return

    heartbeat_task = asyncio.create_task(
        _heartbeat_loop(websocket, 10.0)
    )

    try:

        while True:

            # [NEW] Dùng receive() thay vì receive_bytes() để xử lý
            # cả audio (binary) lẫn config update (text/JSON) giữa chừng
            try:
                message = await websocket.receive()
            except (WebSocketDisconnect, ConnectionClosedError, RuntimeError):
                break

            if message.get("type") == "websocket.disconnect":
                break

            # [NEW] Xử lý config update khi client đổi ngôn ngữ giữa chừng
            if "text" in message and message["text"] is not None:
                try:
                    config_update = json.loads(message["text"])
                    if config_update.get("type") == "config":
                        new_source = _resolve_source_lang(config_update.get("source_lang", session.source_lang))
                        new_target = _resolve_target_lang(config_update.get("target_lang", session.target_lang))
                        if new_source != session.source_lang or new_target != session.target_lang:
                            session.source_lang = new_source
                            session.target_lang = new_target
                            print(f"Đã cập nhật ngôn ngữ: {session.source_lang} -> {session.target_lang}")
                except (json.JSONDecodeError, AttributeError):
                    pass
                continue

            # Xử lý audio binary frame
            if "bytes" not in message or message["bytes"] is None:
                continue
            audio_bytes = message["bytes"]

            # Validate chunk alignment for 16-bit PCM mono.
            if len(audio_bytes) % (session.sample_width * session.channels) != 0:
                ok = await _safe_send_json(websocket, {
                    "type": "error",
                    "message": "Kích thước khối âm thanh không hợp lệ"
                })
                if not ok:
                    break
                continue

            # Day vao queue dung chung. Neu qua tai thi bo qua goi nhap (partial).
            try:
                GLOBAL_STT_QUEUE.put_nowait({
                    "websocket": websocket,
                    "session": session,
                    "audio": audio_bytes,
                    "is_final": False
                })
            except QueueFull:
                # Drop partial de giam tai RAM/CPU khi qua tai.
                await asyncio.sleep(0)
                continue

            # Yield to keep the event loop responsive.
            await asyncio.sleep(0)

    except (WebSocketDisconnect, ConnectionClosedError):

        print(f"Máy khách đã ngắt kết nối: {session_id}")

    except Exception as e:

        print(f"Lỗi WebSocket: {e}")

    finally:

        # Danh dau session da ket thuc de worker pool bo qua.
        session.is_running = False

        heartbeat_task.cancel()
        await asyncio.gather(
            heartbeat_task,
            return_exceptions=True
        )