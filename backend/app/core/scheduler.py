"""
Fair-Share Pipeline Scheduler (Phase 5 Performance Optimization)
Thay thế cơ chế quét rồi đưa lại hàng đợi bằng lập lịch công bằng theo phiên/người dùng.
Đảm bảo một session không thể làm đói (starve) các session khác và ngăn chặn tràn bộ nhớ.
"""
import asyncio
from typing import Dict, Optional, Any, List
from collections import deque
import logging

logger = logging.getLogger(__name__)


class FairSessionQueue:
    """
    Hàng đợi đa phiên công bằng (Deficit / Round-Robin Fair Queue).
    Mỗi session có một sub-queue riêng.
    Các worker lấy item theo vòng tròn giữa các session đang có dữ liệu.
    """
    def __init__(self, max_per_session: int = 15, max_total_items: int = 200):
        self._max_per_session = max_per_session
        self._max_total_items = max_total_items
        self._session_queues: Dict[str, deque[Any]] = {}
        self._active_sessions: deque[str] = deque()
        self._lock = asyncio.Lock()
        self._not_empty = asyncio.Event()
        self._total_items = 0

    async def put(self, item: Any, session_id: Optional[str] = None) -> bool:
        """
        Đưa một item vào hàng đợi của session tương ứng.
        Nếu session vượt quá quota hoặc tổng queue quá tải, trả về False (quá tải).
        """
        sid = session_id or "default"
        async with self._lock:
            if self._total_items >= self._max_total_items:
                logger.warning("fair_queue_full total_items=%d limit=%d", self._total_items, self._max_total_items)
                return False

            if sid not in self._session_queues:
                self._session_queues[sid] = deque()
                self._active_sessions.append(sid)

            q = self._session_queues[sid]
            if len(q) >= self._max_per_session:
                logger.warning("fair_queue_session_full session_id=%s queue_len=%d", sid, len(q))
                return False

            q.append(item)
            self._total_items += 1
            self._not_empty.set()
            return True

    async def get(self) -> Any:
        """
        Lấy item tiếp theo theo cơ chế Round-Robin giữa các active session.
        Chờ nếu toàn bộ hàng đợi đang trống.
        """
        while True:
            async with self._lock:
                if self._total_items > 0:
                    break
                self._not_empty.clear()

            await self._not_empty.wait()

        async with self._lock:
            # Round-robin selection
            searched = 0
            num_sessions = len(self._active_sessions)

            while searched < num_sessions:
                sid = self._active_sessions.popleft()
                q = self._session_queues.get(sid)

                if q and len(q) > 0:
                    item = q.popleft()
                    self._total_items -= 1
                    # Nếu session vẫn còn item, đưa lại vào cuối vòng lặp
                    if len(q) > 0:
                        self._active_sessions.append(sid)
                    else:
                        del self._session_queues[sid]

                    if self._total_items == 0:
                        self._not_empty.clear()
                    return item
                else:
                    # Dọn dẹp session rỗng
                    self._session_queues.pop(sid, None)
                    searched += 1

            # Fallback nếu toàn bộ rỗng ngoài dự kiến
            self._not_empty.clear()
            raise asyncio.QueueEmpty()

    async def cancel_session(self, session_id: str) -> int:
        """Hủy toàn bộ pending items của một session (khi disconnect hoặc reset)"""
        async with self._lock:
            q = self._session_queues.pop(session_id, None)
            dropped = 0
            if q:
                dropped = len(q)
                self._total_items -= dropped
                # Loại bỏ khỏi active_sessions
                self._active_sessions = deque(s for s in self._active_sessions if s != session_id)
                if self._total_items == 0:
                    self._not_empty.clear()
            return dropped

    def qsize(self) -> int:
        return self._total_items

    def empty(self) -> bool:
        return self._total_items == 0

    def active_session_count(self) -> int:
        return len(self._session_queues)


# Global Fair Queues cho Pipeline
FAIR_STT_QUEUE = FairSessionQueue(max_per_session=15, max_total_items=300)
FAIR_TRANSLATE_QUEUE = FairSessionQueue(max_per_session=15, max_total_items=300)
FAIR_TTS_QUEUE = FairSessionQueue(max_per_session=15, max_total_items=300)
