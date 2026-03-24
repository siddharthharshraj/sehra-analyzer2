"""Tests for rate limiting middleware.

The app uses an in-memory RateLimitMiddleware with per-category limits:
  - login: 10 rpm (keyed by IP)
  - llm: 20 rpm (keyed by user)
  - default: 60 rpm (keyed by user)

These tests use a separate app instance with very low limits to
verify rate limiting behavior without interfering with other tests.
"""

import os
import pytest
from unittest.mock import patch

# Ensure test env vars are set
os.environ.setdefault("DATABASE_URL", "sqlite:///test_sehra.db")
os.environ.setdefault("JWT_SECRET", "test-secret-key")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "60")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from api.core.rate_limiter import RateLimitMiddleware


@pytest.fixture
def rate_limited_app():
    """Create a minimal FastAPI app with very low rate limits for testing."""
    app = FastAPI()

    # Add rate limiter with very low limits
    app.add_middleware(RateLimitMiddleware, default_rpm=3, llm_rpm=2, login_rpm=2)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/api/v1/auth/login")
    def login():
        return {"token": "test"}

    @app.post("/api/v1/agent/chat")
    def agent_chat():
        return {"response": "test"}

    @app.get("/api/v1/sehras")
    def list_sehras():
        return []

    return app


@pytest.fixture
def rate_client(rate_limited_app):
    """Test client for the rate-limited app."""
    with TestClient(rate_limited_app) as c:
        yield c


class TestRateLimitLogin:
    """Test login endpoint rate limiting."""

    def test_login_under_limit_succeeds(self, rate_client):
        """First 2 login requests should succeed."""
        for i in range(2):
            res = rate_client.post("/api/v1/auth/login")
            assert res.status_code == 200, f"Request {i+1} should succeed"

    def test_login_exceeds_limit(self, rate_client):
        """After 2 requests, login should be rate limited."""
        # Use up the limit
        for _ in range(2):
            rate_client.post("/api/v1/auth/login")

        # This should be rate limited
        res = rate_client.post("/api/v1/auth/login")
        assert res.status_code == 429
        assert "Retry-After" in res.headers
        assert "rate limit" in res.json()["detail"].lower()


class TestRateLimitDefault:
    """Test default endpoint rate limiting."""

    def test_default_under_limit_succeeds(self, rate_client):
        """First 3 requests to a default endpoint should succeed."""
        for i in range(3):
            res = rate_client.get("/api/v1/sehras")
            assert res.status_code == 200, f"Request {i+1} should succeed"

    def test_default_exceeds_limit(self, rate_client):
        """After 3 requests, default endpoints should be rate limited."""
        for _ in range(3):
            rate_client.get("/api/v1/sehras")

        res = rate_client.get("/api/v1/sehras")
        assert res.status_code == 429


class TestRateLimitLLM:
    """Test LLM endpoint rate limiting."""

    def test_llm_under_limit_succeeds(self, rate_client):
        """First 2 LLM requests should succeed."""
        for i in range(2):
            res = rate_client.post("/api/v1/agent/chat")
            assert res.status_code == 200, f"Request {i+1} should succeed"

    def test_llm_exceeds_limit(self, rate_client):
        """After 2 requests, LLM endpoints should be rate limited."""
        for _ in range(2):
            rate_client.post("/api/v1/agent/chat")

        res = rate_client.post("/api/v1/agent/chat")
        assert res.status_code == 429


class TestRateLimitCategories:
    """Test that different categories have independent limits."""

    def test_login_and_default_independent(self, rate_client):
        """Login and default endpoints should have independent limits."""
        # Use up login limit
        for _ in range(2):
            rate_client.post("/api/v1/auth/login")

        # Login should be limited
        res = rate_client.post("/api/v1/auth/login")
        assert res.status_code == 429

        # But default endpoints should still work
        res = rate_client.get("/api/v1/sehras")
        assert res.status_code == 200

    def test_health_not_rate_limited_as_login(self, rate_client):
        """Health endpoint uses default limits, not login limits."""
        # Use up login limit
        for _ in range(2):
            rate_client.post("/api/v1/auth/login")

        # Health should use default category, still have quota
        res = rate_client.get("/health")
        assert res.status_code == 200


class TestRateLimitResponseFormat:
    """Test rate limit response format."""

    def test_429_response_has_retry_after(self, rate_client):
        """429 response includes Retry-After header."""
        for _ in range(2):
            rate_client.post("/api/v1/auth/login")

        res = rate_client.post("/api/v1/auth/login")
        assert res.status_code == 429
        assert "Retry-After" in res.headers
        retry_after = int(res.headers["Retry-After"])
        assert retry_after > 0

    def test_429_response_has_detail(self, rate_client):
        """429 response includes detail message with category info."""
        for _ in range(2):
            rate_client.post("/api/v1/auth/login")

        res = rate_client.post("/api/v1/auth/login")
        assert res.status_code == 429
        detail = res.json()["detail"]
        assert "login" in detail.lower()


class TestSharePasscodeRateLimit:
    """Test share passcode rate limiting (application-level, not middleware)."""

    @patch("api.routers.share.db")
    def test_passcode_rate_limited_after_5_attempts(self, mock_db, client):
        """After 5 failed attempts, verify endpoint returns 429."""
        mock_db.get_shared_report_by_token.return_value = {
            "id": "r1",
            "is_active": True,
            "expires_at": None,
        }
        mock_db.count_failed_attempts.return_value = 5

        res = client.post(
            "/api/v1/public/share/test-token/verify",
            json={"passcode": "wrong"},
        )
        assert res.status_code == 429

    @patch("api.routers.share.db")
    def test_passcode_under_threshold_allowed(self, mock_db, client):
        """Under 5 failed attempts, verify request is processed."""
        mock_db.get_shared_report_by_token.return_value = {
            "id": "r1",
            "is_active": True,
            "expires_at": None,
        }
        mock_db.count_failed_attempts.return_value = 2
        mock_db.verify_share_passcode.return_value = False

        res = client.post(
            "/api/v1/public/share/test-token/verify",
            json={"passcode": "wrong"},
        )
        assert res.status_code == 200
        assert res.json()["success"] is False
