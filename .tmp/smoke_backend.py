"""Sandbox-only launcher: redirect private runtime files into writable temp."""
from pathlib import Path

import uvicorn

from app.services import audio_storage, training_audio_storage

runtime = Path(__file__).resolve().parent / "trial_runtime"
audio_storage.SECURE_OUTPUT_DIR = runtime / "outputs" / "secure"
audio_storage.SECURE_TEMP_DIR = runtime / "temp" / "secure"
training_audio_storage.TRAINING_AUDIO_DIR = runtime / "data" / "training_audio"

uvicorn.run(
    "app.main:app", host="127.0.0.1", port=8000, workers=1,
    ws_max_size=16384, access_log=False,
)
