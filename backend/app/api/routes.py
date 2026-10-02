"""Translation endpoints authorize the server-issued owner before accessing data."""
import logging
import os
import time
import uuid
import wave
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.access_policy import get_policy_settings, owner_namespace, require_scope, validate_text
from app.core.security import Principal
from app.db.database import get_db
from app.db.models import TranslationLog, SystemSetting
from app.core.inference_errors import NoSpeechDetected
from app.core.telemetry import GLOBAL_TELEMETRY
from app.services import translation_memory as tm
from app.services.audio_storage import SECURE_TEMP_DIR, audio_path, owned_audio, register_audio, secure_directory

router = APIRouter()
logger = logging.getLogger(__name__)
Language = Literal["vi", "en", "vie_Latn", "eng_Latn"]


class TranslateTextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    source_lang: Language
    target_lang: Language


def _resolve_lang(code: str) -> str:
    return {"vi": "vie_Latn", "en": "eng_Latn"}.get(code, code)


def translate_text(*args, **kwargs):
    from app.services.translation_service import translate_text as implementation
    return implementation(*args, **kwargs)


def run_pipeline(*args, **kwargs):
    from app.services.pipeline_service import run_pipeline as implementation
    return implementation(*args, **kwargs)


@router.post("/api/translate-text")
def translate_text_api(payload: TranslateTextRequest, principal: Principal = Depends(require_scope("translate")), db: Session = Depends(get_db)):
    text = validate_text(payload.text, db)
    metric_id = uuid.uuid4().hex
    t0 = time.monotonic()
    GLOBAL_TELEMETRY.start_turn(metric_id, principal.owner_id, source_lang=payload.source_lang, target_lang=payload.target_lang)
    try:
        GLOBAL_TELEMETRY.record_stage(metric_id, "translate_start")
        result = translate_text(text, source_lang=_resolve_lang(payload.source_lang), target_lang=_resolve_lang(payload.target_lang), client_id=principal.owner_id, use_cache=_cache_enabled(db))
        if not str(result.get("translated_text") or "").strip():
            raise RuntimeError("Translation returned no text")
        latency = round(time.monotonic() - t0, 3)
        GLOBAL_TELEMETRY.record_stage(metric_id, "translate_done")
        GLOBAL_TELEMETRY.complete_turn(metric_id)

        try:
            log = TranslationLog(
                client_id=principal.owner_id,
                source_text=text,
                translated_text=result.get("translated_text", ""),
                source_lang=payload.source_lang,
                target_lang=payload.target_lang,
                input_mode="text",
                latency=result.get("latency", latency),
                model_source=result.get("source", "nllb_model"),
                nllb_model_id=os.getenv("NLLB_MODEL", "facebook/nllb-200-distilled-1.3B"),
                is_flagged=False,
                is_reviewed=False,
                created_at=datetime.utcnow(),
            )
            db.add(log)
            db.commit()
        except Exception as e:
            logger.warning("Failed to persist translation log: %s", e)
            db.rollback()

        return {"source_text": text, "translated_text": result.get("translated_text", "")}
    except Exception as error:
        GLOBAL_TELEMETRY.discard_turn(metric_id, error=type(error).__name__)
        logger.error("text_translation_failed error_type=%s", type(error).__name__)
        raise HTTPException(503, "Translation is temporarily unavailable") from None


@router.post("/translate")
async def translate_audio(file: UploadFile = File(...), source_lang: Language = Form("vi"),
                          target_lang: Language = Form("en"),
                          principal: Principal = Depends(require_scope("translate")), db: Session = Depends(get_db)):
    file_name = f"{uuid.uuid4().hex}.wav"
    temp_path = secure_directory(SECURE_TEMP_DIR) / file_name
    output_path = audio_path(file_name)
    registered = False
    try:
        size = 0
        with temp_path.open("xb") as destination:
            while chunk := await file.read(65536):
                size += len(chunk)
                if size > get_policy_settings().MAX_AUDIO_UPLOAD_BYTES:
                    raise HTTPException(413, "Audio upload too large")
                destination.write(chunk)
        try:
            with wave.open(str(temp_path), "rb") as audio:
                if audio.getframerate() != 16000 or audio.getnchannels() != 1 or audio.getsampwidth() != 2 or audio.getcomptype() != "NONE" or not 0 < audio.getnframes() <= 16000 * 30:
                    raise HTTPException(422, "Audio must be PCM WAV, mono, 16 kHz, 16-bit, at most 30 seconds")
                if len(audio.readframes(audio.getnframes())) != audio.getnframes() * 2:
                    raise HTTPException(422, "Truncated audio")
        except (wave.Error, EOFError):
            raise HTTPException(422, "Invalid PCM WAV audio") from None
        # The bounded threadpool keeps health checks and WebSocket ingress responsive.
        result = await run_in_threadpool(run_pipeline, str(temp_path), client_id=principal.owner_id,
                                        output_path=str(output_path), source_lang=_resolve_lang(source_lang),
                                        target_lang=_resolve_lang(target_lang), use_cache=_cache_enabled(db))
        asset = register_audio(db, file_name, principal.owner_id)
        registered = True
        result["audio_url"] = f"/audio/{file_name}"
        result["audio_expires_at"] = asset.expires_at.isoformat() + "Z"

        try:
            log = TranslationLog(
                client_id=principal.owner_id,
                source_text=result.get("original_text", ""),
                translated_text=result.get("translated_text", ""),
                source_lang=source_lang,
                target_lang=target_lang,
                input_mode="voice",
                latency=result.get("metrics", {}).get("total_latency", 0.0),
                model_source="pipeline",
                stt_model_id=os.getenv("WHISPER_TORCH_MODEL", "openai/whisper-large-v3-turbo"),
                nllb_model_id=os.getenv("NLLB_MODEL", "facebook/nllb-200-distilled-1.3B"),
                is_flagged=False,
                is_reviewed=False,
                created_at=datetime.utcnow(),
            )
            db.add(log)
            db.commit()
        except Exception as e:
            logger.warning("Failed to persist audio translation log: %s", e)
            db.rollback()

        return result
    except NoSpeechDetected:
        raise HTTPException(422, "No intelligible speech was detected. Please record again.") from None
    except HTTPException:
        raise
    except Exception as error:
        db.rollback()
        logger.error("audio_translation_failed error_type=%s", type(error).__name__)
        raise HTTPException(503, "Audio translation is temporarily unavailable") from None
    finally:
        await file.close()
        temp_path.unlink(missing_ok=True)
        if not registered:
            output_path.unlink(missing_ok=True)


