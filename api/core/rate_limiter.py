"""In-memory rate limiting middleware for FastAPI.

Designed for small deployments (40-50 users). No Redis dependency.
Tracks request counts per IP/user with per-endpoint category limits.
"""

import time
import logging
from collections import defaultdict
from threading import Lock

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("sehra.rate_limiter")

# Paths that count toward LLM rate limits
LLM_PATHS = ("/api/v1/agent/chat", "/api/v1/chat", "/api/v1/analyze")

# Login path gets its own stricter limit
LOGIN_PATH = "/api/v1/auth/login"

# Cleanup interval: purge stale entries every 5 minutes
_CLEANUP_INTERVAL = 300


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-endpoint-category rate limiter with lazy cleanup.

    Categories:
        - login:  LOGIN_PATH, keyed by IP, default 10 rpm
        - llm:    LLM_PATHS (prefix match), keyed by user (from Authorization header), default 20 rpm
        - default: everything else, keyed by user or IP, default 60 rpm
    """

    def __init__(self, app, default_rpm: int = 60, llm_rpm: int = 20, login_rpm: int = 10):
        super().__init__(app)
        self.default_rpm = default_rpm
        self.llm_rpm = llm_rpm
        self.login_rpm = login_rpm

        # Stores: {category:key -> list of timestamps}
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()
        self._last_cleanup = time.monotonic()

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        now = time.monotonic()

        # Lazy cleanup of stale entries
        if now - self._last_cleanup > _CLEANUP_INTERVAL:
            self._cleanup(now)

        # Determine category and rate limit
        category, key, rpm = self._classify(request, path)

        # Check rate limit
        bucket_key = f"{category}:{key}"
        retry_after = self._check_limit(bucket_key, rpm, now)

        if retry_after is not None:
            logger.warning(
                "Rate limit exceeded: category=%s key=%s path=%s",
                category, key, path,
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded. Max {rpm} requests per minute for {category} endpoints.",
                },
                headers={"Retry-After": str(int(retry_after))},
            )

        response = await call_next(request)
        return response

    def _classify(self, request: Request, path: str) -> tuple[str, str, int]:
        """Classify a request into (category, key, rpm_limit)."""
        client_ip = request.client.host if request.client else "unknown"

        if path == LOGIN_PATH:
            return "login", client_ip, self.login_rpm

        if any(path.startswith(p) for p in LLM_PATHS):
            user_key = self._extract_user(request) or client_ip
            return "llm", user_key, self.llm_rpm

        user_key = self._extract_user(request) or client_ip
        return "default", user_key, self.default_rpm

    def _extract_user(self, request: Request) -> str | None:
        """Extract username from Authorization header without full JWT validation.

        This is a best-effort extraction for rate limiting purposes only.
        Actual authentication is handled by the route dependencies.
        """
        auth = request.headers.get("authorization", "")
        if not auth.startswith("Bearer "):
            return None
        token = auth[7:]
        if not token:
            return None
        # Decode JWT payload without verification (rate limiting only, not auth)
        try:
            import base64
            # JWT structure: header.payload.signature
            parts = token.split(".")
            if len(parts) != 3:
                return None
            # Add padding
            payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
            import json
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
            return payload.get("sub")
        except Exception:
            return None

    def _check_limit(self, bucket_key: str, rpm: int, now: float) -> float | None:
        """Check if a request exceeds the rate limit.

        Returns None if allowed, or the number of seconds to wait if exceeded.
        """
        window = 60.0  # 1-minute sliding window

        with self._lock:
            timestamps = self._buckets[bucket_key]

            # Remove timestamps outside the window
            cutoff = now - window
            while timestamps and timestamps[0] < cutoff:
                timestamps.pop(0)

            if len(timestamps) >= rpm:
                # Calculate when the oldest request in the window expires
                wait = timestamps[0] - cutoff
                return max(wait, 1.0)

            # Allow the request
            timestamps.append(now)
            return None

    def _cleanup(self, now: float):
        """Remove stale bucket entries to prevent memory growth."""
        cutoff = now - 60.0
        with self._lock:
            stale_keys = [
                k for k, timestamps in self._buckets.items()
                if not timestamps or timestamps[-1] < cutoff
            ]
            for k in stale_keys:
                del self._buckets[k]
            self._last_cleanup = now
            if stale_keys:
                logger.debug("Rate limiter cleanup: removed %d stale buckets", len(stale_keys))
