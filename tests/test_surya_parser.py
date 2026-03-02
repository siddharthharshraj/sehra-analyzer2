"""Tests for Surya OCR parser module."""

import pytest
import numpy as np
from PIL import Image
from unittest.mock import patch, MagicMock

from core.surya_parser import (
    is_surya_available,
    _detect_checkbox_state,
    _clean_question_text,
    _extract_field_value,
    _bbox_in_regions,
)

# Check if surya is installed for conditional test skipping
surya_available = is_surya_available()


class TestIsSuryaAvailable:
    """Tests for is_surya_available()."""

    def test_returns_bool(self):
        result = is_surya_available()
        assert isinstance(result, bool)

    def test_returns_false_when_not_installed(self):
        with patch.dict("sys.modules", {"surya": None}):
            # When surya import raises ImportError
            with patch("builtins.__import__", side_effect=ImportError):
                assert is_surya_available() is False


class TestDetectCheckboxState:
    """Tests for _detect_checkbox_state() with synthetic images."""

    def test_empty_checkbox(self):
        """A mostly white image (empty checkbox) should return 'empty'."""
        img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        # Draw a thin border (just a few dark pixels at edges)
        pixels = np.array(img)
        pixels[0, :] = [0, 0, 0]   # top border
        pixels[-1, :] = [0, 0, 0]  # bottom border
        pixels[:, 0] = [0, 0, 0]   # left border
        pixels[:, -1] = [0, 0, 0]  # right border
        img = Image.fromarray(pixels)

        state = _detect_checkbox_state(img, (0, 0, 100, 100))
        assert state == "empty"

    def test_checked_checkbox(self):
        """An image with significant dark pixels (marked checkbox) should return 'checked'."""
        # Create image with >15% dark pixels (simulating a bold tick/cross mark)
        pixels = np.full((100, 100, 3), 255, dtype=np.uint8)
        # Fill a solid block in the center to simulate a heavy mark
        pixels[20:80, 20:80] = [0, 0, 0]
        img = Image.fromarray(pixels)

        state = _detect_checkbox_state(img, (0, 0, 100, 100))
        assert state == "checked"

    def test_zero_size_bbox(self):
        """Zero-size bounding box should return None."""
        img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        state = _detect_checkbox_state(img, (50, 50, 50, 50))
        assert state is None

    def test_negative_size_bbox(self):
        """Negative-size bounding box should return None."""
        img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        state = _detect_checkbox_state(img, (80, 80, 20, 20))
        assert state is None


class TestCleanQuestionText:
    """Tests for _clean_question_text()."""

    def test_collapses_whitespace(self):
        assert _clean_question_text("hello   world") == "hello world"

    def test_strips_leading_numbers(self):
        assert _clean_question_text("1. Are there any programmes") == "Are there any programmes"
        assert _clean_question_text("12) Some question") == "Some question"

    def test_strips_trailing_punctuation(self):
        assert _clean_question_text("Some question:") == "Some question"
        assert _clean_question_text("Some question...") == "Some question"

    def test_preserves_normal_text(self):
        text = "Are there any standalone school eye health programmes"
        assert _clean_question_text(text) == text


class TestExtractFieldValue:
    """Tests for _extract_field_value()."""

    def test_colon_separated(self):
        lines = [{"text": "Country: Liberia", "bbox": (0, 0, 100, 20)}]
        result = _extract_field_value("Country: Liberia", "country", lines, 0)
        assert result == "Liberia"

    def test_label_only_uses_next_line(self):
        lines = [
            {"text": "Country:", "bbox": (0, 0, 100, 20)},
            {"text": "Liberia", "bbox": (0, 25, 100, 45)},
        ]
        result = _extract_field_value("Country:", "country", lines, 0)
        assert result == "Liberia"

    def test_no_value_found(self):
        lines = [{"text": "Country:", "bbox": (0, 0, 100, 20)}]
        result = _extract_field_value("Country:", "country", lines, 0)
        assert result == ""


class TestBboxInRegions:
    """Tests for _bbox_in_regions()."""

    def test_fully_inside(self):
        bbox = (20, 20, 80, 80)
        regions = [(0, 0, 100, 100)]
        assert _bbox_in_regions(bbox, regions) is True

    def test_fully_outside(self):
        bbox = (200, 200, 300, 300)
        regions = [(0, 0, 100, 100)]
        assert _bbox_in_regions(bbox, regions) is False

    def test_partial_overlap_below_threshold(self):
        bbox = (80, 80, 150, 150)
        regions = [(0, 0, 100, 100)]
        # Intersection: (80,80)-(100,100) = 20x20 = 400
        # bbox area: 70x70 = 4900
        # Overlap ratio: 400/4900 ~ 0.08 < 0.5
        assert _bbox_in_regions(bbox, regions) is False

    def test_empty_regions(self):
        bbox = (20, 20, 80, 80)
        assert _bbox_in_regions(bbox, []) is False


@pytest.mark.skipif(not surya_available, reason="surya-ocr not installed")
class TestSuryaParseOutputStructure:
    """Tests that surya_parse_sehra() returns the expected output structure.

    These tests only run when Surya is installed.
    """

    def test_output_has_required_keys(self, liberia_pdf_path):
        """Output should match parse_sehra_pdf() structure."""
        from core.surya_parser import surya_parse_sehra
        result = surya_parse_sehra(liberia_pdf_path)

        assert "header" in result
        assert "full_text" in result
        assert "components" in result

        header = result["header"]
        assert "country" in header
        assert "district" in header
        assert "province" in header
        assert "assessment_date" in header

    def test_components_have_required_keys(self, liberia_pdf_path):
        """Each component should have items, text_field_values, text."""
        from core.surya_parser import surya_parse_sehra
        result = surya_parse_sehra(liberia_pdf_path)

        for comp_name, comp_data in result["components"].items():
            assert "items" in comp_data, f"{comp_name} missing 'items'"
            assert "text_field_values" in comp_data, f"{comp_name} missing 'text_field_values'"
            assert "text" in comp_data, f"{comp_name} missing 'text'"

    def test_items_have_required_keys(self, liberia_pdf_path):
        """Each item should have question, answer, page_num, remark."""
        from core.surya_parser import surya_parse_sehra
        result = surya_parse_sehra(liberia_pdf_path)

        for comp_name, comp_data in result["components"].items():
            for item in comp_data["items"]:
                assert "question" in item, f"Item in {comp_name} missing 'question'"
                assert "answer" in item, f"Item in {comp_name} missing 'answer'"
                assert "page_num" in item, f"Item in {comp_name} missing 'page_num'"
                assert "remark" in item, f"Item in {comp_name} missing 'remark'"
