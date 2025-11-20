import logging
import os
import sys
from typing import Optional
from logging.handlers import RotatingFileHandler


# Re-export standard levels as named constants for clarity
LOG_LEVEL_DEBUG = logging.DEBUG
LOG_LEVEL_INFO = logging.INFO
LOG_LEVEL_WARNING = logging.WARNING
LOG_LEVEL_ERROR = logging.ERROR
LOG_LEVEL_CRITICAL = logging.CRITICAL


# Defaults can be overridden via environment variables:
#   OPENAIEX_LOG_LEVEL_FILE
#   OPENAIEX_LOG_LEVEL_STDOUT
#
# Values should be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL.
def _parse_level(value: Optional[str], default: int) -> int:
    if not value:
        return default
    mapping = {
        "DEBUG": LOG_LEVEL_DEBUG,
        "INFO": LOG_LEVEL_INFO,
        "WARNING": LOG_LEVEL_WARNING,
        "ERROR": LOG_LEVEL_ERROR,
        "CRITICAL": LOG_LEVEL_CRITICAL,
    }
    return mapping.get(value.upper(), default)


def configure_logging() -> None:
    """Configure root logging for the OpenAiEx project.

    Design:
    - File handler under /tmp/openai_ex/app.log with rotation (2MB, a few backups),
      logs everything from DEBUG up.
    - Stdout handler that shows only INFO, ERROR and CRITICAL.
      WARNING and DEBUG are *not* printed to stdout, but remain in the file.
    """
    if getattr(configure_logging, "_configured", False):
        return

    os.makedirs("/tmp/openai_ex", exist_ok=True)
    log_file = "/tmp/openai_ex/app.log"

    file_level = _parse_level(os.getenv("OPENAIEX_LOG_LEVEL_FILE"), LOG_LEVEL_DEBUG)
    stdout_level = _parse_level(os.getenv("OPENAIEX_LOG_LEVEL_STDOUT"), LOG_LEVEL_INFO)

    root = logging.getLogger()
    root.setLevel(min(file_level, stdout_level, LOG_LEVEL_DEBUG))

    # Rotating file handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=2 * 1024 * 1024,  # 2MB
        backupCount=3,
    )
    file_formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(file_level)
    root.addHandler(file_handler)

    # Stdout handler
    stdout_handler = logging.StreamHandler(sys.stdout)

    class ExcludeWarningsFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[name-defined]
            # Drop WARNING (and below INFO if level demands), but allow INFO, ERROR, CRITICAL.
            return record.levelno != LOG_LEVEL_WARNING

    stdout_handler.addFilter(ExcludeWarningsFilter())
    stdout_formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    stdout_handler.setFormatter(stdout_formatter)
    stdout_handler.setLevel(stdout_level)
    root.addHandler(stdout_handler)

    # Let uvicorn loggers propagate to root so they use the same handlers/format
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True

    configure_logging._configured = True
