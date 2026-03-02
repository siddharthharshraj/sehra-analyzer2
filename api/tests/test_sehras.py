"""Tests for SEHRA CRUD endpoints."""

import pytest
from unittest.mock import patch


MOCK_SEHRA = {
    "id": "test-id-1234",
    "country": "Kenya",
    "district": "Nairobi",
    "province": "Nairobi",
    "assessment_date": "2024-01-15",
    "upload_date": "2024-01-16",
    "status": "draft",
    "pdf_filename": "test.pdf",
    "executive_summary": "",
    "recommendations": "",
}


class TestListSehras:
    @patch("api.routers.sehras.list_sehras")
    def test_list_empty(self, mock_list, client, auth_headers):
        mock_list.return_value = []
        res = client.get("/api/v1/sehras", headers=auth_headers)
        assert res.status_code == 200
        assert res.json() == []

    @patch("api.routers.sehras.list_sehras")
    def test_list_returns_sehras(self, mock_list, client, auth_headers):
        mock_list.return_value = [MOCK_SEHRA]
        res = client.get("/api/v1/sehras", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["country"] == "Kenya"


class TestGetSehra:
    @patch("api.routers.sehras.get_sehra")
    def test_get_not_found(self, mock_get, client, auth_headers):
        mock_get.return_value = None
        res = client.get("/api/v1/sehras/nonexistent", headers=auth_headers)
        assert res.status_code == 404

    @patch("api.routers.sehras.get_sehra")
    def test_get_success(self, mock_get, client, auth_headers):
        mock_get.return_value = MOCK_SEHRA
        res = client.get("/api/v1/sehras/test-id-1234", headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["id"] == "test-id-1234"


class TestDeleteSehra:
    @patch("api.routers.sehras.get_sehra")
    def test_delete_not_found(self, mock_get, client, auth_headers):
        mock_get.return_value = None
        res = client.delete("/api/v1/sehras/nonexistent", headers=auth_headers)
        assert res.status_code == 404

    @patch("api.routers.sehras.delete_sehra")
    @patch("api.routers.sehras.get_sehra")
    def test_delete_success(self, mock_get, mock_del, client, auth_headers):
        mock_get.return_value = MOCK_SEHRA
        res = client.delete("/api/v1/sehras/test-id-1234", headers=auth_headers)
        assert res.status_code == 204
        mock_del.assert_called_once_with("test-id-1234")


class TestUpdateStatus:
    @patch("api.routers.sehras.get_sehra")
    def test_invalid_status(self, mock_get, client, auth_headers):
        mock_get.return_value = MOCK_SEHRA
        res = client.patch(
            "/api/v1/sehras/test-id-1234/status",
            json={"status": "invalid"},
            headers=auth_headers,
        )
        assert res.status_code == 400

    @patch("api.routers.sehras.update_sehra_status")
    @patch("api.routers.sehras.get_sehra")
    def test_update_status_success(self, mock_get, mock_update, client, auth_headers):
        updated = {**MOCK_SEHRA, "status": "reviewed"}
        mock_get.side_effect = [MOCK_SEHRA, updated]
        res = client.patch(
            "/api/v1/sehras/test-id-1234/status",
            json={"status": "reviewed"},
            headers=auth_headers,
        )
        assert res.status_code == 200
        assert res.json()["status"] == "reviewed"


class TestBatchApprove:
    @patch("api.routers.sehras.batch_approve_entries")
    @patch("api.routers.sehras.get_sehra")
    def test_batch_approve(self, mock_get, mock_approve, client, auth_headers):
        mock_get.return_value = MOCK_SEHRA
        mock_approve.return_value = 5
        res = client.post(
            "/api/v1/sehras/test-id-1234/batch-approve",
            json={"confidence_threshold": 0.8},
            headers=auth_headers,
        )
        assert res.status_code == 200
        assert res.json()["approved_count"] == 5
