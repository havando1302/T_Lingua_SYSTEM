"""Immutable turn model and protocol specifications for realtime speech translation."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Literal


class TurnStatus(str, Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


SpeakerRole = Literal["me", "partner", "user", "agent"]


@dataclass(frozen=True)
class TurnMetadata:
    """Immutable turn entity containing all context required for downstream inference."""
    turn_id: str
    session_id: str
    turn_index: int
    speaker: str = "me"
    source_lang: str = "vi"
    target_lang: str = "eng_Latn"
    config_version: int = 1
    status: str = TurnStatus.RECORDING.value
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def create(
        cls,
        session_id: str,
        turn_index: int,
        turn_id: str | None = None,
        speaker: str = "me",
        source_lang: str = "vi",
        target_lang: str = "eng_Latn",
        config_version: int = 1,
    ) -> "TurnMetadata":
        return cls(
            turn_id=turn_id or str(uuid.uuid4()),
            session_id=session_id,
            turn_index=turn_index,
            speaker=speaker,
            source_lang=source_lang,
            target_lang=target_lang,
            config_version=config_version,
            status=TurnStatus.RECORDING.value,
        )

    def with_status(self, new_status: TurnStatus | str) -> "TurnMetadata":
        val = new_status.value if isinstance(new_status, TurnStatus) else new_status
        return TurnMetadata(
            turn_id=self.turn_id,
            session_id=self.session_id,
            turn_index=self.turn_index,
            speaker=self.speaker,
            source_lang=self.source_lang,
            target_lang=self.target_lang,
            config_version=self.config_version,
            status=val,
            created_at=self.created_at,
        )

    def to_dict(self) -> dict:
        return {
            "turn_id": self.turn_id,
            "session_id": self.session_id,
            "turn_index": self.turn_index,
            "speaker": self.speaker,
            "source_lang": self.source_lang,
            "target_lang": self.target_lang,
            "config_version": self.config_version,
            "status": self.status,
            "created_at": self.created_at,
        }
