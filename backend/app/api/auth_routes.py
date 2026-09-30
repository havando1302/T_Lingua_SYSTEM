"""Server-issued guest identities and revocable session lifecycle endpoints."""
import logging
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.security import Principal, get_current_principal, issue_guest_session, revoke_session
from app.db.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/session", tags=["Sessions"])


@router.post("/guest")
def create_guest(request: Request, response: Response, db: Session = Depends(get_db)):
    from app.core.access_policy import enforce_rate

    enforce_rate(request, bucket="guest")
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    session_data = issue_guest_session(db)
    logger.info("[AUTH] Cấp phiên khách mới: owner_id=%s (hạn %ds)", session_data.get("owner_id"), session_data.get("expires_in"))
    return session_data


@router.post("/logout", status_code=204)
def logout(principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    revoke_session(principal, db)
    if principal.role == "guest":
        from app.services import translation_memory
        translation_memory.forget_guest(principal.owner_id)
    logger.info("[AUTH] Đã đăng xuất phiên: owner_id=%s", principal.owner_id)
    return Response(status_code=204, headers={"Cache-Control": "no-store"})


@router.get("/me")
def current_session(response: Response, principal: Principal = Depends(get_current_principal)):
    response.headers["Cache-Control"] = "no-store"
    return {"owner_id": principal.owner_id, "role": principal.role,
            "scopes": sorted(principal.scopes), "expires_at": principal.expires_at.isoformat()}
