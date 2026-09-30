"""Authenticated realtime transport with bounded ingress and revocation checks."""
import asyncio
import json
import logging
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from asyncio import QueueFull
from typing import Any
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from websockets.exceptions import ConnectionClosedError

from app.core.access_policy import connection_slots, enforce_origin, enforce_rate, get_policy_settings, owner_namespace, rate_limiter
from app.core.policy_settings import PolicySettings
from app.core.security import Principal, authenticate_token
from app.core.queues import GLOBAL_STT_QUEUE
from app.db.database import SessionLocal
from app.core.telemetry import GLOBAL_TELEMETRY
from app.workers.runtime import complete_if_idle

router = APIRouter()
logger = logging.getLogger(__name__)
_pending_handshakes = threading.BoundedSemaphore(8)
_LANGUAGE_MAP = {"vi": "vi", "en": "en", "vie_Latn": "vi", "eng_Latn": "en"}


async def _queue_utterance(websocket, session, audio: bytes, turn) -> bool:
    """Queue complete utterances, not every microphone stream chunk."""
    if len(audio) < 3200:
        return False
    if getattr(session, "pending_utterances", 0) >= 4:
        await session.send_message({"type": "status", "status": "busy", "turn_id": turn.turn_id if turn else None})
        return False
    metric_id = str(uuid.uuid4())
    GLOBAL_TELEMETRY.start_turn(metric_id, session.client_id, len(audio) / 32000,
                                turn.source_lang if turn else session.source_lang,
                                turn.target_lang if turn else session.target_lang)
    GLOBAL_TELEMETRY.record_stage(metric_id, "queue_in")
    try:
        GLOBAL_STT_QUEUE.put_nowait({"websocket": websocket, "session": session, "audio": audio,
                                   "is_final": True, "turn": turn, "message_id": metric_id,
                                   "metric_id": metric_id, "work_reserved": True})
        session.pending_utterances = getattr(session, "pending_utterances", 0) + 1
        if turn:
            if not hasattr(session, "pending_by_turn"):
                session.pending_by_turn = {}
            session.pending_by_turn[turn.turn_id] = session.pending_by_turn.get(turn.turn_id, 0) + 1
        return True
    except QueueFull:
        GLOBAL_TELEMETRY.discard_turn(metric_id)
        await session.send_message({"type": "status", "status": "busy", "turn_id": turn.turn_id if turn else None})
        return False


def _resolve_source_lang(code: str) -> str:
    if code not in _LANGUAGE_MAP:
        raise ValueError("Unsupported source language")
    return _LANGUAGE_MAP[code]


def _resolve_target_lang(code: str) -> str:
    if code not in _LANGUAGE_MAP:
        raise ValueError("Unsupported target language")
    return {"vi": "vie_Latn", "en": "eng_Latn"}[_LANGUAGE_MAP[code]]


def _authenticate(token: str | None) -> Principal:
    with SessionLocal() as db:
        principal = authenticate_token(token, db)
        if "translate" not in principal.scopes or "audio" not in principal.scopes:
            raise HTTPException(403, "Realtime requires translate and audio scopes")
        return principal


async def _safe_send_json(websocket, payload):
    try:
        await websocket.send_json(payload)
        return True
    except (WebSocketDisconnect, ConnectionClosedError, RuntimeError):
        return False


async def _close(websocket, code, message):
    try:
        await _safe_send_json(websocket, {"type": "error", "message": message})
        await websocket.close(code=code, reason=message)
    except (WebSocketDisconnect, ConnectionClosedError, RuntimeError):
        pass


async def _heartbeat_loop(websocket, token, session):
    while session.is_running:
        await asyncio.sleep(5)
        try:
            await asyncio.to_thread(_authenticate, token)
        except HTTPException as error:
            session.is_running = False
            await _close(websocket, 4401 if error.status_code == 401 else 4403, "Session ended")
            return
        except Exception:
            session.is_running = False
            await _close(websocket, 1011, "Authentication unavailable")
            return
        if not await _safe_send_json(websocket, {"type": "status", "status": "heartbeat"}):
            session.is_running = False
            return


