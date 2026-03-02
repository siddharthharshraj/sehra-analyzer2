"""Tests for form draft endpoints."""

import pytest
from unittest.mock import patch

MOCK_DRAFT = {
    "id": "draft-1",
    "user": "testuser",
    "section_progress": 2,
    "responses": {"q1": {"answer": "yes", "remark": ""}},
    "created_at": "2024-01-16T00:00:00",
    "updated_at": "2024-01-16T01:00:00",
}


class TestGetDraft:
    @patch("api.routers.drafts.db")
    def test_get_no_draft(self, mock_db, client, auth_headers):
        mock_db.get_form_draft.return_value = None
        res = client.get("/api/v1/drafts", headers=auth_headers)
        assert res.status_code == 200
        assert res.json() is None

    @patch("api.routers.drafts.db")
    def test_get_draft(self, mock_db, client, auth_headers):
        mock_db.get_form_draft.return_value = MOCK_DRAFT
        res = client.get("/api/v1/drafts", headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["section_progress"] == 2


class TestSaveDraft:
    @patch("api.routers.drafts.db")
    def test_save_draft(self, mock_db, client, auth_headers):
        mock_db.save_form_draft.return_value = "draft-1"
        mock_db.get_form_draft.return_value = MOCK_DRAFT
        res = client.put(
            "/api/v1/drafts",
            json={"section_progress": 3, "responses": {"q1": "yes"}},
            headers=auth_headers,
        )
        assert res.status_code == 200
        mock_db.save_form_draft.assert_called_once()


class TestDeleteDraft:
    @patch("api.routers.drafts.db")
    def test_delete_draft(self, mock_db, client, auth_headers):
        res = client.delete("/api/v1/drafts", headers=auth_headers)
        assert res.status_code == 204
        mock_db.delete_form_draft.assert_called_once_with("testuser")
