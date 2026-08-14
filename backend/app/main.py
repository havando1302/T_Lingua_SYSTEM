import asyncio
import mimetypes
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi.staticfiles import (
    StaticFiles
)

from app.api.websocket import router
from app.api.routes import router as api_router
from app.api.admin_routes import router as admin_router

from app.core.config import (
    OUTPUT_DIR,
    STT_WORKER_POOL_SIZE,
    TRANSLATION_WORKER_POOL_SIZE,
    TTS_WORKER_POOL_SIZE
)

from app.workers.stt_worker import stt_worker
from app.workers.translation_worker import translation_worker
from app.workers.tts_worker import tts_worker

app = FastAPI()

mimetypes.add_type("audio/wav", ".wav")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _start_worker_pool() -> None:
    # Khoi tao worker pool dung chung de xu ly nhieu session.
    tasks = []
    for i in range(STT_WORKER_POOL_SIZE):
        tasks.append(asyncio.create_task(stt_worker(i)))
    for i in range(TRANSLATION_WORKER_POOL_SIZE):
        tasks.append(asyncio.create_task(translation_worker(i)))
    for i in range(TTS_WORKER_POOL_SIZE):
        tasks.append(asyncio.create_task(tts_worker(i)))
    app.state.worker_tasks = tasks


@app.on_event("shutdown")
async def _stop_worker_pool() -> None:
    tasks = getattr(app.state, "worker_tasks", [])
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

app.include_router(router)
app.include_router(api_router)
app.include_router(admin_router)

app.mount(
    "/audio",
    StaticFiles(directory=OUTPUT_DIR),
    name="audio"
)