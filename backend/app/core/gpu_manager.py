"""
Adaptive GPU Memory and Resource Governor (Phase 5 Performance Optimization)
- Đặt ngân sách tài nguyên chung cho GPU, đồng thời kiểm soát số tác vụ theo model.
- Đánh giá lại việc giải phóng GPU cache sau mỗi câu: loại bỏ overhead torch.cuda.empty_cache() liên tục.
"""
import asyncio
import time
import logging
import torch
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class GPUResourceManager:
    """
    Quản lý tài nguyên GPU tập trung và điều phối dọn dẹp cache thích ứng.
    """
    def __init__(self, memory_threshold_ratio: float = 0.85, idle_cleanup_interval_s: float = 10.0):
        self._threshold = memory_threshold_ratio
        self._idle_interval = idle_cleanup_interval_s
        self._last_cleanup_time = time.time()
        self._last_activity_time = time.time()
        self._total_cleanups = 0
        self._skipped_cleanups = 0

    def is_cuda_available(self) -> bool:
        return torch.cuda.is_available()

    def get_memory_stats(self) -> Dict[str, Any]:
        if not self.is_cuda_available():
            return {
                "cuda_available": False,
                "device_name": "CPU",
                "allocated_mb": 0.0,
                "reserved_mb": 0.0,
                "total_mb": 0.0,
                "utilization_ratio": 0.0,
            }

        allocated = torch.cuda.memory_allocated()
        reserved = torch.cuda.memory_reserved()
        total = torch.cuda.get_device_properties(0).total_memory

        return {
            "cuda_available": True,
            "device_name": torch.cuda.get_device_name(0),
            "allocated_mb": round(allocated / (1024 * 1024), 2),
            "reserved_mb": round(reserved / (1024 * 1024), 2),
            "total_mb": round(total / (1024 * 1024), 2),
            "utilization_ratio": round(reserved / total if total > 0 else 0.0, 3),
        }

    def adaptive_cleanup(self, force: bool = False) -> bool:
        """
        Dọn dẹp cache có điều kiện (Adaptive Cache Policy):
        - Chỉ gọi empty_cache() nếu tỷ lệ VRAM reserved vượt ngưỡng (mặc định 85%)
        - Hoặc khi đã idle quá interval quy định
        - Hoặc khi có cờ force=True (ví dụ: OOM recovery hoặc shutdown)
        """
        now = time.time()
        self._last_activity_time = now

        if not self.is_cuda_available():
            return False

        stats = self.get_memory_stats()
        ratio = stats.get("utilization_ratio", 0.0)
        is_idle_expired = (now - self._last_cleanup_time) > self._idle_interval

        if force or ratio >= self._threshold or (is_idle_expired and ratio > 0.5):
            torch.cuda.empty_cache()
            self._last_cleanup_time = now
            self._total_cleanups += 1
            logger.debug(
                "adaptive_gpu_cleanup executed ratio=%.2f forced=%s cleanups=%d",
                ratio, force, self._total_cleanups
            )
            return True
        else:
            self._skipped_cleanups += 1
            return False


class ModelConcurrencyGovernor:
    """
    Điều phối số lượng tác vụ song song đồng thời trên toàn bộ pipeline (HTTP + WebSocket).
    """
    def __init__(self, stt_limit: int = 4, translate_limit: int = 4, tts_limit: int = 4, total_gpu_limit: int = 8):
        self.stt_sem = asyncio.Semaphore(stt_limit)
        self.translate_sem = asyncio.Semaphore(translate_limit)
        self.tts_sem = asyncio.Semaphore(tts_limit)
        self.total_gpu_sem = asyncio.Semaphore(total_gpu_limit)

    async def acquire_stt(self):
        await self.total_gpu_sem.acquire()
        try:
            await self.stt_sem.acquire()
        except:
            self.total_gpu_sem.release()
            raise

    def release_stt(self):
        self.stt_sem.release()
        self.total_gpu_sem.release()

    async def acquire_translate(self):
        await self.total_gpu_sem.acquire()
        try:
            await self.translate_sem.acquire()
        except:
            self.total_gpu_sem.release()
            raise

    def release_translate(self):
        self.translate_sem.release()
        self.total_gpu_sem.release()

    async def acquire_tts(self):
        await self.total_gpu_sem.acquire()
        try:
            await self.tts_sem.acquire()
        except:
            self.total_gpu_sem.release()
            raise

    def release_tts(self):
        self.tts_sem.release()
        self.total_gpu_sem.release()


# Global singletons
GPU_MANAGER = GPUResourceManager()
GPU_GOVERNOR = ModelConcurrencyGovernor()
