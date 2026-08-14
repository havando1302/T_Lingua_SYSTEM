from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="employee") # superadmin, admin, employee
    created_at = Column(DateTime, default=datetime.utcnow)

class TranslationLog(Base):
    __tablename__ = "translation_logs"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, index=True)
    source_text = Column(String, nullable=False)
    translated_text = Column(String, nullable=False)
    latency = Column(Float)
    model_source = Column(String) # Ví dụ: nllb_model, translation_memory
    is_flagged = Column(Boolean, default=False) # Bị cờ báo (nghi ngờ sai)
    created_at = Column(DateTime, default=datetime.utcnow)

class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    key = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(String, nullable=False)
    description = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
