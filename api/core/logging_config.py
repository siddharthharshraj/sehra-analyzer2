"""Logging configuration for SEHRA Analyzer.

Outputs structured logs to stdout (Railway captures stdout).
No file-based logging on ephemeral filesystem.
"""

import os
import logging
import sys


def setup_logging():
    """Configure application-wide logging to stdout."""
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

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
