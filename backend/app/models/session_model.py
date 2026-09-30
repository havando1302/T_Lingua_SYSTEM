import asyncio
from dataclasses import dataclass, field
import logging
from typing import Any
import uuid

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosedError

from app.core.config import BYTES_PER_SAMPLE, CHANNELS, SAMPLE_RATE
from app.models.turn_model import TurnMetadata, TurnStatus
from app.services.vad_service import WebRtcVadStream

logger = logging.getLogger(__name__)


@dataclass
class RealtimeSession:
    websocket: WebSocket
    session_id: str
    pipeline: object = None
    audio_buffer: bytes = b""
    partial_text: str = ""
    client_id: str = "default"
    vad_stream: WebRtcVadStream | None = None
    silence_count: int = 0
    last_partial_decode_ts: float = 0.0
    sample_rate: int = SAMPLE_RATE
    channels: int = CHANNELS
    sample_width: int = BYTES_PER_SAMPLE
    is_running: bool = True
    tasks: list = field(default_factory=list)

    # Language and speaker state
    source_lang: str = "vi"
    target_lang: str = "eng_Latn"
    speaker: str = "me"
    protocol_version: int = 2

    # Turn management
    turn_counter: int = 0
    current_turn: TurnMetadata | None = None
    active_turns: dict[str, TurnMetadata] = field(default_factory=dict)
    cancelled_turns: set[str] = field(default_factory=set)

    # Pending configurations for the NEXT turn
    pending_source_lang: str = "vi"
    pending_target_lang: str = "eng_Latn"
    pending_speaker: str = "me"
    config_version: int = 1

    turn_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    send_queue: asyncio.Queue = field(default_factory=lambda: asyncio.Queue(maxsize=150))
    sender_task: asyncio.Task | None = None
    pending_utterances: int = 0
    pending_by_turn: dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        self.pending_source_lang = self.source_lang
        self.pending_target_lang = self.target_lang
        self.pending_speaker = self.speaker
        if self.vad_stream is None:
            self.vad_stream = WebRtcVadStream(
                sample_rate=self.sample_rate,
                channels=self.channels,
                sample_width=self.sample_width,
                max_speech_ms=15000,
            )

    def start_sender(self):
        if self.sender_task is None or self.sender_task.done():
            loop = asyncio.get_running_loop()
            self.sender_task = loop.create_task(self._sender_loop())

    async def _sender_loop(self):
        try:
            while self.is_running:
                payload = await self.send_queue.get()
                try:
                    if payload.get("turn_id") in self.cancelled_turns and payload.get("type") != "turn_cancelled":
                        continue
                    await self.websocket.send_json(payload)
                except (WebSocketDisconnect, ConnectionClosedError, RuntimeError):
                    self.is_running = False
                    break
                except Exception as exc:
                    logger.warning("Session sender error: %s", exc)
                finally:
                    self.send_queue.task_done()
        except asyncio.CancelledError:
            pass

    async def send_message(self, payload: dict) -> bool:
        if not self.is_running:
            return False
        msg_type = payload.get("type")
        turn_id = payload.get("turn_id")
        if turn_id and turn_id in self.cancelled_turns and msg_type != "turn_cancelled":
            return False
        try:
            self.send_queue.put_nowait(payload)
            return True
        except asyncio.QueueFull:
            return False

    def start_new_turn(
        self,
        turn_id: str | None = None,
        speaker: str | None = None,
        source_lang: str | None = None,
        target_lang: str | None = None,
    ) -> TurnMetadata:
        if turn_id is not None and (not isinstance(turn_id, str) or not turn_id.strip() or len(turn_id) > 128):
            raise ValueError("Invalid turn identifier")
        if speaker is not None and speaker not in {"me", "partner", "user", "agent"}:
            raise ValueError("Unsupported speaker")
        if turn_id in self.active_turns:
            raise ValueError("Turn identifier has already been used")
        if self.turn_counter == 0:
            # Also supports callers that set the handshake fields after construction.
            self.pending_source_lang, self.pending_target_lang, self.pending_speaker = self.source_lang, self.target_lang, self.speaker
        if self.current_turn and self.current_turn.status == TurnStatus.RECORDING.value:
            self.cancel_active_turn(self.current_turn.turn_id)
        while len(self.active_turns) >= 128:
            oldest = next(iter(self.active_turns))
            self.active_turns.pop(oldest)
            self.cancelled_turns.discard(oldest)
        self.turn_counter += 1
        turn = TurnMetadata.create(
            session_id=self.session_id,
            turn_index=self.turn_counter,
            turn_id=turn_id or str(uuid.uuid4()),
            speaker=speaker or self.pending_speaker,
            source_lang=source_lang or self.pending_source_lang,
            target_lang=target_lang or self.pending_target_lang,
            config_version=self.config_version,
        )
        self.current_turn = turn
        self.active_turns[turn.turn_id] = turn
        if self.vad_stream:
            self.vad_stream.reset()
        return turn

    def end_active_turn(self, turn_id: str | None = None) -> TurnMetadata | None:
        target = self.current_turn
        if turn_id and target and target.turn_id != turn_id:
            target = self.active_turns.get(turn_id)
        if target and target.status == TurnStatus.RECORDING.value and target.turn_id not in self.cancelled_turns:
            updated = target.with_status(TurnStatus.PROCESSING)
            self.active_turns[target.turn_id] = updated
            if self.current_turn and self.current_turn.turn_id == target.turn_id:
                self.current_turn = updated
            return updated
        return None

    def cancel_active_turn(self, turn_id: str | None = None) -> None:
        target_id = turn_id or (self.current_turn.turn_id if self.current_turn else None)
        if target_id in self.active_turns:
            self.cancelled_turns.add(target_id)
            if target_id in self.active_turns:
                self.active_turns[target_id] = self.active_turns[target_id].with_status(TurnStatus.CANCELLED)
        if self.vad_stream and self.current_turn and self.current_turn.turn_id == target_id:
            self.vad_stream.reset()

    def is_turn_active(self, turn_id: str | None) -> bool:
        if not self.is_running:
            return False
        if turn_id is None:
            return True
        return turn_id in self.active_turns and turn_id not in self.cancelled_turns

    def update_pending_config(
        self,
        source_lang: str | None = None,
        target_lang: str | None = None,
        speaker: str | None = None,
    ):
        if speaker is not None and speaker not in {"me", "partner", "user", "agent"}:
            raise ValueError("Unsupported speaker")
        if source_lang:
            self.pending_source_lang = source_lang
            self.source_lang = source_lang
        if target_lang:
            self.pending_target_lang = target_lang
            self.target_lang = target_lang
        if speaker:
            self.pending_speaker = speaker
            self.speaker = speaker
        self.config_version += 1
