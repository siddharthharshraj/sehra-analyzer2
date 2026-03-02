"""Integration tests for the full SEHRA analysis pipeline."""

import json
import pytest
from unittest.mock import patch, MagicMock


class TestFullPipeline:
    """Test the full pipeline: parse -> score -> mock AI -> generate report."""

    def test_pipeline_with_liberia(self, liberia_pdf_path, mock_llm_response):
        """Run full pipeline with Liberia PDF and mocked AI."""
        from core.pdf_parser import parse_and_enrich
        from core.codebook import score_all_items

        # Step 1: Parse
        parsed = parse_and_enrich(liberia_pdf_path)
        assert parsed["header"]["country"] == "Liberia"
        assert len(parsed["components"]) >= 6

        # Step 2: Score
        all_items = []
        for comp_name, comp_data in parsed["components"].items():
            for item in comp_data.get("items", []):
                all_items.append({**item, "component": comp_name})

        scores = score_all_items(all_items)
        assert scores["totals"]["enabler_count"] > 0
        assert scores["totals"]["barrier_count"] > 0

        # Step 3: Mock AI analysis
        with patch("core.ai_engine._call_llm") as mock_llm:
            mock_llm.return_value = mock_llm_response

            from core.ai_engine import analyze_full_sehra
            ai_results = analyze_full_sehra(parsed)

            assert isinstance(ai_results, dict)

        # Step 4: Generate DOCX report
        from core.report_gen import generate_report

        component_analyses = []
        for comp in scores["by_component"]:
            comp_scores = scores["by_component"][comp]
            ai_comp = ai_results.get(comp, {})
            component_analyses.append({
                "id": f"test-{comp}",
                "component": comp,
                "enabler_count": comp_scores["enabler_count"],
                "barrier_count": comp_scores["barrier_count"],
                "items": comp_scores["items"],
                "qualitative_entries": [
                    {
                        "id": f"qe-{i}",
                        "remark_text": c.get("remark_text", ""),
                        "item_id": c.get("item_id", ""),
                        "theme": c.get("theme", "Other"),
                        "classification": c.get("classification", "enabler"),
                        "confidence": c.get("confidence", 0.5),
                        "edited_by_human": False,
                    }
                    for i, c in enumerate(ai_comp.get("classifications", []))
                ],
                "report_sections": {},
            })

        header = {
            "country": parsed["header"]["country"],
            "district": parsed["header"]["district"],
            "assessment_date": parsed["header"].get("assessment_date", ""),
        }

        docx_buf = generate_report({}, component_analyses, header)
        assert docx_buf.getvalue()[:2] == b'PK'  # Valid DOCX

        # Step 5: Generate HTML report
        from core.report_html import generate_html_report

        html = generate_html_report(component_analyses, header)
        assert "<html" in html
        assert "Liberia" in html

    def test_pipeline_scoring_consistency(self, liberia_pdf_path):
        """Test that scoring produces consistent results."""
        from core.pdf_parser import parse_and_enrich
        from core.codebook import score_all_items, LIBERIA_EXPECTED

        parsed = parse_and_enrich(liberia_pdf_path)
        all_items = []
        for comp_name, comp_data in parsed["components"].items():
            for item in comp_data.get("items", []):
                all_items.append({**item, "component": comp_name})

        scores1 = score_all_items(all_items)
        scores2 = score_all_items(all_items)

        assert scores1["totals"] == scores2["totals"]

    def test_codebook_coverage(self, codebook):
        """Test that the codebook covers all expected sections."""
        sections = set(item["section"] for item in codebook["items"])
        expected = {"context", "policy", "service_delivery",
                    "human_resources", "supply_chain", "barriers"}
        assert expected.issubset(sections)

    def test_themes_coverage(self, themes):
        """Test that all 11 themes are defined."""
        assert len(themes) == 11
        theme_names = [t["name"] for t in themes]
        assert "Funding" in theme_names
        assert "Institutional Structure and Stakeholders" in theme_names
