"""End-to-end integration tests for the SEHRA analysis pipeline.

Tests the full flow: upload/create -> analysis -> edit -> export,
with all external services (LLM, file system) mocked.
"""

import io
import json
import pytest
from unittest.mock import patch, MagicMock


MOCK_SEHRA = {
    "id": "e2e-sehra-1",
    "country": "Liberia",
    "district": "Montserrado",
    "province": "",
    "assessment_date": "2024-05-17",
    "upload_date": "2024-05-18",
    "status": "draft",
    "pdf_filename": "liberia_test.pdf",
    "executive_summary": "Executive summary of Liberia SEHRA.",
    "recommendations": "Recommendations for Liberia.",
    "raw_extracted_data": {},
}

MOCK_COMPONENTS = [
    {
        "id": "ca-e2e-1",
        "component": "context",
        "enabler_count": 8,
        "barrier_count": 4,
        "items": [
            {
                "question": "Are there standalone school eye health programmes?",
                "item_id": "O10",
                "yes_no": "yes",
                "remark": "SHIP programme is operational.",
                "score": 1,
            }
        ],
        "qualitative_entries": [
            {
                "id": "qe-e2e-1",
                "remark_text": "SHIP programme is operational.",
                "item_id": "O10",
                "theme": "Institutional Structure and Stakeholders",
                "classification": "enabler",
                "confidence": 0.92,
                "edited_by_human": False,
            }
        ],
        "report_sections": {
            "enabler_summary": {
                "id": "rs-e2e-1",
                "content": "Strong institutional framework.",
                "edited_by_human": False,
            },
        },
    },
    {
        "id": "ca-e2e-2",
        "component": "policy",
        "enabler_count": 6,
        "barrier_count": 2,
        "items": [],
        "qualitative_entries": [],
        "report_sections": {},
    },
]

MOCK_SUMMARY = {
    "executive_summary": "Executive summary of Liberia SEHRA.",
    "recommendations": "Recommendations for Liberia.",
}


