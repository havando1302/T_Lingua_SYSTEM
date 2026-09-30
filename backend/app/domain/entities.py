"""
Domain Entities and Value Objects (Phase 7 Clean Architecture)
Chứa các quy tắc nghiệp vụ thuần túy, không phụ thuộc vào framework, database hay thư viện AI bên thứ ba.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any


class TurnStatus(str, Enum):
    CREATED = "created"
    PROCESSING_STT = "processing_stt"
    PROCESSING_TRANSLATION = "processing_translation"
    PROCESSING_TTS = "processing_tts"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass(frozen=True)
class LanguagePair:
    source_lang: str
    target_lang: str

    @classmethod
    def create(cls, source: str, target: str) -> "LanguagePair":
        canonical_map = {
            "vi": "vi", "vie": "vi", "vie_latn": "vi",
            "en": "en", "eng": "en", "eng_latn": "en"
        }
        s = canonical_map.get(source.strip().lower(), source.strip().lower())
        t = canonical_map.get(target.strip().lower(), target.strip().lower())
        if not s or not t:
            raise ValueError(f"Invalid language pair: source='{source}', target='{target}'")
        return cls(source_lang=s, target_lang=t)

    @property
    def nllb_source(self) -> str:
        return "vie_Latn" if self.source_lang == "vi" else "eng_Latn"

    @property
    def nllb_target(self) -> str:
        return "eng_Latn" if self.target_lang == "en" else "vie_Latn"


@dataclass
class DomainTurn:
    turn_id: str
    session_id: str
    speaker: str
    lang_pair: LanguagePair
    turn_index: int = 0
    status: TurnStatus = TurnStatus.CREATED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_text: Optional[str] = None
    translated_text: Optional[str] = None
    error_message: Optional[str] = None

    def mark_status(self, new_status: TurnStatus) -> None:
        if self.status == TurnStatus.CANCELLED:
            # Lượt đã hủy không được chuyển trạng thái khác
            return
        self.status = new_status

    def cancel(self) -> None:
        self.status = TurnStatus.CANCELLED

    def is_active(self) -> bool:
        return self.status not in (TurnStatus.COMPLETED, TurnStatus.CANCELLED, TurnStatus.FAILED)
