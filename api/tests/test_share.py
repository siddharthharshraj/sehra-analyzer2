"""Tests for share endpoints."""

import pytest
from unittest.mock import patch, MagicMock


MOCK_SHARE = {
    "id": "share-1",
    "share_token": "abc123token",
    "created_by": "testuser",
    "created_at": "2024-01-16T00:00:00",
    "expires_at": "2024-01-23T00:00:00",
    "is_active": True,
    "view_count": 0,
}


class TestListShares:
    @patch("api.routers.share.db")
    def test_list_shares(self, mock_db, client, auth_headers):
        mock_db.list_shared_reports.return_value = [MOCK_SHARE]
        res = client.get("/api/v1/shares/sehra-1", headers=auth_headers)
        assert res.status_code == 200
        assert len(res.json()) == 1


class TestRevokeShare:
    @patch("api.routers.share.db")
    def test_revoke(self, mock_db, client, auth_headers):
        res = client.delete("/api/v1/shares/abc123token", headers=auth_headers)
        assert res.status_code == 204
        mock_db.revoke_shared_report.assert_called_once_with("abc123token")


class TestPublicShareCheck:
    @patch("api.routers.share.db")
    def test_check_invalid(self, mock_db, client):
        mock_db.get_shared_report_by_token.return_value = None
        res = client.get("/api/v1/public/share/bad-token")
        assert res.status_code == 200
        assert res.json()["valid"] is False

    @patch("api.routers.share.db")
    def test_check_valid(self, mock_db, client):
        mock_db.get_shared_report_by_token.return_value = {
            "is_active": True,
            "expires_at": None,
        }
        res = client.get("/api/v1/public/share/good-token")
        assert res.status_code == 200
        data = res.json()
        assert data["valid"] is True
        assert data["needs_passcode"] is True


class TestVerifyPasscode:
    @patch("api.routers.share.db")
    def test_verify_not_found(self, mock_db, client):
        mock_db.get_shared_report_by_token.return_value = None
        res = client.post(
            "/api/v1/public/share/bad-token/verify",
            json={"passcode": "test"},
        )
        assert res.status_code == 404

    @patch("api.routers.share.db")
    def test_verify_wrong_passcode(self, mock_db, client):
        mock_db.get_shared_report_by_token.return_value = {
            "id": "r1",
            "is_active": True,
            "expires_at": None,
        }
        mock_db.count_failed_attempts.return_value = 0
        mock_db.verify_share_passcode.return_value = False
        res = client.post(
            "/api/v1/public/share/good-token/verify",
            json={"passcode": "wrong"},
        )
        assert res.status_code == 200
        assert res.json()["success"] is False

    @patch("api.routers.share.db")
    def test_verify_rate_limited(self, mock_db, client):
        mock_db.get_shared_report_by_token.return_value = {
            "id": "r1",
            "is_active": True,
            "expires_at": None,
        }
        mock_db.count_failed_attempts.return_value = 5
        res = client.post(
            "/api/v1/public/share/good-token/verify",
            json={"passcode": "test"},
        )
        assert res.status_code == 429
