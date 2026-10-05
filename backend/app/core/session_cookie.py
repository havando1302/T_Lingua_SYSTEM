"""HttpOnly refresh-cookie policy shared by login and session routes."""
from fastapi import Response

from app.core.auth_settings import get_auth_settings


REFRESH_COOKIE_NAME = "tlingua_refresh"
REFRESH_COOKIE_PATH = "/api/session"


def set_refresh_cookie(response: Response, token: str) -> None:
    settings = get_auth_settings()
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=settings.AUTH_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=settings.APP_ENV != "local",
        samesite="strict",
        path=REFRESH_COOKIE_PATH,
    )


def clear_refresh_cookie(response: Response) -> None:
    settings = get_auth_settings()
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        secure=settings.APP_ENV != "local",
        samesite="strict",
        path=REFRESH_COOKIE_PATH,
    )
