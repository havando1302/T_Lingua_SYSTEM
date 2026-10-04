"""
T-Lingua Backend — Entry point.
Apply compatibility patches, then start uvicorn.
"""
import sys
import io

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Apply torch ecosystem patches before any AI imports.
from app.core.compat import apply_torch_patches
apply_torch_patches()

import asyncio
import logging
import uvicorn

from app.core.config import settings
from app.core.logging_config import setup_logging

setup_logging()


if __name__ == "__main__":

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        logging.getLogger("asyncio").setLevel(logging.CRITICAL)
        try:
            from asyncio.proactor_events import _ProactorBasePipeTransport
            _orig_call_connection_lost = _ProactorBasePipeTransport._call_connection_lost

            def _silent_call_connection_lost(self, exc):
                try:
                    _orig_call_connection_lost(self, exc)
                except Exception:
                    pass

            _ProactorBasePipeTransport._call_connection_lost = _silent_call_connection_lost
        except Exception:
            pass

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,
        workers=1,  # GPU models không chia sẻ qua workers → giữ 1
        ws_max_size=settings.WS_MAX_MESSAGE_BYTES,
        ws_max_queue=4,
        ws_per_message_deflate=False,
        limit_concurrency=64,
        timeout_keep_alive=10,
        forwarded_allow_ips=settings.PROXY_TRUSTED_IPS,
        access_log=False,  # Paths can contain dictionary text; never log request content.
        ws_ping_interval=30,
        ws_ping_timeout=120,
    )
