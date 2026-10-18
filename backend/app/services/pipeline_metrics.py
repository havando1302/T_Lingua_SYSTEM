"""Durable, content-free storage for realtime pipeline telemetry."""
from __future__ import annotations

import hashlib
import logging

from app.core.telemetry import TurnMetric
from app.db.database import SessionLocal
from app.db.models import PipelineMetric

logger = logging.getLogger(__name__)


def _positive_or_none(value: float) -> float | None:
    return round(value, 2) if value > 0 else None


def persist_pipeline_metric(
    metric: TurnMetric | None,
    *,
    status: str = "success",
    error_stage: str | None = None,
) -> None:
    """Persist timings without transcript, translation, audio, or raw session ID."""
    if metric is None:
        return
    session_hash = hashlib.sha256(metric.session_id.encode("utf-8")).hexdigest() if metric.session_id else None
    try:
        with SessionLocal() as db:
            existing = db.query(PipelineMetric).filter(PipelineMetric.turn_id == metric.turn_id).first()
            if existing is not None:
                return
            db.add(PipelineMetric(
                turn_id=metric.turn_id,
                session_id_hash=session_hash,
                source_lang=metric.source_lang,
                target_lang=metric.target_lang,
                status=status,
                error_stage=error_stage,
                error_code=metric.error,
                queue_wait_ms=_positive_or_none(metric.queue_wait_ms),
                stt_ms=_positive_or_none(metric.stt_ms),
                translate_ms=_positive_or_none(metric.translate_ms),
                tts_first_chunk_ms=_positive_or_none(metric.tts_first_chunk_ms),
                tts_total_ms=_positive_or_none(metric.tts_total_ms),
                end_to_end_ms=_positive_or_none(metric.total_latency_ms),
                audio_duration_s=round(metric.audio_duration_s, 3) if metric.audio_duration_s > 0 else None,
                text_length=metric.text_length or None,
                created_at=metric.received_at,
            ))
            db.commit()
    except Exception as error:
        # Telemetry must never make the inference pipeline fail.
        logger.warning("pipeline_metric_persist_failed error_type=%s", type(error).__name__)
