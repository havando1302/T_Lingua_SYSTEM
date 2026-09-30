"""New audio has an owner and expiry; legacy output is never publicly mounted."""
from datetime import datetime
from sqlalchemy import Column, DateTime, String
from app.db.database import Base


class AudioAsset(Base):
    __tablename__ = "audio_assets"
    file_name = Column(String(40), primary_key=True)
    owner_id = Column(String(36), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
