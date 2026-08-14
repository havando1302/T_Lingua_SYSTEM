from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import File
from fastapi import HTTPException
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import TranslationLog

from app.services.pipeline_service import run_pipeline
from app.services.translation_service import translate_text
from app.services import translation_memory as tm

import shutil
import uuid
import os
import traceback # truy vết lỗi

router = APIRouter()

class TranslateTextRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str


_LANGUAGE_MAP = {
    "vi": "vie_Latn",
    "en": "eng_Latn",
}

def _resolve_lang(code: str) -> str:
    normalized = code.strip()
    if not normalized:
        return normalized
    mapped = _LANGUAGE_MAP.get(normalized.lower())
    return mapped or normalized


@router.post("/api/translate-text")
async def translate_text_api(payload: TranslateTextRequest):
    try:
        text = payload.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="text is required")

        source_lang = _resolve_lang(payload.source_lang)
        target_lang = _resolve_lang(payload.target_lang)
        result = translate_text(
            text,
            source_lang=source_lang,
            target_lang=target_lang
        )

        return {
            "source_text": text,
            "translated_text": result.get("translated_text", "")
        }

    except HTTPException:
        raise
    except Exception as e:
        print("LỖI NGHIÊM TRỌNG TRONG TEXT TRANSLATION:")
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/translate")
async def translate_audio(
    file: UploadFile = File(...)
):
    try:
        file_id = str(uuid.uuid4())
        temp_path = f"temp/{file_id}.wav"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = run_pipeline(temp_path)
        if os.path.exists(temp_path):
            os.remove(temp_path)

        return result

    except Exception as e:
        print("LỖI NGHIÊM TRỌNG TRONG PIPELINE:")
        traceback.print_exc() 
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
class TMEntry(BaseModel):
    source_text: str
    translated_text: str
    client_id: str = "default"


@router.get("/api/translation-memory")
async def get_translation_memory(client_id: str = "default"):
    # Lấy toàn bộ Translation Memory.
    return {
        "entries": tm.get_all(client_id),
        "count": tm.count(client_id)
    }


@router.post("/api/translation-memory")
async def add_translation_memory(entry: TMEntry):
    #Thêm hoặc cập nhật một cặp dịch.
    source = entry.source_text.strip()
    target = entry.translated_text.strip()
    client = entry.client_id.strip()

    if not source or not target:
        raise HTTPException(
            status_code=400,
            detail="source_text and translated_text are required"
        )

    success = tm.add(source, target, client)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Failed to add entry"
        )

    return {
        "message": "Added successfully",
        "source_text": source,
        "translated_text": target,
        "total_entries": tm.count(client)
    }


class TMDeleteRequest(BaseModel):
    source_text: str
    client_id: str = "default"


@router.post("/api/translation-memory/delete")
async def delete_translation_memory(entry: TMDeleteRequest):
    #Xóa một cặp dịch khỏi Translation Memory.
    source = entry.source_text.strip()
    client = entry.client_id.strip()
    
    if not source:
        raise HTTPException(
            status_code=400,
            detail="source_text is required"
        )

    success = tm.delete(source, client)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Entry not found: {source}"
        )

    return {
        "message": "Deleted successfully",
        "source_text": source,
        "total_entries": tm.count(client)
    }

class FlagTranslationRequest(BaseModel):
    source_text: str
    translated_text: str
    client_id: str = "default"

@router.post("/api/flag-translation")
async def flag_translation_api(payload: FlagTranslationRequest, db: Session = Depends(get_db)):
    log = TranslationLog(
        client_id=payload.client_id,
        source_text=payload.source_text.strip(),
        translated_text=payload.translated_text.strip(),
        is_flagged=True,
        latency=0.0,
        model_source="user_flagged"
    )
    db.add(log)
    db.commit()
    return {"ok": True}