async def _receive_while_processing(websocket, session, idle_timeout):
    """Apply the idle limit to a free session, not an utterance in the pipeline."""
    while session.is_running:
        try:
            return await asyncio.wait_for(websocket.receive(), idle_timeout)
        except asyncio.TimeoutError:
            # Outbound heartbeats do not count as inbound frames. A finished
            # utterance can take longer than the idle limit on CPU hardware.
            if session.pending_utterances <= 0:
                raise
    raise WebSocketDisconnect()


@dataclass
class _ConnectionState:
    pending_handshake: bool = True
    slot_acquired: bool = False
    principal: Principal | None = None
    session: Any = None
    heartbeat: asyncio.Task | None = None


async def _admit_websocket(websocket: WebSocket, policy: PolicySettings) -> bool:
    try:
        enforce_origin(websocket)
        if policy.APP_ENV != "local" and websocket.url.scheme != "wss":
            raise HTTPException(403, "WSS is required")
        enforce_rate(websocket, bucket="ws-handshake", limit=120 if policy.APP_ENV == "local" else 15)
    except HTTPException:
        # Reject an untrusted Origin before upgrading the connection.
        await websocket.close(code=4403)
        return False
    return True


async def _read_initial_config(
    websocket: WebSocket, policy: PolicySettings,
) -> tuple[dict[str, Any], str | None, Principal]:
    raw = await asyncio.wait_for(websocket.receive_text(), policy.WS_CONFIG_TIMEOUT_SECONDS)
    if len(raw.encode("utf-8")) > policy.WS_MAX_MESSAGE_BYTES:
        raise ValueError("Configuration is too large")
    payload = json.loads(raw)
    if not isinstance(payload, dict) or payload.get("type") != "config":
        raise ValueError("Configuration is required")
    # Browser WebSocket APIs cannot set Authorization; token is sent once in this frame.
    token = payload.pop("access_token", None)
    principal = await asyncio.to_thread(_authenticate, token)
    owner_namespace(principal, payload.get("client_id"))
    pcm_keys = ("sample_rate", "channels", "sample_width")
    if tuple(payload.get(key) for key in pcm_keys) != (16000, 1, 2) or any(
        isinstance(payload.get(key), bool) for key in pcm_keys
    ):
        raise ValueError("Expected PCM mono 16 kHz 16-bit")
    return payload, token, principal


async def _create_session(
    websocket: WebSocket, payload: dict[str, Any], principal: Principal, state: _ConnectionState,
) -> None:
    from app.models.session_model import RealtimeSession

    session = RealtimeSession(
        websocket=websocket,
        session_id=str(uuid.uuid4()),
        client_id=principal.owner_id,
    )
    state.session = session
    session.source_lang = _resolve_source_lang(payload.get("source_lang", "vi"))
    session.target_lang = _resolve_target_lang(payload.get("target_lang", "eng_Latn"))
    session.speaker = payload.get("speaker", "me")
    session.protocol_version = payload.get("protocol_version", 2)
    if hasattr(session, "start_sender"):
        session.start_sender()
    if hasattr(session, "start_new_turn"):
        session.start_new_turn()
    await websocket.send_json({
        "type": "status",
        "status": "authenticated",
        "owner_id": principal.owner_id,
        "expires_at": principal.expires_at.isoformat(),
        "protocol_version": session.protocol_version,
    })
    logger.info(
        "[WS] Client connected: owner_id=%s (protocol v%s, %s -> %s)",
        principal.owner_id,
        session.protocol_version,
        session.source_lang,
        session.target_lang,
    )


async def _send_turn_event(websocket: WebSocket, session: Any, payload: dict) -> None:
    if hasattr(session, "send_message"):
        await session.send_message(payload)
    else:
        await _safe_send_json(websocket, payload)


def _update_config(session: Any, principal: Principal, msg: dict[str, Any]) -> None:
    audio_fields = ("sample_rate", "channels", "sample_width")
    if any(key in msg and msg[key] != getattr(session, key) for key in audio_fields):
        raise ValueError("Audio format cannot be changed mid-session")
    if "client_id" in msg and msg["client_id"] != principal.owner_id:
        raise ValueError("Identity cannot be changed mid-session")
    source = _resolve_source_lang(msg["source_lang"]) if "source_lang" in msg else None
    target = _resolve_target_lang(msg["target_lang"]) if "target_lang" in msg else None
    session.update_pending_config(source_lang=source, target_lang=target, speaker=msg.get("speaker"))


