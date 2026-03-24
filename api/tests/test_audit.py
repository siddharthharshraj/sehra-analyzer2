"""Tests for audit trail endpoints and edit traceability."""

import pytest
from unittest.mock import patch, MagicMock


MOCK_SEHRA = {
    "id": "sehra-audit-1",
    "country": "Kenya",
    "district": "Nairobi",
    "province": "",
    "assessment_date": "2024-01-15",
    "upload_date": "2024-01-16",
    "status": "draft",
    "pdf_filename": "test.pdf",
    "executive_summary": "Original summary",
    "recommendations": "Original recs",
}

MOCK_AUDIT_ENTRIES = [
    {
        "id": "audit-1",
        "sehra_id": "sehra-audit-1",
        "user": "testuser",
        "tool_name": "edit_entry",
        "tool_args": {"entry_id": "qe-1", "classification": "barrier"},
        "old_value": "enabler",
        "new_value": "barrier",
        "rolled_back": False,
        "created_at": "2025-06-01T10:00:00",
    },
    {
        "id": "audit-2",
        "sehra_id": "sehra-audit-1",
        "user": "testuser",
        "tool_name": "edit_report_section",
        "tool_args": {"section_id": "rs-1", "content": "Updated content"},
        "old_value": "Old content",
        "new_value": "Updated content",
        "rolled_back": False,
        "created_at": "2025-06-01T10:05:00",
    },
]


class TestGetAuditLog:
    """Test GET /audit/{sehra_id} for retrieving audit entries."""

    @patch("api.routers.audit.get_audit_log")
    def test_get_audit_log_success(self, mock_fn, client, auth_headers):
        """Retrieve audit log entries for a SEHRA."""
        mock_fn.return_value = MOCK_AUDIT_ENTRIES
        res = client.get("/api/v1/audit/sehra-audit-1", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["sehra_id"] == "sehra-audit-1"
        assert data["count"] == 2
        assert len(data["entries"]) == 2
        assert data["entries"][0]["tool_name"] == "edit_entry"

    @patch("api.routers.audit.get_audit_log")
    def test_get_audit_log_empty(self, mock_fn, client, auth_headers):
        """Retrieve empty audit log for a SEHRA with no edits."""
        mock_fn.return_value = []
        res = client.get("/api/v1/audit/sehra-no-edits", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["count"] == 0
        assert data["entries"] == []

    @patch("api.routers.audit.get_audit_log")
    def test_get_audit_log_with_user_filter(self, mock_fn, client, auth_headers):
        """Filter audit log by user."""
        mock_fn.return_value = [MOCK_AUDIT_ENTRIES[0]]
        res = client.get(
            "/api/v1/audit/sehra-audit-1?user=testuser",
            headers=auth_headers,
        )
        assert res.status_code == 200
        mock_fn.assert_called_once_with(
            sehra_id="sehra-audit-1", user="testuser", limit=50
        )

    @patch("api.routers.audit.get_audit_log")
    def test_get_audit_log_with_limit(self, mock_fn, client, auth_headers):
        """Limit the number of audit log entries."""
        mock_fn.return_value = [MOCK_AUDIT_ENTRIES[0]]
        res = client.get(
            "/api/v1/audit/sehra-audit-1?limit=1",
            headers=auth_headers,
        )
        assert res.status_code == 200
        mock_fn.assert_called_once_with(
            sehra_id="sehra-audit-1", user=None, limit=1
        )

    def test_get_audit_log_requires_auth(self, client):
        """GET /audit requires authentication."""
        res = client.get("/api/v1/audit/sehra-audit-1")
        assert res.status_code in (401, 422)

    def test_get_audit_log_invalid_token(self, client):
        """GET /audit with invalid token returns 401."""
        res = client.get(
            "/api/v1/audit/sehra-audit-1",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert res.status_code == 401


class TestRollbackAction:
    """Test POST /audit/{audit_id}/rollback."""

    @patch("api.routers.audit.rollback_action")
    def test_rollback_success(self, mock_fn, client, auth_headers):
        """Successfully rollback a copilot action."""
        mock_fn.return_value = {
            "success": True,
            "audit_id": "audit-1",
            "tool_name": "edit_entry",
            "restored_value": "enabler",
        }
        res = client.post("/api/v1/audit/audit-1/rollback", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["restored_value"] == "enabler"
        mock_fn.assert_called_once_with("audit-1")

    @patch("api.routers.audit.rollback_action")
    def test_rollback_already_rolled_back(self, mock_fn, client, auth_headers):
        """Rollback fails if already rolled back."""
        mock_fn.return_value = {
            "success": False,
            "error": "Action has already been rolled back",
        }
        res = client.post("/api/v1/audit/audit-1/rollback", headers=auth_headers)
        assert res.status_code == 400
        assert "already" in res.json()["detail"].lower()

    @patch("api.routers.audit.rollback_action")
    def test_rollback_not_found(self, mock_fn, client, auth_headers):
        """Rollback fails for nonexistent audit entry."""
        mock_fn.return_value = {
            "success": False,
            "error": "Audit entry not found",
        }
        res = client.post("/api/v1/audit/nonexistent/rollback", headers=auth_headers)
        assert res.status_code == 400

    def test_rollback_requires_auth(self, client):
        """POST /audit/rollback requires authentication."""
        res = client.post("/api/v1/audit/audit-1/rollback")
        assert res.status_code in (401, 422)


class TestEntryEditTracking:
    """Verify that inline edits to entries and sections call the right functions."""

    @patch("api.routers.sehras.update_qualitative_entry")
    def test_patch_entry_calls_update(self, mock_update, client, auth_headers):
        """PATCH /entries calls update_qualitative_entry with correct args."""
        res = client.patch(
            "/api/v1/entries/qe-audit-1",
            json={"theme": "Funding", "classification": "barrier"},
            headers=auth_headers,
        )
        assert res.status_code == 200
        mock_update.assert_called_once_with(
            "qe-audit-1", theme="Funding", classification="barrier"
        )

    @patch("api.routers.sehras.update_report_section")
    def test_patch_section_calls_update(self, mock_update, client, auth_headers):
        """PATCH /sections calls update_report_section with correct args."""
        res = client.patch(
            "/api/v1/sections/rs-audit-1",
            json={"content": "Updated summary content."},
            headers=auth_headers,
        )
        assert res.status_code == 200
        mock_update.assert_called_once_with("rs-audit-1", "Updated summary content.")


class TestStatusChangeAudit:
    """Verify status changes work correctly."""

    @patch("api.routers.sehras.update_sehra_status")
    @patch("api.routers.sehras.get_sehra")
    def test_status_change_draft_to_reviewed(
        self, mock_get, mock_update, client, auth_headers
    ):
        """Change status from draft to reviewed."""
        updated = {**MOCK_SEHRA, "status": "reviewed"}
        mock_get.side_effect = [MOCK_SEHRA, updated]
        res = client.patch(
            "/api/v1/sehras/sehra-audit-1/status",
            json={"status": "reviewed"},
            headers=auth_headers,
        )
        assert res.status_code == 200
        assert res.json()["status"] == "reviewed"

    @patch("api.routers.sehras.get_sehra")
    def test_status_change_invalid(self, mock_get, client, auth_headers):
        """Invalid status returns 400."""
        mock_get.return_value = MOCK_SEHRA
        res = client.patch(
            "/api/v1/sehras/sehra-audit-1/status",
            json={"status": "approved"},
            headers=auth_headers,
        )
        assert res.status_code == 400