class TestFullPipelineViaAPI:
    """Test end-to-end flow through the API endpoints."""

    @patch("api.routers.sehras.list_sehras")
    def test_step1_list_sehras(self, mock_list, client, auth_headers):
        """Step 1: List SEHRAs to verify initial state."""
        mock_list.return_value = [MOCK_SEHRA]
        res = client.get("/api/v1/sehras", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 1
        assert data[0]["country"] == "Liberia"

    @patch("api.routers.sehras.get_sehra")
    def test_step2_get_sehra_detail(self, mock_get, client, auth_headers):
        """Step 2: Get detailed info for a specific SEHRA."""
        mock_get.return_value = MOCK_SEHRA
        res = client.get("/api/v1/sehras/e2e-sehra-1", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["country"] == "Liberia"
        assert data["executive_summary"] == "Executive summary of Liberia SEHRA."

    @patch("api.routers.sehras.get_component_analyses")
    @patch("api.routers.sehras.get_sehra")
    def test_step3_get_components(self, mock_get, mock_ca, client, auth_headers):
        """Step 3: Retrieve component analyses."""
        mock_get.return_value = MOCK_SEHRA
        mock_ca.return_value = MOCK_COMPONENTS
        res = client.get(
            "/api/v1/sehras/e2e-sehra-1/components",
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 2
        assert data[0]["component"] == "context"
        assert data[0]["enabler_count"] == 8

    @patch("api.routers.sehras.update_qualitative_entry")
    def test_step4_edit_entry(self, mock_update, client, auth_headers):
        """Step 4: Edit a qualitative entry (reclassify)."""
        res = client.patch(
            "/api/v1/entries/qe-e2e-1",
            json={"classification": "barrier", "theme": "Funding"},
            headers=auth_headers,
        )
        assert res.status_code == 200
        assert res.json()["status"] == "updated"
        mock_update.assert_called_once_with(
            "qe-e2e-1", theme="Funding", classification="barrier"
        )

    @patch("api.routers.sehras.update_report_section")
    def test_step5_edit_section(self, mock_update, client, auth_headers):
        """Step 5: Edit a report section."""
        res = client.patch(
            "/api/v1/sections/rs-e2e-1",
            json={"content": "Updated: Moderate institutional framework."},
            headers=auth_headers,
        )
        assert res.status_code == 200
        assert res.json()["status"] == "updated"
        mock_update.assert_called_once_with(
            "rs-e2e-1", "Updated: Moderate institutional framework."
        )

    @patch("api.routers.sehras.update_sehra_status")
    @patch("api.routers.sehras.get_sehra")
    def test_step6_change_status(self, mock_get, mock_update, client, auth_headers):
        """Step 6: Change status from draft to reviewed."""
        reviewed = {**MOCK_SEHRA, "status": "reviewed"}
        mock_get.side_effect = [MOCK_SEHRA, reviewed]
        res = client.patch(
            "/api/v1/sehras/e2e-sehra-1/status",
            json={"status": "reviewed"},
            headers=auth_headers,
        )
        assert res.status_code == 200
        assert res.json()["status"] == "reviewed"

    @patch("api.routers.sehras.get_executive_summary")
    @patch("api.routers.sehras.get_sehra")
    def test_step7_get_summary(self, mock_get, mock_summary, client, auth_headers):
        """Step 7: Retrieve executive summary."""
        mock_get.return_value = MOCK_SEHRA
        mock_summary.return_value = MOCK_SUMMARY
        res = client.get(
            "/api/v1/sehras/e2e-sehra-1/summary",
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert "executive" in data["executive_summary"].lower() or len(data["executive_summary"]) > 0

    @patch("api.core.report_html.generate_html_report")
    @patch("api.routers.export.db")
    def test_step8_export_html(self, mock_db, mock_gen, client, auth_headers):
        """Step 8: Export as HTML."""
        mock_db.get_sehra.return_value = MOCK_SEHRA
        mock_db.get_component_analyses.return_value = MOCK_COMPONENTS
        mock_db.get_executive_summary.return_value = MOCK_SUMMARY
        mock_gen.return_value = "<html><body>Liberia SEHRA Report</body></html>"

        res = client.get(
            "/api/v1/export/e2e-sehra-1/html",
            headers=auth_headers,
        )
        assert res.status_code == 200
        assert "text/html" in res.headers["content-type"]
        assert b"Liberia" in res.content

    @patch("api.routers.sehras.batch_approve_entries")
    @patch("api.routers.sehras.get_sehra")
    def test_step9_batch_approve(self, mock_get, mock_approve, client, auth_headers):
        """Step 9: Batch approve high-confidence entries."""
        mock_get.return_value = MOCK_SEHRA
        mock_approve.return_value = 3
        res = client.post(
            "/api/v1/sehras/e2e-sehra-1/batch-approve",
            json={"confidence_threshold": 0.85},
            headers=auth_headers,
        )
        assert res.status_code == 200
        assert res.json()["approved_count"] == 3

    @patch("api.routers.sehras.delete_sehra")
    @patch("api.routers.sehras.get_sehra")
    def test_step10_delete_sehra(self, mock_get, mock_del, client, auth_headers):
        """Step 10: Delete the SEHRA."""
        mock_get.return_value = MOCK_SEHRA
        res = client.delete("/api/v1/sehras/e2e-sehra-1", headers=auth_headers)
        assert res.status_code == 204
        mock_del.assert_called_once_with("e2e-sehra-1")


class TestExportFormats:
    """Test various export format endpoints."""

    @patch("api.routers.export.db")
    def test_export_not_found(self, mock_db, client, auth_headers):
        """Export for nonexistent SEHRA returns 404."""
        mock_db.get_sehra.return_value = None
        for fmt in ["html", "docx", "xlsx", "pdf"]:
            res = client.get(
                f"/api/v1/export/nonexistent/{fmt}",
                headers=auth_headers,
            )
            assert res.status_code == 404, f"Expected 404 for {fmt}"

    @patch("api.core.report_html.generate_html_report")
    @patch("api.routers.export.db")
    def test_export_html_content_type(self, mock_db, mock_gen, client, auth_headers):
        """HTML export returns correct content type."""
        mock_db.get_sehra.return_value = MOCK_SEHRA
        mock_db.get_component_analyses.return_value = []
        mock_db.get_executive_summary.return_value = MOCK_SUMMARY
        mock_gen.return_value = "<html>Report</html>"

        res = client.get(
            "/api/v1/export/e2e-sehra-1/html",
            headers=auth_headers,
        )
        assert res.status_code == 200
        assert "text/html" in res.headers["content-type"]
        assert "content-disposition" in res.headers

    @patch("api.core.report_gen.generate_report")
    @patch("api.routers.export.db")
    def test_export_docx_content_type(self, mock_db, mock_gen, client, auth_headers):
        """DOCX export returns correct content type."""
        mock_db.get_sehra.return_value = MOCK_SEHRA
        mock_db.get_component_analyses.return_value = []
        mock_db.get_executive_summary.return_value = MOCK_SUMMARY

        # Mock generate_report to return a BytesIO object
        buf = io.BytesIO(b"PK\x03\x04fake-docx-content")
        mock_gen.return_value = buf

        res = client.get(
            "/api/v1/export/e2e-sehra-1/docx",
            headers=auth_headers,
        )
        assert res.status_code == 200
        content_type = res.headers.get("content-type", "")
        assert "officedocument" in content_type or "octet-stream" in content_type

    def test_export_requires_auth(self, client):
        """Export endpoints require authentication."""
        for fmt in ["html", "docx", "xlsx", "pdf"]:
            res = client.get(f"/api/v1/export/test-id/{fmt}")
            assert res.status_code in (401, 422), f"Expected auth error for {fmt}"


class TestChatEndpoint:
    """Test the chat endpoint for SEHRA data queries."""

    @patch("api.routers.chat.chat_query")
    @patch("api.routers.chat.db")
    def test_chat_success(self, mock_db, mock_query, client, auth_headers):
        """Chat with valid question returns a text response."""
        mock_db.get_sehra.return_value = MOCK_SEHRA
        mock_db.get_component_analyses.return_value = MOCK_COMPONENTS

        mock_result = MagicMock()
        mock_result.text = "There are 8 enablers and 4 barriers in the context component."
        mock_result.chart = None
        mock_query.return_value = mock_result

        res = client.post(
            "/api/v1/chat",
            json={"question": "How many enablers?", "sehra_id": "e2e-sehra-1"},
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert "enablers" in data["text"].lower() or len(data["text"]) > 0

    @patch("api.routers.chat.db")
    def test_chat_sehra_not_found(self, mock_db, client, auth_headers):
        """Chat with invalid sehra_id returns 404."""
        mock_db.get_sehra.return_value = None
        res = client.post(
            "/api/v1/chat",
            json={"question": "Hello?", "sehra_id": "nonexistent"},
            headers=auth_headers,
        )
        assert res.status_code == 404

    def test_chat_requires_auth(self, client):
        """Chat endpoint requires authentication."""
        res = client.post(
            "/api/v1/chat",
            json={"question": "Hello?", "sehra_id": "test"},
        )
        assert res.status_code in (401, 422)

    def test_chat_missing_fields(self, client, auth_headers):
        """Chat without required fields returns 422."""
        res = client.post(
            "/api/v1/chat",
            json={},
            headers=auth_headers,
        )
        assert res.status_code == 422


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_ok(self, client):
        """Health endpoint returns 200 with status healthy."""
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] in ("ok", "healthy", "degraded")