async def _start_turn(websocket: WebSocket, session: Any, msg: dict) -> None:
    source = _resolve_source_lang(msg["source_lang"]) if "source_lang" in msg else None
    target = _resolve_target_lang(msg["target_lang"]) if "target_lang" in msg else None
    if hasattr(session, "start_new_turn"):
        turn = session.start_new_turn(
            turn_id=msg.get("turn_id"), speaker=msg.get("speaker"),
            source_lang=source, target_lang=target,
        )
        payload = {
            "type": "turn_started", "turn_id": turn.turn_id, "turn_index": turn.turn_index,
            "speaker": turn.speaker, "source_lang": turn.source_lang,
            "target_lang": turn.target_lang,
        }
    else:
        payload = {"type": "turn_started", "turn_id": msg.get("turn_id")}
    logger.info(
        "[TURN START] turn_id=%s, speaker=%s, translation: %s -> %s",
        payload.get("turn_id"), msg.get("speaker", getattr(session, "speaker", "me")),
        source or session.source_lang, target or session.target_lang,
    )
    session._frame_count = 0
    session._total_bytes = 0
    await _send_turn_event(websocket, session, payload)


async def _end_turn(websocket: WebSocket, session: Any, msg: dict) -> None:
    turn = session.end_active_turn(msg.get("turn_id")) if hasattr(session, "end_active_turn") else None
    logger.info(
        "[TURN END] turn_id=%s (%d audio chunks received)",
        msg.get("turn_id"), getattr(session, "_frame_count", 0),
    )
    current = getattr(session, "current_turn", None)
    vad = getattr(session, "vad_stream", None)
    if turn and current and current.turn_id == turn.turn_id and vad and hasattr(vad, "flush"):
        pending_audio = vad.flush()
        if pending_audio:
            await _queue_utterance(websocket, session, pending_audio, turn)
    await _send_turn_event(websocket, session, {
        "type": "turn_ended", "turn_id": msg.get("turn_id") or (turn.turn_id if turn else None),
    })
    await complete_if_idle(session, turn)


async def _cancel_turn(websocket: WebSocket, session: Any, msg: dict) -> None:
    logger.info("[TURN CANCEL] turn_id=%s", msg.get("turn_id"))
    if hasattr(session, "cancel_active_turn"):
        session.cancel_active_turn(msg.get("turn_id"))
    await _send_turn_event(websocket, session, {
        "type": "turn_cancelled", "turn_id": msg.get("turn_id"),
    })


async def _handle_control_message(
    websocket: WebSocket, policy: PolicySettings, principal: Principal, session: Any, text: str,
) -> None:
    if len(text.encode("utf-8")) > policy.WS_MAX_MESSAGE_BYTES:
        raise ValueError("Message too large")
    rate_limiter.check(f"ws:ctrl:{principal.owner_id}", 120 if policy.APP_ENV == "local" else 60)
    msg = json.loads(text)
    if not isinstance(msg, dict):
        raise ValueError("Unsupported message")
    kind = msg.get("type")
    if kind == "config":
        _update_config(session, principal, msg)
    elif kind == "start_turn":
        await _start_turn(websocket, session, msg)
    elif kind == "end_turn":
        await _end_turn(websocket, session, msg)
    elif kind == "cancel_turn":
        await _cancel_turn(websocket, session, msg)
    else:
        raise ValueError(f"Unsupported message type: {kind}")


async def _handle_audio_chunk(
    websocket: WebSocket, policy: PolicySettings, principal: Principal, session: Any, chunk: bytes | None,
) -> None:
    if not chunk or len(chunk) > policy.WS_MAX_MESSAGE_BYTES or len(chunk) % 2:
        raise ValueError("Invalid audio frame")
    rate_limiter.check(
        f"ws:bytes:{principal.owner_id}", policy.WS_BYTES_PER_SECOND,
        window=1, cost=len(chunk),
    )
    rate_limiter.check(f"ws:frames:{principal.owner_id}", 200, window=1)
    session._frame_count = getattr(session, "_frame_count", 0) + 1
    session._total_bytes = getattr(session, "_total_bytes", 0) + len(chunk)
    if session._frame_count % 50 == 0:
        logger.info(
            "[AUDIO] Received %d chunks (%.1fs PCM, %d KB) - client=%s",
            session._frame_count,
            session._total_bytes / (session.sample_rate * session.channels * session.sample_width),
            session._total_bytes // 1024,
            principal.owner_id,
        )
    # Process VAD in wire order so end_turn flushes after every received frame.
    vad = getattr(session, "vad_stream", None)
    if vad is not None:
        turn = getattr(session, "current_turn", None)
        if turn is not None and turn.status == "recording":
            utterances, _, _ = vad.process(chunk)
            for utterance in utterances:
                await _queue_utterance(websocket, session, utterance, turn)
        return
    try:
        GLOBAL_STT_QUEUE.put_nowait({
            "websocket": websocket, "session": session, "audio": chunk,
            "is_final": False, "turn": getattr(session, "current_turn", None),
        })
    except QueueFull:
        await _send_turn_event(websocket, session, {"type": "status", "status": "busy"})
    await asyncio.sleep(0)


