"""Server-issued guest identities and revocable session lifecycle endpoints."""
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.security import (
    Principal,
    authenticate_token,
    get_current_principal,
    issue_guest_session,
    oauth2_scheme,
    revoke_refresh_session,
    revoke_session,
    refresh_user_session,
)
from app.core.session_cookie import REFRESH_COOKIE_NAME, clear_refresh_cookie, set_refresh_cookie
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
    logger.info("[AUTH] guest_session_created owner_id=%s expires_in=%ss", session_data.get("owner_id"), session_data.get("expires_in"))
    return session_data


@router.post("/logout", status_code=204)
def logout(request: Request, token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    principal = None
    try:
        principal = authenticate_token(token, db)
        revoke_session(principal, db)
    except HTTPException:
        pass
    revoke_refresh_session(request.cookies.get(REFRESH_COOKIE_NAME), db)
    if principal is not None and principal.role == "guest":
        from app.services import translation_memory
        translation_memory.forget_guest(principal.owner_id)
    logger.info("[AUTH] session_logged_out owner_id=%s", principal.owner_id if principal else "cookie")
    response = Response(status_code=204, headers={"Cache-Control": "no-store"})
    clear_refresh_cookie(response)
    return response


@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    try:
        session, user, rotated_refresh_token = refresh_user_session(
            request.cookies.get(REFRESH_COOKIE_NAME), db,
        )
    except HTTPException as error:
        invalid = JSONResponse(
            status_code=error.status_code,
            content={"detail": error.detail},
            headers=error.headers,
        )
        return invalid
    response.headers["Cache-Control"] = "no-store"
    set_refresh_cookie(response, rotated_refresh_token)
    return {
        **session,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "public_id": user.public_id,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "mfa_enabled": user.mfa_enabled,
        },
    }


@router.get("/me")
def current_session(response: Response, principal: Principal = Depends(get_current_principal)):
    response.headers["Cache-Control"] = "no-store"
    return {"owner_id": principal.owner_id, "role": principal.role,
            "scopes": sorted(principal.scopes), "expires_at": principal.expires_at.isoformat()}
