"""Logging configuration for SEHRA Analyzer.

Outputs structured logs to stdout (Railway captures stdout).
No file-based logging on ephemeral filesystem.

Includes:
- Request ID middleware for correlating logs per request
- Request duration logging
- Structured JSON format for production
"""

import json
import os
import logging
import sys
import time
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Context variable for per-request ID, accessible from any log call
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIDFilter(logging.Filter):
    """Inject the current request ID into every log record."""

    def filter(self, record):
        record.request_id = request_id_var.get("-")
        return True


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for production environments."""

    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable log format with request ID for development."""

    def __init__(self):
        super().__init__(
            "%(asctime)s | %(name)s | %(levelname)s | rid=%(request_id)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that assigns a unique ID to each request
    and logs the request duration upon completion."""

    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        token = request_id_var.set(rid)

        logger = logging.getLogger("sehra.api")
        start = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "%s %s %d (%.1fms)",
                request.method, request.url.path, response.status_code, duration_ms,
            )
            response.headers["X-Request-ID"] = rid
            return response
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "%s %s FAILED (%.1fms)", request.method, request.url.path, duration_ms
            )
            raise
        finally:
            request_id_var.reset(token)


def setup_logging():
    """Configure application-wide logging to stdout.

    Uses JSON format when LOG_FORMAT=json (e.g., in production),
    otherwise uses a readable text format with request ID.
    """
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_format = os.environ.get("LOG_FORMAT", "text").lower()

    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIDFilter())

    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level, logging.INFO))
    root.handlers.clear()
    root.addHandler(handler)

    # Suppress noisy third-party loggers
    for noisy in [
        "urllib3", "httpcore", "httpx", "openai", "anthropic",
        "pdfminer", "pdfplumber", "PIL", "matplotlib", "watchdog",
        "streamlit", "fsevents",
    ]:
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger("sehra").setLevel(getattr(logging, log_level, logging.INFO))