async def _run_messages(websocket: WebSocket, policy: PolicySettings, principal: Principal, session: Any) -> None:
    while session.is_running:
        message = await _receive_while_processing(websocket, session, policy.WS_IDLE_TIMEOUT_SECONDS)
        if message.get("type") == "websocket.disconnect":
            break
        if datetime.now(timezone.utc) >= principal.expires_at:
            raise HTTPException(401, "Session expired")
        received_text = message.get("text")
        if received_text is not None:
            await _handle_control_message(websocket, policy, principal, session, received_text)
        else:
            await _handle_audio_chunk(websocket, policy, principal, session, message.get("bytes"))


async def _serve_websocket(websocket: WebSocket, policy: PolicySettings, state: _ConnectionState) -> None:
    await websocket.accept()
    payload, token, principal = await _read_initial_config(websocket, policy)
    state.principal = principal
    state.slot_acquired = connection_slots.acquire(principal.owner_id)
    if not state.slot_acquired:
        await _close(websocket, 4429, "Connection limit reached")
        return
    _pending_handshakes.release()
    state.pending_handshake = False
    await _create_session(websocket, payload, principal, state)
    state.heartbeat = asyncio.create_task(_heartbeat_loop(websocket, token, state.session))
    await _run_messages(websocket, policy, principal, state.session)


async def _handle_websocket_error(websocket: WebSocket, error: Exception) -> None:
    if isinstance(error, HTTPException):
        code = 4401 if error.status_code == 401 else 4429 if error.status_code == 429 else 4403
        logger.warning("[WS] Closing due to HTTP exception: %s (code=%d)", error.detail, code)
        await _close(websocket, code, "Session expired" if code == 4401 else "Access denied")
    elif isinstance(error, asyncio.TimeoutError):
        logger.warning("[WS] Connection timed out (4408)")
        await _close(websocket, 4408, "Connection timed out")
    elif isinstance(error, (ValueError, TypeError, KeyError)):
        logger.warning("[WS] Invalid configuration or audio: %s", error)
        await _close(websocket, 4400, "Invalid configuration or audio")
    elif isinstance(error, (WebSocketDisconnect, ConnectionClosedError, RuntimeError)):
        return
    else:
        logger.error("[WS] Unexpected realtime error: %s", error, exc_info=error)
        await _close(websocket, 1011, "Realtime service unavailable")


async def _cleanup_connection(state: _ConnectionState) -> None:
    if state.pending_handshake:
        _pending_handshakes.release()
    if state.session is not None:
        state.session.is_running = False
        task = getattr(state.session, "sender_task", None)
        if task:
            task.cancel()
            # Await cancellation so the task cannot leak a CancelledError into
            # Starlette's TestClient (or remain pending during real shutdown).
            await asyncio.gather(task, return_exceptions=True)
    if state.heartbeat is not None:
        state.heartbeat.cancel()
        await asyncio.gather(state.heartbeat, return_exceptions=True)
    if state.slot_acquired and state.principal is not None:
        connection_slots.release(state.principal.owner_id)
        logger.info("[WS] Client disconnected: owner_id=%s", state.principal.owner_id)


@router.websocket("/ws/realtime")
async def realtime_translation(websocket: WebSocket) -> None:
    policy = get_policy_settings()
    if not await _admit_websocket(websocket, policy):
        return
    if not _pending_handshakes.acquire(blocking=False):
        await websocket.close(code=4429)
        return
    state = _ConnectionState()
    try:
        await _serve_websocket(websocket, policy, state)
    except Exception as error:
        await _handle_websocket_error(websocket, error)
    finally:
        await _cleanup_connection(state)
