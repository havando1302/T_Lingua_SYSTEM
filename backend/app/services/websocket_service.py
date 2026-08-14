import base64
import logging

from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from app.core import queues


logger = logging.getLogger("WebSocket-Service")


async def websocket_receiver(websocket: WebSocket):

    logger.info("Luồng nhận WebSocket đã bắt đầu")

    try:

        while True:

            data = await websocket.receive_json()

            chunk_id = data.get("chunk_id")

            audio_base64 = data.get("audio")

            is_final = data.get("is_final", False)

            # ==========================================
            # VALIDATE
            # ==========================================

            if chunk_id is None:

                await websocket.send_json({
                    "type": "error",
                    "message": "Thiếu chunk_id"
                })

                continue

            if audio_base64 is None:

                await websocket.send_json({
                    "type": "error",
                    "message": "Thiếu dữ liệu âm thanh"
                })

                continue

            # ==========================================
            # BASE64 -> BYTES
            # ==========================================

            try:

                audio_bytes = base64.b64decode(
                    audio_base64
                )

            except Exception:

                await websocket.send_json({
                    "type": "error",
                    "message": "Dữ liệu base64 âm thanh không hợp lệ"
                })

                continue

            # ==========================================
            # PUSH QUEUE
            # ==========================================

            await queues.STT_QUEUE.put({

                "websocket": websocket,

                "chunk_id": chunk_id,

                "audio": audio_bytes,

                "is_final": is_final
            })

    except WebSocketDisconnect:

        logger.warning("WebSocket đã ngắt kết nối")

    except Exception as e:

        logger.error(f"Lỗi luồng nhận WebSocket: {e}")

        try:

            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })

        except:
            pass