@router.get("/audio/{file_name}")
def get_audio(file_name: str, principal: Principal = Depends(require_scope("audio")), db: Session = Depends(get_db)):
    return FileResponse(owned_audio(db, file_name, principal.owner_id), media_type="audio/wav", headers={"Cache-Control": "no-store"})


class TMEntry(BaseModel):
    source_text: str = Field(min_length=1, max_length=10000)
    translated_text: str = Field(min_length=1, max_length=10000)
    client_id: str | None = Field(default=None, max_length=64)
    source_lang: str | None = Field(default=None, max_length=16)
    target_lang: str | None = Field(default=None, max_length=16)


class TMDeleteRequest(BaseModel):
    source_text: str = Field(min_length=1, max_length=10000)
    client_id: str | None = Field(default=None, max_length=64)


@router.get("/api/translation-memory")
def get_translation_memory(client_id: str | None = None, principal: Principal = Depends(require_scope("tm:read"))):
    owner = owner_namespace(principal, client_id)
    return {"entries": tm.get_all(owner), "count": tm.count(owner)}


@router.post("/api/translation-memory")
def add_translation_memory(entry: TMEntry, principal: Principal = Depends(require_scope("tm:write")), db: Session = Depends(get_db)):
    owner = owner_namespace(principal, entry.client_id)
    source, target = validate_text(entry.source_text, db), validate_text(entry.translated_text, db)
    if principal.role == "guest":
        try:
            tm.register_guest(owner, principal.expires_at)
        except ValueError:
            raise HTTPException(409, "Guest dictionary is unavailable") from None
    try:
        if not tm.add_many(
            [{"source_text": source, "translated_text": target}], owner,
            max_entries=500, volatile=principal.role == "guest",
            source_lang=entry.source_lang, target_lang=entry.target_lang,
        ):
            raise HTTPException(422, "Invalid entry")
    except ValueError as error:
        if "capacity" in str(error).lower():
            raise HTTPException(409, "Private dictionary capacity reached") from None
        raise HTTPException(422, "Invalid dictionary entry or language pair") from None
    except OSError:
        raise HTTPException(503, "Dictionary storage is unavailable") from None
    return {"message": "Added successfully", "source_text": source, "translated_text": target, "total_entries": tm.count(owner)}


@router.post("/api/translation-memory/delete")
def delete_translation_memory(entry: TMDeleteRequest, principal: Principal = Depends(require_scope("tm:write"))):
    owner = owner_namespace(principal, entry.client_id)
    try:
        if not tm.delete(entry.source_text, owner):
            raise HTTPException(404, "Entry not found")
    except OSError:
        raise HTTPException(503, "Dictionary storage is unavailable") from None
    return {"message": "Deleted successfully", "source_text": entry.source_text, "total_entries": tm.count(owner)}


class FlagTranslationRequest(BaseModel):
    source_text: str = Field(min_length=1, max_length=10000)
    translated_text: str = Field(min_length=1, max_length=10000)
    client_id: str | None = Field(default=None, max_length=64)
    source_lang: Language = "vi"
    target_lang: Language = "en"
    input_mode: Literal["voice", "text", "unknown"] = "unknown"


@router.post("/api/flag-translation")
def flag_translation_api(payload: FlagTranslationRequest, principal: Principal = Depends(require_scope("flag")), db: Session = Depends(get_db)):
    from app.core.config import settings
    owner = owner_namespace(principal, payload.client_id)
    log = TranslationLog(client_id=owner, source_text=validate_text(payload.source_text, db), translated_text=validate_text(payload.translated_text, db),
                         source_lang=tm.normalize_lang_code(payload.source_lang), target_lang=tm.normalize_lang_code(payload.target_lang),
                         input_mode=payload.input_mode,
                         stt_model_id=settings.WHISPER_TORCH_MODEL if payload.input_mode == "voice" else None,
                         nllb_model_id=settings.NLLB_MODEL,
                         is_flagged=True, latency=0.0, model_source="user_flagged")
    db.add(log)
    db.commit()
    return {"ok": True}


def _cache_enabled(db: Session) -> bool:
    setting = db.query(SystemSetting).filter(SystemSetting.key == "enable_cache").first()
    return setting is None or setting.value.strip().lower() == "true"
