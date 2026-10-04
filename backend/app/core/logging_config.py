"""
Unified Logging Configuration for T-Lingua Backend.
Outputs clean, colorized, timestamped logs to terminal for real-time monitoring.
"""
import logging
import os
import sys

# Enable ANSI escape sequences on Windows console if available
if sys.platform == "win32":
    try:
        os.system("")
    except Exception:
        pass


class ColorFormatter(logging.Formatter):
    """Clean, readable terminal log formatter with timestamps, colors, and module tags."""

    GREY = "\033[90m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, "%H:%M:%S")

        if record.levelno >= logging.ERROR:
            color = self.RED
        elif record.levelno >= logging.WARNING:
            color = self.YELLOW
        elif record.levelno >= logging.INFO:
            color = self.GREEN
        else:
            color = self.GREY

        prefix = f"{self.GREY}[{timestamp}]{self.RESET} {color}{record.levelname:<5}{self.RESET}"
        module_tag = f"{self.CYAN}[{record.name.split('.')[-1]}]{self.RESET}"
        return f"{prefix} {module_tag} {record.getMessage()}"


def setup_logging(level: int = logging.INFO):
    """Configures the root logger for terminal streaming."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColorFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear previous handlers to avoid duplicate lines
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Silence noisy low-level libraries
    for noisy in (
        "asyncio",
        "websockets",
        "urllib3",
        "multipart",
        "multipart.multipart",
        "passlib",
        "torch",
        "transformers",
        "numba",
    ):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
