"""Tests for theme validation, confidence calibration, and input sanitization."""
import json
import logging
import sys
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Import from api/core which has the newer multi-country/validation functions
sys.path.insert(0, str(PROJECT_ROOT / "api"))
import importlib
for mod_name in list(sys.modules):
    if mod_name.startswith("core."):
        del sys.modules[mod_name]
if "core" in sys.modules:
    del sys.modules["core"]

import core.ai_engine as ai_engine_module
from core.ai_engine import (
    _validate_and_fix_themes, _calibrate_confidence, _sanitize_remark,
    _load_themes, analyze_component,
)


@pytest.fixture
def all_theme_names():
    """Load all 11 valid theme names from themes.json."""
    themes = _load_themes()
    return [t["name"] for t in themes]


class TestThemeValidation:
    """Test theme name validation against themes.json."""

    def test_exact_theme_match(self, all_theme_names):
        """Exact theme names pass validation unchanged."""
        entries = [
            {"theme": "Funding", "confidence": 0.9},
            {"theme": "Institutional Structure and Stakeholders", "confidence": 0.85},
        ]
        result = _validate_and_fix_themes(entries, all_theme_names)
        assert result[0]["theme"] == "Funding"
        assert result[0]["theme_validated"] is True
        assert result[1]["theme"] == "Institutional Structure and Stakeholders"
        assert result[1]["theme_validated"] is True

    def test_case_insensitive_match(self, all_theme_names):
        """Theme matching is case-insensitive."""
        entries = [
            {"theme": "funding", "confidence": 0.9},
            {"theme": "FUNDING", "confidence": 0.85},
            {"theme": "FuNdInG", "confidence": 0.8},
        ]
        result = _validate_and_fix_themes(entries, all_theme_names)
        for entry in result:
            assert entry["theme"] == "Funding"
            assert entry["theme_validated"] is True

    def test_fuzzy_match_close_theme(self, all_theme_names):
        """Close misspellings are fuzzy-matched to correct theme."""
        entries = [
            {"theme": "Institutional Structure & Stakeholders", "confidence": 0.9},
        ]
        result = _validate_and_fix_themes(entries, all_theme_names)
        assert result[0]["theme"] == "Institutional Structure and Stakeholders"
        assert result[0]["theme_validated"] is True
        assert result[0].get("theme_fuzzy_matched") is True

    def test_fuzzy_match_logs_warning(self, all_theme_names, caplog):
        """Fuzzy-matched themes generate a warning log."""
        entries = [
            {"theme": "Institutional Structure & Stakeholders", "confidence": 0.9},
        ]
        with caplog.at_level(logging.WARNING, logger="sehra.ai_engine"):
            _validate_and_fix_themes(entries, all_theme_names)
        assert any("fuzzy-matched" in record.message.lower() or
                    "Theme fuzzy-matched" in record.message
                    for record in caplog.records)

    def test_completely_invalid_theme_gets_low_confidence(self, all_theme_names):
        """Unrecognized themes get confidence capped at 0.4."""
        entries = [
            {"theme": "Totally Made Up Theme XYZ123", "confidence": 0.95},
        ]
        result = _validate_and_fix_themes(entries, all_theme_names)
        assert result[0]["theme_validated"] is False
        assert result[0]["confidence"] <= 0.4

    def test_all_11_themes_are_valid(self, all_theme_names):
        """All 11 defined themes pass validation."""
        assert len(all_theme_names) == 11
        entries = [{"theme": t, "confidence": 0.9} for t in all_theme_names]
        result = _validate_and_fix_themes(entries, all_theme_names)
        for entry in result:
            assert entry["theme_validated"] is True

    def test_empty_theme_handled(self, all_theme_names):
        """Empty/null theme string doesn't crash."""
        entries = [{"theme": "", "confidence": 0.5}]
        result = _validate_and_fix_themes(entries, all_theme_names)
        assert len(result) == 1
        assert result[0]["theme_validated"] is False

    def test_theme_with_extra_whitespace(self, all_theme_names):
        """Themes with leading/trailing whitespace are trimmed."""
        entries = [{"theme": "  Funding  ", "confidence": 0.9}]
        result = _validate_and_fix_themes(entries, all_theme_names)
        assert result[0]["theme"] == "Funding"
        assert result[0]["theme_validated"] is True

    def test_theme_names_completeness(self, all_theme_names):
        """Verify the expected 11 themes are all present."""
        expected = {
            "Institutional Structure and Stakeholders",
            "Operationalization Strategies",
            "Coordination and Integration",
            "Funding",
            "Local Capacity and Service Delivery",
            "Accessibility and Inclusivity",
            "Cost, Availability and Affordability",
            "Data Considerations",
            "Sociocultural Factors and Compliance",
            "Services at Higher Levels of Health System",
            "Procuring Eyeglasses",
        }
        assert set(all_theme_names) == expected


