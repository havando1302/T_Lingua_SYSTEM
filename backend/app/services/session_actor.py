"""Session Actor with bounded Mailbox and Serial Sender ensuring in-order execution."""
import asyncio
import logging
from typing import Any
import uuid

from starlette.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosedError

from app.models.turn_model import TurnMetadata, TurnStatus
from app.services.vad_service import WebRtcVadStream
from app.core.config import (
    BYTES_PER_SAMPLE,
    CHANNELS,
    MIN_BUFFER_BYTES,
    SAMPLE_RATE,
)
from app.core.queues import GLOBAL_STT_QUEUE

logger = logging.getLogger(__name__)


class SessionActor:
    """Manages an isolated sequential pipeline per realtime WebSocket session.

    Responsibilities:
    - Serial Mailbox: processes audio chunks and control frames sequentially.
    - Serial Sender: guarantees in-order delivery of WebSocket responses.
    - Turn Lifecycle: maintains immutable TurnMetadata, tracks active and cancelled turns.
    - Late Result Filtering: drops results from cancelled or expired turns.
    - Bounded VAD Stream: segments speech without unbounded buffer growth.
    """

    def __init__(
        self,
        websocket,
        session_id: str,
        owner_id: str,
        source_lang: str = "vi",
        target_lang: str = "eng_Latn",
        speaker: str = "me",
        protocol_version: int = 2,
        sample_rate: int = SAMPLE_RATE,
        channels: int = CHANNELS,
        sample_width: int = BYTES_PER_SAMPLE,
    ):
        self.websocket = websocket
        self.session_id = session_id
        self.owner_id = owner_id
        self.protocol_version = protocol_version
        self.sample_rate = sample_rate
        self.channels = channels
        self.sample_width = sample_width

        # Pending configuration for the NEXT turn (does not mutate active turns)
        self.pending_source_lang = source_lang
        self.pending_target_lang = target_lang
        self.pending_speaker = speaker
        self.config_version = 1

        self.turn_counter = 0
        self.current_turn: TurnMetadata | None = None
        self.active_turns: dict[str, TurnMetadata] = {}
        self.cancelled_turns: set[str] = set()

        self.vad_stream = WebRtcVadStream(
            sample_rate=sample_rate,
            channels=channels,
            sample_width=sample_width,
            max_speech_ms=15000,
        )

        self.is_running = True
        self._mailbox: asyncio.Queue[tuple[str, Any]] = asyncio.Queue(maxsize=200)
        self._send_queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=200)

        self._mailbox_task: asyncio.Task | None = None
        self._sender_task: asyncio.Task | None = None

    @property
    def client_id(self) -> str:
        return self.owner_id

    def start(self):
        loop = asyncio.get_running_loop()
        self._mailbox_task = loop.create_task(self._mailbox_loop())
        self._sender_task = loop.create_task(self._sender_loop())

    async def close(self):
        self.is_running = False
        if self.current_turn and self.current_turn.turn_id not in self.cancelled_turns:
            self.cancelled_turns.add(self.current_turn.turn_id)
        if self._mailbox_task:
            self._mailbox_task.cancel()
        if self._sender_task:
            self._sender_task.cancel()
        self.vad_stream.reset()

    # ── Ingress API (called by WebSocket route handler) ──

    async def post_audio(self, chunk: bytes) -> bool:
        if not self.is_running:
            return False
        try:
            self._mailbox.put_nowait(("audio", chunk))
            return True
        except asyncio.QueueFull:
            await self.send_message({"type": "status", "status": "busy", "message": "Buffer full"})
            return False

    async def post_start_turn(
        self,
        turn_id: str | None = None,
        speaker: str | None = None,
        source_lang: str | None = None,
        target_lang: str | None = None,
    ):
        payload = {
            "turn_id": turn_id or str(uuid.uuid4()),
            "speaker": speaker or self.pending_speaker,
            "source_lang": source_lang or self.pending_source_lang,
            "target_lang": target_lang or self.pending_target_lang,
        }
        await self._mailbox.put(("start_turn", payload))

    async def post_end_turn(self, turn_id: str | None = None):
        await self._mailbox.put(("end_turn", turn_id))

    async def post_cancel_turn(self, turn_id: str | None = None):
        await self._mailbox.put(("cancel_turn", turn_id))

    def update_config(self, source_lang: str, target_lang: str, speaker: str | None = None):
        self.pending_source_lang = source_lang
        self.pending_target_lang = target_lang
        if speaker is not None:
            self.pending_speaker = speaker
        self.config_version += 1

    # ── Mailbox Worker ──

    async def _mailbox_loop(self):
        try:
            while self.is_running:
                event_type, payload = await self._mailbox.get()
                try:
                    if event_type == "audio":
                        await self._handle_audio_chunk(payload)
                    elif event_type == "start_turn":
                        self._handle_start_turn(payload)
                    elif event_type == "end_turn":
                        await self._handle_end_turn(payload)
                    elif event_type == "cancel_turn":
                        self._handle_cancel_turn(payload)
                except Exception as exc:
                    logger.exception("Mailbox error processing %s: %s", event_type, exc)
                finally:
                    self._mailbox.task_done()
        except asyncio.CancelledError:
            pass

    def _handle_start_turn(self, payload: dict):
        self.turn_counter += 1
        turn = TurnMetadata.create(
            session_id=self.session_id,
            turn_index=self.turn_counter,
            turn_id=payload.get("turn_id"),
            speaker=payload.get("speaker", self.pending_speaker),
            source_lang=payload.get("source_lang", self.pending_source_lang),
            target_lang=payload.get("target_lang", self.pending_target_lang),
            config_version=self.config_version,
        )
        self.current_turn = turn
        self.active_turns[turn.turn_id] = turn
        self.vad_stream.reset()

    async def _handle_end_turn(self, turn_id: str | None):
        target_turn = self.current_turn
        if turn_id and target_turn and target_turn.turn_id != turn_id:
            target_turn = self.active_turns.get(turn_id)

        if not target_turn or target_turn.turn_id in self.cancelled_turns:
            return

        # Flush any remaining speech in VAD
        pending_audio = self.vad_stream.flush()
        if pending_audio and len(pending_audio) >= MIN_BUFFER_BYTES:
            await self._dispatch_turn_inference(target_turn, pending_audio, is_final=True)
        else:
            # Signal completion if no remaining audio
            await self.send_message({
                "type": "turn_complete",
                "turn_id": target_turn.turn_id,
                "status": "completed",
            })

    def _handle_cancel_turn(self, turn_id: str | None):
        tid = turn_id or (self.current_turn.turn_id if self.current_turn else None)
        if tid:
            self.cancelled_turns.add(tid)
            if tid in self.active_turns:
                self.active_turns[tid] = self.active_turns[tid].with_status(TurnStatus.CANCELLED)
        self.vad_stream.reset()

    async def _handle_audio_chunk(self, chunk: bytes):
        if not self.current_turn:
            # Auto-start turn 1 for legacy protocol v1 or unannounced streaming
            self._handle_start_turn({
                "turn_id": str(uuid.uuid4()),
                "speaker": self.pending_speaker,
                "source_lang": self.pending_source_lang,
                "target_lang": self.pending_target_lang,
            })

        turn = self.current_turn
        if not turn or turn.turn_id in self.cancelled_turns:
            return

        finals, _current, in_speech = self.vad_stream.process(chunk)
        for utterance in finals:
            if len(utterance) >= MIN_BUFFER_BYTES:
                await self._dispatch_turn_inference(turn, utterance, is_final=True)

    async def _dispatch_turn_inference(self, turn: TurnMetadata, audio_bytes: bytes, is_final: bool = True):
        if turn.turn_id in self.cancelled_turns:
            return

        task = {
            "actor": self,
            "session": self,  # for compatibility with legacy workers
            "websocket": self.websocket,
            "turn": turn,
            "audio": audio_bytes,
            "is_final": is_final,
            "client_id": self.owner_id,
        }

        try:
            GLOBAL_STT_QUEUE.put_nowait(task)
        except asyncio.QueueFull:
            await self.send_message({"type": "status", "status": "busy", "message": "STT Queue is full"})

    # ── Egress & Late Result Filtering ──

    def is_turn_active(self, turn_id: str) -> bool:
        return self.is_running and (turn_id not in self.cancelled_turns)

    async def send_message(self, payload: dict) -> bool:
        """Enqueues message into serial sender queue."""
        if not self.is_running:
            return False

        # Drop messages for cancelled turns
        turn_id = payload.get("turn_id")
        if turn_id and turn_id in self.cancelled_turns:
            return False

        try:
            self._send_queue.put_nowait(payload)
            return True
        except asyncio.QueueFull:
            return False

    async def _sender_loop(self):
        try:
            while self.is_running:
                payload = await self._send_queue.get()
                try:
                    await self.websocket.send_json(payload)
                except (WebSocketDisconnect, ConnectionClosedError, RuntimeError):
                    self.is_running = False
                    break
                except Exception as err:
                    logger.warning("Sender failed: %s", err)
                finally:
                    self._send_queue.task_done()
        except asyncio.CancelledError:
            pass
