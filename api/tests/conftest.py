"""Shared test fixtures for SEHRA API tests."""

import os
import pytest
from unittest.mock import patch, MagicMock

# Set test env vars before importing app modules
os.environ["DATABASE_URL"] = "sqlite:///test_sehra.db"
os.environ["JWT_SECRET"] = "test-secret-key"
os.environ["JWT_EXPIRE_MINUTES"] = "60"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"

from fastapi.testclient import TestClient
from api.auth import create_access_token


@pytest.fixture(scope="session")
def _init_db():
    """Initialize test database once."""
    from api.core.db import init_db
    init_db()
    yield
    # Cleanup
    if os.path.exists("test_sehra.db"):
        os.remove("test_sehra.db")


def _clear_rate_limiter():
    """Walk the ASGI middleware stack and clear rate limiter buckets."""
    from api.main import app
    from api.core.rate_limiter import RateLimitMiddleware

    # The middleware_stack is built when TestClient starts.
    # Walk the chain of .app references to find the RateLimitMiddleware instance.
    obj = app.middleware_stack
    while obj is not None:
        if isinstance(obj, RateLimitMiddleware):
            obj._buckets.clear()
            break
        obj = getattr(obj, "app", None)


@pytest.fixture
def client(_init_db):
    """FastAPI test client (skips lifespan to avoid seeding).

    Resets the rate limiter between tests so rapid test requests
    are not throttled.
    """
    from api.main import app

    with TestClient(app, raise_server_exceptions=False) as c:
        # Clear rate limiter after the middleware stack is built
        _clear_rate_limiter()
        yield c


@pytest.fixture
def auth_headers():
    """Authorization headers with a valid analyst JWT."""
    token = create_access_token({
        "sub": "testuser",
        "name": "Test User",
        "role": "analyst",
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers():
    """Authorization headers with a valid admin JWT."""
    token = create_access_token({
        "sub": "admin",
        "name": "Admin User",
        "role": "admin",
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def expired_headers():
    """Authorization headers with an expired JWT."""
    from datetime import datetime, timedelta, timezone
    from jose import jwt
    data = {
        "sub": "testuser",
        "name": "Test User",
        "role": "analyst",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    token = jwt.encode(data, "test-secret-key", algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}
