"""Tests for inline editing endpoints (entries, sections, SEHRA fields, status)."""

import pytest
from unittest.mock import patch, MagicMock


MOCK_SEHRA = {
    "id": "sehra-edit-1",
    "country": "Liberia",
    "district": "Montserrado",
    "province": "",
    "assessment_date": "2024-05-17",
    "upload_date": "2024-05-18",
    "status": "draft",
    "pdf_filename": "liberia.pdf",
    "executive_summary": "Original executive summary.",
    "recommendations": "Original recommendations.",
}


class TestPatchEntry:
    """Test PATCH /entries/{entry_id} for inline edits to qualitative entries."""

    @patch("api.routers.sehras.update_qualitative_entry")
    def test_patch_entry_theme_only(self, mock_update, client, auth_headers):
        """Update just the theme of an entry."""
        res = client.patch(
            "/api/v1/entries/entry-1",
            json={"theme": "Funding"},
            headers=auth_headers,
        )
        assert res.status_code == 200
        assert res.json()["id"] == "entry-1"
        mock_update.assert_called_once_with(
            "entry-1", theme="Funding", classification=None
        )

    @patch("api.routers.sehras.update_qualitative_entry")
    def test_patch_entry_classification_only(self, mock_update, client, auth_headers):
        """Update just the classification of an entry."""
        res = client.patch(
            "/api/v1/entries/entry-1",
            json={"classification": "barrier"},
            headers=auth_headers,
        )
        assert res.status_code == 200
        mock_update.assert_called_once_with(
            "entry-1", theme=None, classification="barrier"
        )

    @patch("api.routers.sehras.update_qualitative_entry")
    def test_patch_entry_both_fields(self, mock_update, client, auth_headers):
        """Update both theme and classification together."""
        res = client.patch(
            "/api/v1/entries/entry-1",
            json={"theme": "Curriculum Design", "classification": "enabler"},
            headers=auth_headers,
        )
        assert res.status_code == 200
        mock_update.assert_called_once_with(
            "entry-1", theme="Curriculum Design", classification="enabler"
        )

    def test_patch_entry_requires_auth(self, client):
        """PATCH /entries without auth returns 401 or 422."""
        res = client.patch(
            "/api/v1/entries/entry-1",
            json={"theme": "Funding"},
        )
        assert res.status_code in (401, 422)

    def test_patch_entry_invalid_token(self, client):
        """PATCH /entries with bad token returns 401."""
        res = client.patch(
            "/api/v1/entries/entry-1",
            json={"theme": "Funding"},
            headers={"Authorization": "Bearer bad-token"},
        )
        assert res.status_code == 401

    def test_patch_entry_expired_token(self, client, expired_headers):
        """PATCH /entries with expired token returns 401."""
        res = client.patch(
            "/api/v1/entries/entry-1",
            json={"theme": "Funding"},
            headers=expired_headers,
        )
        assert res.status_code == 401


