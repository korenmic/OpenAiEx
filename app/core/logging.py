"""Structured JSON logging configuration."""
import json
import logging
from datetime import datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for log aggregation."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        
        # Add extra fields
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "username"):
            log_data["username"] = record.username
        
        # Redact sensitive data
        message_lower = str(log_data.get("message", "")).lower()
        if "api_key" in message_lower or "bearer" in message_lower:
            log_data["message"] = "[REDACTED - contains sensitive data]"
        
        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO") -> None:
    """Set up structured JSON logging."""
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(handler)
