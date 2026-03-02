"""Tests for PDF parser module."""

import pytest
from core.pdf_parser import (
    extract_header_from_form_fields,
    pair_checkboxes,
    extract_items_widget_first,
    match_items_to_codebook,
    parse_sehra_pdf,
    parse_and_enrich,
    COMPONENT_PAGE_RANGES,
)
from core.exceptions import PDFParsingError


class TestPairCheckboxes:
    """Tests for checkbox pairing logic."""

    def test_pair_two_checkboxes(self):
        checkboxes = [
            {"name": "cb1", "checked": True, "rect": (100, 200, 120, 220)},
            {"name": "cb2", "checked": False, "rect": (150, 200, 170, 220)},
        ]
        pairs = pair_checkboxes(checkboxes)
        assert len(pairs) == 1
        assert pairs[0]["yes_checked"] is True
        assert pairs[0]["no_checked"] is False
        assert pairs[0]["answer"] == "yes"

    def test_pair_no_answer(self):
        checkboxes = [
            {"name": "cb1", "checked": False, "rect": (100, 200, 120, 220)},
            {"name": "cb2", "checked": True, "rect": (150, 200, 170, 220)},
        ]
        pairs = pair_checkboxes(checkboxes)
        assert len(pairs) == 1
        assert pairs[0]["answer"] == "no"

    def test_pair_empty(self):
        assert pair_checkboxes([]) == []

    def test_pair_single_checkbox(self):
        checkboxes = [
            {"name": "cb1", "checked": True, "rect": (100, 200, 120, 220)},
        ]
        pairs = pair_checkboxes(checkboxes)
        assert len(pairs) == 1
        assert pairs[0]["answer"] == "yes"

    def test_pair_multiple_rows(self):
        checkboxes = [
            {"name": "cb1", "checked": True, "rect": (100, 100, 120, 120)},
            {"name": "cb2", "checked": False, "rect": (150, 100, 170, 120)},
            {"name": "cb3", "checked": False, "rect": (100, 200, 120, 220)},
            {"name": "cb4", "checked": True, "rect": (150, 200, 170, 220)},
        ]
        pairs = pair_checkboxes(checkboxes)
        assert len(pairs) == 2

    def test_pair_six_checkboxes_grid_row(self):
        """6 checkboxes at same Y should produce 3 pairs (grid table)."""
        checkboxes = [
            {"name": "cb1", "checked": True, "rect": (253, 364, 270, 380)},
            {"name": "cb2", "checked": False, "rect": (291, 364, 308, 380)},
            {"name": "cb3", "checked": True, "rect": (330, 364, 347, 380)},
            {"name": "cb4", "checked": False, "rect": (368, 364, 385, 380)},
            {"name": "cb5", "checked": True, "rect": (407, 364, 424, 380)},
            {"name": "cb6", "checked": False, "rect": (446, 364, 463, 380)},
        ]
        pairs = pair_checkboxes(checkboxes)
        assert len(pairs) == 3
        assert pairs[0]["answer"] == "yes"
        assert pairs[0]["x"] == 253
        assert pairs[1]["answer"] == "yes"
        assert pairs[1]["x"] == 330
        assert pairs[2]["answer"] == "yes"
        assert pairs[2]["x"] == 407

    def test_pair_four_checkboxes_grid_row(self):
        """4 checkboxes at same Y should produce 2 pairs."""
        checkboxes = [
            {"name": "cb1", "checked": True, "rect": (251, 285, 268, 302)},
            {"name": "cb2", "checked": False, "rect": (279, 285, 296, 302)},
            {"name": "cb3", "checked": True, "rect": (394, 285, 411, 302)},
            {"name": "cb4", "checked": False, "rect": (422, 285, 439, 302)},
        ]
        pairs = pair_checkboxes(checkboxes)
        assert len(pairs) == 2
        assert pairs[0]["answer"] == "yes"
        assert pairs[1]["answer"] == "yes"

    def test_pair_three_checkboxes_keeps_extra(self):
        """3 checkboxes should produce 1 pair + 1 extra (yes/no/does-not-exist)."""
        checkboxes = [
            {"name": "cb1", "checked": True, "rect": (252, 273, 270, 290)},
            {"name": "cb2", "checked": False, "rect": (279, 273, 297, 290)},
            {"name": "cb3", "checked": False, "rect": (383, 273, 401, 290)},
        ]
        pairs = pair_checkboxes(checkboxes)
        assert len(pairs) == 1
        assert pairs[0]["answer"] == "yes"
        assert len(pairs[0]["extra_checkboxes"]) == 1

    def test_pair_has_x_field(self):
        """All pairs should include an x field for column identification."""
        checkboxes = [
            {"name": "cb1", "checked": True, "rect": (100, 200, 120, 220)},
            {"name": "cb2", "checked": False, "rect": (150, 200, 170, 220)},
        ]
        pairs = pair_checkboxes(checkboxes)
        assert "x" in pairs[0]
        assert pairs[0]["x"] == 100


class TestMatchItemsToCodebook:
    """Tests for codebook matching."""

    def test_exact_match(self, codebook):
        items = [{"question": "Are there any standalone school eye health programmes or activities in the country?"}]
        matched = match_items_to_codebook(items, codebook["items"], "context")
        assert len(matched) == 1
        assert matched[0].get("item_id") != ""

    def test_partial_match(self, codebook):
        items = [{"question": "Are there standalone school eye health programmes"}]
        matched = match_items_to_codebook(items, codebook["items"], "context")
        assert len(matched) == 1

    def test_short_label_match(self, codebook):
        """Short grid labels should match via substring check."""
        items = [{"question": "School nurse level"}]
        matched = match_items_to_codebook(items, codebook["items"], "context")
        assert len(matched) == 1

    def test_no_match(self, codebook):
        items = [{"question": "zzzzz xxxxx qqqqq jjjjj"}]
        matched = match_items_to_codebook(items, codebook["items"], "context")
        assert len(matched) == 1
        assert matched[0].get("item_id") == ""


class TestParseAndEnrich:
    """Tests for full parsing (requires sample PDF)."""

    def test_parse_liberia(self, liberia_pdf_path):
        """Test full parsing of Liberia PDF."""
        result = parse_and_enrich(liberia_pdf_path)

        assert "header" in result
        assert result["header"]["country"] == "Liberia"
        assert "components" in result
        assert len(result["components"]) >= 6

        # Check all expected components exist
        for comp in ["context", "policy", "service_delivery",
                     "human_resources", "supply_chain", "barriers"]:
            assert comp in result["components"]

    def test_header_extraction(self, liberia_pdf_path):
        """Test header extraction from Liberia PDF."""
        import fitz
        doc = fitz.open(liberia_pdf_path)
        header = extract_header_from_form_fields(doc)
        doc.close()

        assert header["country"] == "Liberia"

    def test_component_page_ranges(self):
        """Test that page ranges are properly defined."""
        assert len(COMPONENT_PAGE_RANGES) >= 6
        for comp, (start, end) in COMPONENT_PAGE_RANGES.items():
            assert start < end
            assert start >= 1

    def test_widget_first_extracts_grid_items(self, liberia_pdf_path):
        """Widget-first extraction should capture grid table items."""
        import fitz
        doc = fitz.open(liberia_pdf_path)
        # Supply chain pages 31-35 have grid tables
        items = extract_items_widget_first(doc, (31, 35))
        doc.close()

        # Should extract significantly more than the old approach
        # Grid pages alone should have 15+ items (optical products grid)
        assert len(items) >= 15
