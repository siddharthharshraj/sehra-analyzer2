"""Tests for export endpoints."""

import io
import pytest
from unittest.mock import patch, MagicMock


MOCK_SEHRA = {
    "id": "test-id-1234",
    "country": "Kenya",
    "district": "Nairobi",
    "province": "",
    "assessment_date": "2024-01-15",
    "status": "draft",
    "pdf_filename": "test.pdf",
}

MOCK_SUMMARY = {
    "executive_summary": "Test summary",
    "recommendations": "Test recommendations",
}


class TestExportEndpoints:
    @patch("api.core.report_html.generate_html_report")
    @patch("api.routers.export.db")
    def test_export_html(self, mock_db, mock_gen, client, auth_headers):
        mock_db.get_sehra.return_value = MOCK_SEHRA
        mock_db.get_component_analyses.return_value = []
        mock_db.get_executive_summary.return_value = MOCK_SUMMARY
        mock_gen.return_value = "<html>Test</html>"

        res = client.get(
            "/api/v1/export/test-id-1234/html",
            headers=auth_headers,
        )
        assert res.status_code == 200
        assert "text/html" in res.headers["content-type"]

    @patch("api.routers.export.db")
    def test_export_not_found(self, mock_db, client, auth_headers):
        mock_db.get_sehra.return_value = None
        res = client.get(
            "/api/v1/export/nonexistent/html",
            headers=auth_headers,
        )
        assert res.status_code == 404
