"""Validated deployment limits without database or inference imports."""
from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


class PolicySettings(BaseSettings):
    APP_ENV: Literal["local", "colab", "production"] = "local"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080,http://localhost:7357,http://127.0.0.1:7357"
    TRUSTED_HOSTS: str = "localhost,127.0.0.1,[::1],testserver"
    PROXY_TRUSTED_IPS: str = "127.0.0.1"
    MAX_TEXT_CHARS: int = Field(default=5000, ge=1, le=10000)
    RATE_LIMIT_RPM: int = Field(default=60, ge=1, le=600)
    GUEST_SESSIONS_PER_MINUTE: int = Field(default=5, ge=1, le=30)
    MAX_AUDIO_UPLOAD_BYTES: int = Field(default=1_000_000, ge=32000, le=2_000_000)
    MAX_DICTIONARY_UPLOAD_BYTES: int = Field(default=1_000_000, ge=1000, le=2_000_000)
    MAX_WS_CONNECTIONS: int = Field(default=8, ge=1, le=64)
    MAX_WS_CONNECTIONS_PER_OWNER: int = Field(default=4, ge=1, le=8)
    WS_CONFIG_TIMEOUT_SECONDS: int = Field(default=5, ge=1, le=15)
    WS_IDLE_TIMEOUT_SECONDS: int = Field(default=60, ge=10, le=300)
    WS_MAX_MESSAGE_BYTES: int = Field(default=16384, ge=1920, le=64000)
    WS_BYTES_PER_SECOND: int = Field(default=64000, ge=32000, le=128000)
    TTS_AUDIO_TTL_SECONDS: int = Field(default=300, ge=30, le=3600)
    # Content in QA is saved only by an explicit flag action; purge is an operator action.
    QA_RETENTION_DAYS: int = Field(default=30, ge=1, le=90)
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore", "hide_input_in_errors": True}

    @property
    def cors_origin_list(self) -> list[str]:
        return [value.strip() for value in self.CORS_ORIGINS.split(",") if value.strip()]

    @property
    def trusted_host_list(self) -> list[str]:
        return [value.strip() for value in self.TRUSTED_HOSTS.split(",") if value.strip()]

    @model_validator(mode="after")
    def validate_boundary(self):
        for origin in self.cors_origin_list:
            parsed = urlsplit(origin)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment or "*" in origin:
                raise ValueError("CORS_ORIGINS must contain exact HTTP(S) origins without paths")
            if self.APP_ENV != "local" and parsed.scheme != "https":
                raise ValueError("Non-local browser origins require HTTPS")
        if not self.trusted_host_list or any("*" in host for host in self.trusted_host_list):
            raise ValueError("TRUSTED_HOSTS must be an explicit host allowlist")
        if "*" in self.PROXY_TRUSTED_IPS:
            raise ValueError("PROXY_TRUSTED_IPS must name only trusted proxy addresses")
        return self


@lru_cache
def get_policy_settings() -> PolicySettings:
    return PolicySettings()
