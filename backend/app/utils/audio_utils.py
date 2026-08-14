import math

import numpy as np
from scipy import signal

BACKEND_SAMPLE_RATE = 16000
_BUTTER_ORDER = 4
_HP_CUTOFF = 80.0
_LP_CUTOFF = 7000.0

_HP_B, _HP_A = signal.butter(
    _BUTTER_ORDER,
    _HP_CUTOFF,
    btype="highpass",
    fs=BACKEND_SAMPLE_RATE
)
_LP_B, _LP_A = signal.butter(
    _BUTTER_ORDER,
    _LP_CUTOFF,
    btype="lowpass",
    fs=BACKEND_SAMPLE_RATE
)


def pcm_to_numpy(audio_bytes: bytes) -> np.ndarray:
    if not audio_bytes:
        return np.array([], dtype=np.float32)

    audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
    audio_np /= 32768.0
    return audio_np


def pcm_bytes_to_mono_16k_bytes(
    audio_bytes: bytes,
    sample_rate: int,
    channels: int,
    sample_width: int
) -> bytes:
    if not audio_bytes:
        return b""

    if sample_width != 2:
        raise ValueError("Only 16-bit PCM is supported")

    audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
    audio_np /= 32768.0

    if channels > 1:
        audio_np = audio_np.reshape(-1, channels).mean(axis=1)

    if sample_rate != BACKEND_SAMPLE_RATE:
        gcd = math.gcd(sample_rate, BACKEND_SAMPLE_RATE)
        up = BACKEND_SAMPLE_RATE // gcd
        down = sample_rate // gcd
        audio_np = signal.resample_poly(audio_np, up, down)

    audio_np = np.clip(audio_np, -1.0, 1.0)
    audio_int16 = (audio_np * 32767.0).astype(np.int16)
    return audio_int16.tobytes()


def preprocess_audio_numpy(audio_np: np.ndarray) -> np.ndarray:
    if audio_np.size == 0:
        return audio_np

    # Buoc 1: Loai DC offset de giu tin hieu on dinh.
    audio_np = audio_np - float(np.mean(audio_np))

    # Buoc 2: Loc high-pass va low-pass de giam nhieu.
    audio_np = signal.lfilter(_HP_B, _HP_A, audio_np)
    audio_np = signal.lfilter(_LP_B, _LP_A, audio_np)

    # Buoc 3: Chuan hoa am luong len 95% bien do toi da.
    peak = float(np.max(np.abs(audio_np)))
    if peak > 0.0:
        audio_np = audio_np * (0.95 / peak)

    return audio_np.astype(np.float32, copy=False)