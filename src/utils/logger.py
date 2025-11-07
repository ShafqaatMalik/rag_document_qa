import logging
import json
import uuid
from datetime import datetime
from typing import Any, Dict
from contextvars import ContextVar

# Context variable for trace ID
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": trace_id_var.get() or "no-trace",
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Setup structured logger with JSON formatting."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    
    return logger


def generate_trace_id() -> str:
    """Generate unique trace ID for request tracking."""
    return str(uuid.uuid4())


def set_trace_id(trace_id: str) -> None:
    """Set trace ID in context."""
    trace_id_var.set(trace_id)


def get_trace_id() -> str:
    """Get current trace ID from context."""
    return trace_id_var.get()
