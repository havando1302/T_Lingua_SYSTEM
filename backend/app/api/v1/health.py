"""
Health-check endpoints (Phase 6 Operations Lifecycle)
Tách bạch Liveness Probe (/health/live) và Readiness Probe (/health/ready).
Readiness kiểm tra thật database, model bắt buộc và trạng thái worker mà không để lộ chi tiết lỗi ra bên ngoài.
"""
import logging
from fastapi import APIRouter, Response, status, Request
from sqlalchemy import text
from app.ai.model_manager import model_manager
from app.core.config import settings
from app.db.database import engine

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])


@router.get("/health/live")
async def liveness_check():
    """
    Liveness probe: Kiểm tra tiến trình và event loop còn sống.
    Trả về 200 OK ngay lập tức nếu tiến trình không bị deadlock.
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_check(request: Request, response: Response):
    """
    Readiness probe: Kiểm tra hệ thống đã sẵn sàng phục vụ lưu lượng thật:
    1. Không nằm trong quá trình graceful shutdown (draining).
    2. Kết nối cơ sở dữ liệu hoạt động bình thường.
    3. Các model AI bắt buộc đã tải xong (ở môi trường production).
    4. Worker pool đang chạy và không bị chết.
    """
    is_draining = getattr(request.app.state, "is_draining", False)
    if is_draining:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "draining", "ready": False}

    # 1. Kiểm tra Database
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_ok = True
    except Exception as exc:
        logger.error("readiness_db_check_failed: %s", type(exc).__name__)
        db_ok = False

    # 2. Kiểm tra AI Models (ở production bắt buộc phải loaded)
    models_ok = model_manager.is_loaded
    if settings.APP_ENV != "production":
        # Ở môi trường local/test cho phép khởi động nhanh
        models_ok = True

    # 3. Kiểm tra Worker tasks
    worker_tasks = getattr(request.app.state, "worker_tasks", [])
    expected_workers = getattr(request.app.state, "expected_worker_count", 1)
    workers_ok = len(worker_tasks) >= expected_workers and all(not task.done() for task in worker_tasks)
    if not workers_ok:
        logger.warning("readiness_workers_unavailable")

    is_ready = db_ok and models_ok and workers_ok

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "ready": False,
            "database": "ok" if db_ok else "unavailable",
            "models": "ok" if models_ok else "loading",
            "workers": "ok" if workers_ok else "error",
        }

    return {
        "status": "ready",
        "ready": True,
        "environment": settings.APP_ENV,
        "device": model_manager.device,
    }


@router.get("/health")
async def legacy_health_check(request: Request, response: Response):
    """Giữ tương thích ngược cho các client cũ gọi /health."""
    return await readiness_check(request, response)
