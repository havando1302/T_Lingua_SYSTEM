import sys
import types
import io

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import torch
if not hasattr(torch, "float8_e8m0fnu"):
    torch.float8_e8m0fnu = torch.float8_e4m3fn


# 1. Tự định nghĩa một Mock Class giả lập cấu trúc AudioMetaData đúng chuẩn Python
class MockAudioMetaData:
    def __init__(self, sample_rate: int = 48000, num_frames: int = 0, num_channels: int = 1, bits_per_sample: int = 16, encoding: str = "PCM_S"):
        self.sample_rate = sample_rate
        self.num_frames = num_frames
        self.num_channels = num_channels
        self.bits_per_sample = bits_per_sample
        self.encoding = encoding

# 2. Tạo module giả lập 'torchaudio.info' ngay trên RAM để đánh lừa DeepFilterNet
info_module = types.ModuleType("torchaudio.info")
info_module.AudioMetaData = MockAudioMetaData

# Đăng ký module giả lập này trực tiếp vào hệ thống nạp module của Python
sys.modules["torchaudio.info"] = info_module


# 3. Ép module torchaudio gốc (nếu được import) cũng phải nhận diện class Mock này
try:
    import torchaudio
    torchaudio.AudioMetaData = MockAudioMetaData
except Exception:
    pass

# 4. Vá tiếp hàm resample phòng hờ lỗi truyền tham số nâng cao ở các bước sau
try:
    from torchaudio.functional import resample as original_resample
    
    def safe_resample(audio, orig_sr, new_sr, **kwargs):
        return original_resample(audio, orig_sr, new_sr)
        
    import torchaudio.functional
    torchaudio.functional.resample = safe_resample
except Exception:
    pass
# =====================================================================

import asyncio
import logging
import uvicorn

from app.core.config import (
    HOST,
    PORT
)

if __name__ == "__main__":

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        logging.getLogger("asyncio").setLevel(logging.ERROR)

    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=False,
        ws_ping_interval=30,
        ws_ping_timeout=120
    )