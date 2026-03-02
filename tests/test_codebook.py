"""Tests for codebook scoring module."""

import pytest
from core.codebook import (
    load_codebook, build_scoring_lookup, score_item,
    score_all_items, get_component_from_item_id,
    LIBERIA_EXPECTED,
)
from core.exceptions import ScoringError


class TestLoadCodebook:
    def test_loads_successfully(self):
        codebook = load_codebook()
        assert "items" in codebook
        assert len(codebook["items"]) > 100

    def test_has_expected_fields(self):
        codebook = load_codebook()
        for item in codebook["items"][:5]:
            assert "id" in item
            assert "section" in item
            assert "question" in item


class TestScoringLookup:
    def test_build_lookup(self, codebook):
        lookup = build_scoring_lookup(codebook)
        assert len(lookup) > 0
        # Check a known scored item
        for item_id, rules in lookup.items():
            assert "is_reverse" in rules
            assert "score_yes" in rules
            assert "score_no" in rules
            break


class TestScoreItem:
    def test_standard_yes(self, codebook):
        lookup = build_scoring_lookup(codebook)
        # Find a standard (non-reverse) item
        for item_id, rules in lookup.items():
            if not rules["is_reverse"]:
                result = score_item(item_id, "yes", lookup)
                assert result is not None
                assert result["score"] == 1
                assert result["classification"] == "enabler"
                break

    def test_standard_no(self, codebook):
        lookup = build_scoring_lookup(codebook)
        for item_id, rules in lookup.items():
            if not rules["is_reverse"]:
                result = score_item(item_id, "no", lookup)
                assert result is not None
                assert result["score"] == 0
                assert result["classification"] == "barrier"
                break

    def test_reverse_yes(self, codebook):
        lookup = build_scoring_lookup(codebook)
        for item_id, rules in lookup.items():
            if rules["is_reverse"]:
                result = score_item(item_id, "yes", lookup)
                assert result is not None
                assert result["classification"] == "barrier"
                break

    def test_none_answer(self, codebook):
        lookup = build_scoring_lookup(codebook)
        item_id = list(lookup.keys())[0]
        result = score_item(item_id, None, lookup)
        assert result is None

    def test_unknown_item(self, codebook):
        lookup = build_scoring_lookup(codebook)
        result = score_item("UNKNOWN99", "yes", lookup)
        assert result is None

    def test_boolean_answer(self, codebook):
        lookup = build_scoring_lookup(codebook)
        item_id = list(lookup.keys())[0]
        result = score_item(item_id, True, lookup)
        assert result is not None


class TestGetComponentFromItemId:
    def test_known_prefixes(self):
        assert get_component_from_item_id("O10") == "context"
        assert get_component_from_item_id("S1") == "policy"
        assert get_component_from_item_id("I5") == "service_delivery"
        assert get_component_from_item_id("H3") == "human_resources"
        assert get_component_from_item_id("C12") == "supply_chain"
        assert get_component_from_item_id("B7") == "barriers"

    def test_unknown_prefix(self):
        assert get_component_from_item_id("X99") == "unknown"

    def test_empty(self):
        assert get_component_from_item_id("") == "unknown"


class TestScoreAllItems:
    def test_score_sample_items(self, codebook):
        """Test scoring with a small set of items."""
        items = [
            {"item_id": "O10", "answer": "yes", "component": "context", "question": "Test", "remark": ""},
            {"item_id": "S1", "answer": "yes", "component": "policy", "question": "Test", "remark": ""},
        ]
        results = score_all_items(items)
        assert "by_component" in results
        assert "totals" in results

    def test_liberia_validation(self, liberia_pdf_path):
        """Validate Liberia scoring matches expected counts (+/- 2 tolerance)."""
        from core.pdf_parser import parse_and_enrich

        parsed = parse_and_enrich(liberia_pdf_path)
        all_items = []
        for comp_name, comp_data in parsed["components"].items():
            for item in comp_data.get("items", []):
                all_items.append({**item, "component": comp_name})

        results = score_all_items(all_items)

        for comp, expected in LIBERIA_EXPECTED.items():
            actual = results["by_component"].get(comp, {})
            actual_enablers = actual.get("enabler_count", 0)
            actual_barriers = actual.get("barrier_count", 0)

            assert abs(actual_enablers - expected["enablers"]) <= 2, \
                f"{comp}: expected ~{expected['enablers']} enablers, got {actual_enablers}"
            assert abs(actual_barriers - expected["barriers"]) <= 2, \
                f"{comp}: expected ~{expected['barriers']} barriers, got {actual_barriers}"