class TestConfidenceCalibration:
    """Test confidence score post-processing."""

    def test_short_remark_reduces_confidence(self):
        """Remarks < 20 chars get confidence reduced by 0.2."""
        entries = [
            {"remark_text": "Short remark", "confidence": 0.9, "theme_validated": True},
        ]
        result = _calibrate_confidence(entries, "policy")
        assert result[0]["confidence"] < 0.9
        assert abs(result[0]["confidence"] - 0.7) < 0.01

    def test_long_remark_boosts_confidence(self):
        """Remarks > 200 chars get slight confidence boost."""
        long_remark = "A" * 250
        entries = [
            {"remark_text": long_remark, "confidence": 0.85, "theme_validated": True},
        ]
        result = _calibrate_confidence(entries, "context")
        assert abs(result[0]["confidence"] - 0.9) < 0.01

    def test_unvalidated_theme_caps_confidence(self):
        """Entries with theme_validated=False get confidence capped at 0.4."""
        entries = [
            {"remark_text": "A decent length remark for testing purposes here.",
             "confidence": 0.95, "theme_validated": False},
        ]
        result = _calibrate_confidence(entries, "policy")
        assert result[0]["confidence"] <= 0.4

    def test_confidence_clamped_0_to_1(self):
        """Confidence is always in [0.0, 1.0] range."""
        entries = [
            {"remark_text": "X", "confidence": 0.05, "theme_validated": True},
        ]
        result = _calibrate_confidence(entries, "policy")
        assert 0.0 <= result[0]["confidence"] <= 1.0

        entries2 = [
            {"remark_text": "A" * 300, "confidence": 0.99, "theme_validated": True},
        ]
        result2 = _calibrate_confidence(entries2, "context")
        assert 0.0 <= result2[0]["confidence"] <= 1.0

    def test_confidence_rounded_to_3_decimals(self):
        """Confidence scores are rounded to 3 decimal places."""
        entries = [
            {"remark_text": "A moderate length remark here.", "confidence": 0.87654321,
             "theme_validated": True},
        ]
        result = _calibrate_confidence(entries, "policy")
        conf_str = str(result[0]["confidence"])
        if "." in conf_str:
            decimals = conf_str.split(".")[1]
            assert len(decimals) <= 3

    def test_normal_remark_unchanged_confidence(self):
        """Remark between 20-200 chars with validated theme keeps confidence."""
        entries = [
            {"remark_text": "This is a normal length remark with enough content.",
             "confidence": 0.88, "theme_validated": True},
        ]
        result = _calibrate_confidence(entries, "context")
        assert result[0]["confidence"] == 0.88


class TestInputSanitization:
    """Test remark sanitization for prompt injection prevention."""

    def test_normal_remark_unchanged(self):
        """Normal text passes through unchanged."""
        text = "The school health programme is operational in 5 districts."
        assert _sanitize_remark(text) == text

    def test_control_characters_removed(self):
        """Control characters (except newline/tab) are stripped."""
        text = "Hello\x00World\x01Test\nNew line\tTab"
        result = _sanitize_remark(text)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "\n" in result
        assert "\t" in result

    def test_very_long_remark_truncated(self):
        """Remarks > 2000 chars are truncated with ellipsis."""
        long_text = "A" * 3000
        result = _sanitize_remark(long_text)
        assert len(result) == 2003  # 2000 + "..."
        assert result.endswith("...")

    def test_empty_remark_returns_empty(self):
        """Empty/None remarks return empty string."""
        assert _sanitize_remark("") == ""
        assert _sanitize_remark(None) == ""

    def test_whitespace_only_remark(self):
        """Whitespace-only remarks are handled gracefully."""
        result = _sanitize_remark("   \t  \n  ")
        assert isinstance(result, str)

    def test_remark_with_json_characters(self):
        """Remarks with {, }, [, ] don't break anything."""
        text = 'The response was {"status": "ok"} with [data].'
        result = _sanitize_remark(text)
        assert "{" in result
        assert "}" in result

    def test_remark_exactly_2000_chars(self):
        """Remarks of exactly 2000 chars are not truncated."""
        text = "B" * 2000
        result = _sanitize_remark(text)
        assert len(result) == 2000
        assert not result.endswith("...")

    def test_leading_trailing_whitespace_stripped(self):
        """Leading and trailing whitespace is stripped."""
        text = "   Some remark text   "
        result = _sanitize_remark(text)
        assert result == "Some remark text"


class TestFilteredRemarks:
    """Test that short/empty remarks are filtered from analysis."""

    def test_remark_under_5_chars_filtered(self):
        """Remarks <= 5 chars are filtered from analysis in analyze_component."""
        from unittest.mock import patch

        items = [
            {"item_id": "S1", "question": "Test question", "answer": "yes", "remark": "No"},
            {"item_id": "S2", "question": "Test question 2", "answer": "yes", "remark": "X"},
        ]
        with patch.object(ai_engine_module, "_call_llm") as mock_llm:
            result = analyze_component("policy", items)
            mock_llm.assert_not_called()
            assert result["classifications"] == []

    def test_remark_exactly_6_chars_included(self):
        """Remarks of exactly 6 chars are included in analysis (not filtered)."""
        from unittest.mock import patch, MagicMock

        items = [
            {"item_id": "S1", "question": "Test", "answer": "yes", "remark": "AB CDE"},
        ]
        mock_response = json.dumps({
            "classifications": [
                {"remark_index": 1, "theme": "Funding", "classification": "enabler",
                 "confidence": 0.8}
            ],
            "enabler_summary": [],
            "barrier_summary": [],
        })
        with patch.object(ai_engine_module, "_call_llm", return_value=mock_response) as mock_llm, \
             patch.object(ai_engine_module, "_get_provider", return_value=MagicMock()):
            result = analyze_component("policy", items)
            mock_llm.assert_called_once()

    def test_empty_remark_filtered(self):
        """Empty remarks are filtered from LLM analysis."""
        from unittest.mock import patch

        items = [
            {"item_id": "S1", "question": "Test", "answer": "yes", "remark": ""},
            {"item_id": "S2", "question": "Test 2", "answer": "no", "remark": "  "},
        ]
        with patch.object(ai_engine_module, "_call_llm") as mock_llm:
            result = analyze_component("policy", items)
            mock_llm.assert_not_called()
            assert result["classifications"] == []
