"""Tests for auth endpoints."""

import pytest
from unittest.mock import patch, MagicMock


class TestLogin:
    def test_login_missing_fields(self, client):
        res = client.post("/api/v1/auth/login", json={})
        assert res.status_code == 422

    def test_login_wrong_username(self, client):
        res = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "test"},
        )
        assert res.status_code == 401

    @patch("api.routers.auth.get_session")
    def test_login_success(self, mock_session, client):
        import bcrypt

        pw_hash = bcrypt.hashpw(b"testpass", bcrypt.gensalt()).decode()
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.name = "Test User"
        mock_user.role = "analyst"
        mock_user.password_hash = pw_hash

        ctx = MagicMock()
        ctx.__enter__ = lambda s: ctx
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.query.return_value.filter.return_value.first.return_value = mock_user
        mock_session.return_value = ctx

        res = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["user"]["username"] == "testuser"
        assert data["token_type"] == "bearer"


class TestRefresh:
    def test_refresh_no_auth(self, client):
        res = client.post("/api/v1/auth/refresh")
        assert res.status_code == 422  # missing header

    def test_refresh_invalid_token(self, client):
        res = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": "Bearer invalid"},
        )
        assert res.status_code == 401

    def test_refresh_expired_token(self, client, expired_headers):
        res = client.post("/api/v1/auth/refresh", headers=expired_headers)
        assert res.status_code == 401

    def test_refresh_valid_token(self, client, auth_headers):
        res = client.post("/api/v1/auth/refresh", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["user"]["username"] == "testuser"


class TestAuthProtection:
    def test_no_token_returns_422(self, client):
        res = client.get("/api/v1/sehras")
        assert res.status_code == 422

    def test_bad_token_returns_401(self, client):
        res = client.get(
            "/api/v1/sehras",
            headers={"Authorization": "Bearer bad-token"},
        )
        assert res.status_code == 401

    def test_valid_token_succeeds(self, client, auth_headers):
        res = client.get("/api/v1/sehras", headers=auth_headers)
        assert res.status_code == 200
