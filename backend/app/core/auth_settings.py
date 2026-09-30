"""Authentication configuration without importing the AI runtime."""
from functools import lru_cache
from pathlib import Path
import secrets
from typing import Literal

from cryptography.fernet import Fernet
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_LOCAL_EPHEMERAL_SECRET = secrets.token_urlsafe(48)
_DEFAULT_DATABASE_URL = "sqlite:///" + (Path(__file__).resolve().parents[2] / "data" / "admin.db").as_posix()


class AuthSettings(BaseSettings):
    APP_ENV: Literal["local", "colab", "production"] = "local"
    DATABASE_URL: str = _DEFAULT_DATABASE_URL
    JWT_SECRET_KEY: str = Field(default="", repr=False)
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, ge=1, le=60)
    AUTH_GUEST_TOKEN_EXPIRE_MINUTES: int = Field(default=15, ge=1, le=60)
    AUTH_GUEST_ENABLED: bool = True
    AUTH_MAX_ACTIVE_GUEST_SESSIONS: int = Field(default=500, ge=1, le=10000)
    AUTH_REQUIRE_PRIVILEGED_MFA: bool = True
    MFA_ENCRYPTION_KEY: str = Field(default="", repr=False)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", hide_input_in_errors=True
    )

    @model_validator(mode="after")
    def validate_security_configuration(self):
        production = self.APP_ENV != "local"
        secret = self.JWT_SECRET_KEY.strip()
        if not secret:
            if production:
                raise ValueError("JWT_SECRET_KEY is required outside local development")
            self.JWT_SECRET_KEY = _LOCAL_EPHEMERAL_SECRET
        elif (
            len(secret.encode("utf-8")) < 32
            or len(set(secret)) < 12
            or "change-me" in secret.lower()
            or "changeme" in secret.lower()
        ):
            raise ValueError("JWT_SECRET_KEY must be a strong, randomly generated secret")
        if self.JWT_ALGORITHM != "HS256":
            raise ValueError("Only HS256 is supported for application session tokens")
        if production and not self.AUTH_REQUIRE_PRIVILEGED_MFA:
            raise ValueError("Privileged MFA cannot be disabled outside local development")
        if self.MFA_ENCRYPTION_KEY:
            try:
                Fernet(self.MFA_ENCRYPTION_KEY.encode("ascii"))
            except (ValueError, UnicodeError) as exc:
                raise ValueError("MFA_ENCRYPTION_KEY must be a valid Fernet key") from exc
            if self.MFA_ENCRYPTION_KEY == self.JWT_SECRET_KEY:
                raise ValueError("MFA encryption and JWT signing must use independent keys")
        elif production:
            raise ValueError("MFA_ENCRYPTION_KEY is required outside local development")
        return self


@lru_cache(maxsize=1)
def get_auth_settings() -> AuthSettings:
    return AuthSettings()
