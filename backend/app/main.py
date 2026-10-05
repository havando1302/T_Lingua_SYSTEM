"""T-Lingua application with authenticated ingress and private audio lifecycle."""
import asyncio
import logging

import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.logging_config import setup_logging
setup_logging()

from app.core.config import settings, STT_WORKER_POOL_SIZE, TRANSLATION_WORKER_POOL_SIZE, TTS_WORKER_POOL_SIZE
from app.core.http_boundary import HTTPBoundaryMiddleware
from app.api.websocket import router as ws_router
from app.api.routes import router as api_router
from app.api.admin_routes import router as admin_router
from app.api.training_routes import router as training_router
from app.api.auth_routes import router as auth_router
from app.api.v1.health import router as health_router
from app.db.database import SessionLocal
from app.db.init_db import init_db
from app.services.audio_storage import sweep_audio
from app.workers.stt_worker import stt_worker
from app.workers.translation_worker import translation_worker
from app.workers.tts_worker import tts_worker
from app.ai.model_manager import model_manager

logger = logging.getLogger(__name__)
app = FastAPI(title="T-Lingua API", version="1.1.0")

app.add_middleware(HTTPBoundaryMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$" if settings.APP_ENV == "local" else None,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_host_list)


@app.middleware("http")
async def _log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    if request.url.path not in ("/api/v1/health", "/health", "/favicon.ico"):
        status = response.status_code
        indicator = "OK" if status < 400 else "CLIENT" if status < 500 else "SERVER"
        logger.info(
            "%s [HTTP] %s %s -> %d (%.1fms)",
            indicator,
            request.method,
            getattr(request.scope.get("route"), "path", "<unmatched>"),
            status,
            duration_ms,
        )
    return response


def _sweep_private_audio():
    with SessionLocal() as db:
        sweep_audio(db)


async def _audio_cleanup_loop():
    while True:
        await asyncio.sleep(30)
        try:
            await asyncio.to_thread(_sweep_private_audio)
        except Exception as error:
            logger.error("audio_cleanup_failed error_type=%s", type(error).__name__)


@app.on_event("startup")
async def _on_startup():
    app.state.is_draining = False
    # Additive schema migration runs before inference or accepting traffic.
    migration = await asyncio.to_thread(init_db)
    logger.info("security_schema version=%s applied=%s", migration["version"], migration["applied"])
    await asyncio.to_thread(_sweep_private_audio)
    await asyncio.to_thread(model_manager.load_all, settings)
    tasks = [asyncio.create_task(stt_worker(i), name=f"stt-{i}") for i in range(STT_WORKER_POOL_SIZE)]
    tasks += [asyncio.create_task(translation_worker(i), name=f"translate-{i}") for i in range(TRANSLATION_WORKER_POOL_SIZE)]
    tasks += [asyncio.create_task(tts_worker(i), name=f"tts-{i}") for i in range(TTS_WORKER_POOL_SIZE)]
    tasks.append(asyncio.create_task(_audio_cleanup_loop(), name="private-audio-cleanup"))
    app.state.worker_tasks = tasks
    app.state.expected_worker_count = len(tasks)


@app.on_event("shutdown")
async def _on_shutdown():
    logger.info("system_shutdown_initiated setting_draining=True")
    app.state.is_draining = True

    # 1. Graceful drain: Cho phép các turn đang dở dang hoàn thành
    drain_wait_s = 5.0
    start = asyncio.get_event_loop().time()
    from app.core.queues import GLOBAL_STT_QUEUE, GLOBAL_TRANSLATE_QUEUE, GLOBAL_TTS_QUEUE
    while (asyncio.get_event_loop().time() - start) < drain_wait_s:
        if GLOBAL_STT_QUEUE.empty() and GLOBAL_TRANSLATE_QUEUE.empty() and GLOBAL_TTS_QUEUE.empty():
            break
        await asyncio.sleep(0.5)

    # 2. Hủy các worker tasks còn lại
    tasks = getattr(app.state, "worker_tasks", [])
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

    # 3. Dọn dẹp tài nguyên và giải phóng GPU
    try:
        await asyncio.to_thread(_sweep_private_audio)
    except Exception:
        pass

    from app.core.gpu_manager import GPU_MANAGER
    GPU_MANAGER.adaptive_cleanup(force=True)
    logger.info("system_shutdown_completed")


app.include_router(health_router, prefix="/api/v1")
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(ws_router)
app.include_router(api_router)
app.include_router(admin_router)
app.include_router(training_router)