class TestPatchSection:
    """Test PATCH /sections/{section_id} for inline edits to report sections."""

    @patch("api.routers.sehras.update_report_section")
    def test_patch_section_content(self, mock_update, client, auth_headers):
        """Update section content successfully."""
        res = client.patch(
            "/api/v1/sections/section-1",
            json={"content": "Updated enabler summary."},
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == "section-1"
        assert data["status"] == "updated"
        mock_update.assert_called_once_with("section-1", "Updated enabler summary.")

    @patch("api.routers.sehras.update_report_section")
    def test_patch_section_long_content(self, mock_update, client, auth_headers):
        """Update section with long content."""
        long_content = "A" * 5000
        res = client.patch(
            "/api/v1/sections/section-1",
            json={"content": long_content},
            headers=auth_headers,
        )
        assert res.status_code == 200
        mock_update.assert_called_once_with("section-1", long_content)

    def test_patch_section_missing_content(self, client, auth_headers):
        """PATCH /sections without content field returns 422."""
        res = client.patch(
            "/api/v1/sections/section-1",
            json={},
            headers=auth_headers,
        )
        assert res.status_code == 422

    def test_patch_section_requires_auth(self, client):
        """PATCH /sections without auth returns 401 or 422."""
        res = client.patch(
            "/api/v1/sections/section-1",
            json={"content": "Test"},
        )
        assert res.status_code in (401, 422)


class TestPatchSehraStatus:
    """Test PATCH /sehras/{sehra_id}/status for status changes."""

    @patch("api.routers.sehras.update_sehra_status")
    @patch("api.routers.sehras.get_sehra")
    def test_update_to_reviewed(self, mock_get, mock_update, client, auth_headers):
        """Update status from draft to reviewed."""
        updated = {**MOCK_SEHRA, "status": "reviewed"}
        mock_get.side_effect = [MOCK_SEHRA, updated]
        res = client.patch(
            "/api/v1/sehras/sehra-edit-1/status",
            json={"status": "reviewed"},
            headers=auth_headers,
        )
        assert res.status_code == 200
        assert res.json()["status"] == "reviewed"

    @patch("api.routers.sehras.update_sehra_status")
    @patch("api.routers.sehras.get_sehra")
    def test_update_to_published(self, mock_get, mock_update, client, auth_headers):
        """Update status to published."""
        reviewed = {**MOCK_SEHRA, "status": "reviewed"}
        published = {**MOCK_SEHRA, "status": "published"}
        mock_get.side_effect = [reviewed, published]
        res = client.patch(
            "/api/v1/sehras/sehra-edit-1/status",
            json={"status": "published"},
            headers=auth_headers,
        )
        assert res.status_code == 200
        assert res.json()["status"] == "published"

    @patch("api.routers.sehras.get_sehra")
    def test_update_invalid_status(self, mock_get, client, auth_headers):
        """Invalid status value returns 400."""
        mock_get.return_value = MOCK_SEHRA
        res = client.patch(
            "/api/v1/sehras/sehra-edit-1/status",
            json={"status": "invalid_status"},
            headers=auth_headers,
        )
        assert res.status_code == 400

    @patch("api.routers.sehras.get_sehra")
    def test_update_status_sehra_not_found(self, mock_get, client, auth_headers):
        """Status update on nonexistent SEHRA returns 404."""
        mock_get.return_value = None
        res = client.patch(
            "/api/v1/sehras/nonexistent/status",
            json={"status": "reviewed"},
            headers=auth_headers,
        )
        assert res.status_code == 404

    def test_update_status_requires_auth(self, client):
        """PATCH /sehras/{id}/status without auth returns 401 or 422."""
        res = client.patch(
            "/api/v1/sehras/sehra-edit-1/status",
            json={"status": "reviewed"},
        )
        assert res.status_code in (401, 422)


class TestGetSehraComponents:
    """Test GET /sehras/{sehra_id}/components for component retrieval."""

    @patch("api.routers.sehras.get_component_analyses")
    @patch("api.routers.sehras.get_sehra")
    def test_get_components_success(self, mock_get, mock_ca, client, auth_headers):
        """Retrieve components for a SEHRA."""
        mock_get.return_value = MOCK_SEHRA
        mock_ca.return_value = [
            {
                "id": "ca-1",
                "component": "context",
                "enabler_count": 8,
                "barrier_count": 4,
                "items": [],
                "qualitative_entries": [
                    {
                        "id": "qe-1",
                        "remark_text": "Test remark",
                        "item_id": "O10",
                        "theme": "Institutional Structure and Stakeholders",
                        "classification": "enabler",
                        "confidence": 0.9,
                        "edited_by_human": False,
                    }
                ],
                "report_sections": {
                    "enabler_summary": {
                        "id": "rs-1",
                        "content": "Strong framework.",
                        "edited_by_human": False,
                    },
                },
            },
        ]
        res = client.get(
            "/api/v1/sehras/sehra-edit-1/components",
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["component"] == "context"
        assert data[0]["enabler_count"] == 8
        assert len(data[0]["qualitative_entries"]) == 1

    @patch("api.routers.sehras.get_sehra")
    def test_get_components_not_found(self, mock_get, client, auth_headers):
        """Components for nonexistent SEHRA returns 404."""
        mock_get.return_value = None
        res = client.get(
            "/api/v1/sehras/nonexistent/components",
            headers=auth_headers,
        )
        assert res.status_code == 404


class TestGetSehraSummary:
    """Test GET /sehras/{sehra_id}/summary for executive summary retrieval."""

    @patch("api.routers.sehras.get_executive_summary")
    @patch("api.routers.sehras.get_sehra")
    def test_get_summary_success(self, mock_get, mock_summary, client, auth_headers):
        """Retrieve executive summary and recommendations."""
        mock_get.return_value = MOCK_SEHRA
        mock_summary.return_value = {
            "executive_summary": "Test summary",
            "recommendations": "Test recs",
        }
        res = client.get(
            "/api/v1/sehras/sehra-edit-1/summary",
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["executive_summary"] == "Test summary"
        assert data["recommendations"] == "Test recs"

    @patch("api.routers.sehras.get_sehra")
    def test_get_summary_not_found(self, mock_get, client, auth_headers):
        """Summary for nonexistent SEHRA returns 404."""
        mock_get.return_value = None
        res = client.get(
            "/api/v1/sehras/nonexistent/summary",
            headers=auth_headers,
        )
        assert res.status_code == 404
