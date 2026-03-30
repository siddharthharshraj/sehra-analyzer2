"""Adversarial and edge case tests for robustness."""
import json
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).parent.parent

# Import from api/core which has the newer validation/calibration functions
sys.path.insert(0, str(PROJECT_ROOT / "api"))
import importlib
for mod_name in list(sys.modules):
    if mod_name.startswith("core."):
        del sys.modules[mod_name]
if "core" in sys.modules:
    del sys.modules["core"]

from core.ai_engine import (
    _parse_llm_json, _validate_response, _calibrate_confidence,
    _validate_and_fix_themes, _sanitize_remark, analyze_component,
    ComponentAnalysisResponse,
)
from core.codebook import (
    score_item, build_scoring_lookup, load_codebook,
    get_component_from_item_id, score_all_items,
)
from core.pdf_parser import pair_checkboxes


class TestLLMOutputAdversarial:
    """Test handling of unexpected/malformed LLM outputs."""

    def test_llm_returns_extra_fields(self):
        """LLM returns fields not in schema - they're ignored."""
        raw = {
            "classifications": [
                {"remark_index": 1, "theme": "Funding",
                 "classification": "enabler", "confidence": 0.9,
                 "extra_field": "should be ignored",
                 "another_extra": 42}
            ],
            "enabler_summary": [],
            "barrier_summary": [],
            "completely_unknown_key": "value",
        }
        result = _validate_response(raw)
        assert isinstance(result, ComponentAnalysisResponse)
        assert len(result.classifications) == 1
        assert result.classifications[0].theme == "Funding"

    def test_llm_returns_confidence_above_1(self):
        """Confidence > 1.0 is clamped to 1.0 before Pydantic validation."""
        raw = {
            "classifications": [
                {"remark_index": 1, "theme": "Funding",
                 "classification": "enabler", "confidence": 1.5}
            ],
            "enabler_summary": [],
            "barrier_summary": [],
        }
        result = _validate_response(raw)
        assert len(result.classifications) == 1
        assert result.classifications[0].confidence <= 1.0

    def test_llm_returns_negative_confidence(self):
        """Negative confidence is clamped to 0.0 before Pydantic validation."""
        raw = {
            "classifications": [
                {"remark_index": 1, "theme": "Funding",
                 "classification": "enabler", "confidence": -0.5}
            ],
            "enabler_summary": [],
            "barrier_summary": [],
        }
        result = _validate_response(raw)
        assert len(result.classifications) == 1
        assert result.classifications[0].confidence >= 0.0

    def test_llm_returns_empty_classifications(self):
        """Empty classifications list is handled gracefully."""
        raw = {
            "classifications": [],
            "enabler_summary": [],
            "barrier_summary": [],
        }
        result = _validate_response(raw)
        assert isinstance(result, ComponentAnalysisResponse)
        assert len(result.classifications) == 0

    def test_llm_returns_invalid_json(self):
        """Invalid JSON triggers graceful fallback."""
        result = _parse_llm_json("This is not JSON at all, just plain text.")
        assert isinstance(result, dict)
        assert "classifications" in result or "error" in result

    def test_llm_returns_classification_not_in_enum(self):
        """Classification like 'neutral' (not enabler/barrier) is handled."""
        raw = {
            "classifications": [
                {"remark_index": 1, "theme": "Funding",
                 "classification": "neutral", "confidence": 0.7}
            ],
            "enabler_summary": [],
            "barrier_summary": [],
        }
        result = _validate_response(raw)
        assert isinstance(result, ComponentAnalysisResponse)
        assert result.classifications[0].classification == "neutral"

    def test_llm_returns_nested_markdown_fences(self):
        """Response with nested markdown code fences is parsed correctly."""
        text = '```json\n```json\n{"classifications": [], "enabler_summary": [], "barrier_summary": []}\n```\n```'
        result = _parse_llm_json(text)
        assert isinstance(result, dict)

    def test_llm_returns_json_with_trailing_text(self):
        """JSON followed by extra text (LLM commentary) is parsed correctly."""
        text = '{"classifications": [{"theme": "Funding"}], "enabler_summary": [], "barrier_summary": []}\n\nI hope this analysis is helpful!'
        result = _parse_llm_json(text)
        assert "classifications" in result

    def test_llm_returns_json_with_leading_text(self):
        """Text followed by JSON is extracted correctly."""
        text = 'Here is my analysis:\n{"classifications": [{"theme": "Funding"}], "enabler_summary": [], "barrier_summary": []}'
        result = _parse_llm_json(text)
        assert "classifications" in result

    def test_missing_required_fields_in_classification(self):
        """Classification with missing required fields gets defaults."""
        raw = {
            "classifications": [
                {"theme": "Funding"}
            ],
            "enabler_summary": [],
            "barrier_summary": [],
        }
        result = _validate_response(raw)
        assert len(result.classifications) == 1
        assert result.classifications[0].remark_index == 0
        assert result.classifications[0].confidence == 0.0


class TestPDFEdgeCases:
    """Test PDF parsing edge cases."""

    def test_pdf_with_empty_checkboxes(self):
        """All checkboxes unchecked doesn't crash."""
        checkboxes = [
            {"name": "cb1", "checked": False, "rect": (100, 200, 120, 220)},
            {"name": "cb2", "checked": False, "rect": (150, 200, 170, 220)},
        ]
        pairs = pair_checkboxes(checkboxes)
        assert len(pairs) == 1
        assert pairs[0]["answer"] is None

    def test_pdf_with_unicode_text(self):
        """Unicode characters in remarks are handled correctly."""
        remark = "Programme d'ophtalmologie scolaire avec des resultats"
        sanitized = _sanitize_remark(remark)
        assert sanitized == remark.strip()

    def test_many_checkboxes_on_same_row(self):
        """8 checkboxes at same Y produces 4 pairs (grid table)."""
        checkboxes = [
            {"name": f"cb{i}", "checked": (i % 2 == 0),
             "rect": (100 + i * 40, 300, 120 + i * 40, 320)}
            for i in range(8)
        ]
        pairs = pair_checkboxes(checkboxes)
        assert len(pairs) == 4

    def test_checkboxes_at_different_y_positions(self):
        """Checkboxes at very different Y positions are separate pairs."""
        checkboxes = [
            {"name": "cb1", "checked": True, "rect": (100, 100, 120, 120)},
            {"name": "cb2", "checked": False, "rect": (150, 100, 170, 120)},
            {"name": "cb3", "checked": False, "rect": (100, 500, 120, 520)},
            {"name": "cb4", "checked": True, "rect": (150, 500, 170, 520)},
        ]
        pairs = pair_checkboxes(checkboxes)
        assert len(pairs) == 2
        assert pairs[0]["answer"] == "yes"
        assert pairs[1]["answer"] == "no"


class TestCodebookEdgeCases:
    """Test codebook scoring edge cases."""

    def test_item_with_unknown_id_prefix(self):
        """Item ID with unknown prefix (e.g., 'X1') returns 'unknown' component."""
        assert get_component_from_item_id("X1") == "unknown"
        assert get_component_from_item_id("Z99") == "unknown"

    def test_score_item_with_none_answer(self, codebook):
        """None answer returns None score."""
        lookup = build_scoring_lookup(codebook)
        item_id = list(lookup.keys())[0]
        result = score_item(item_id, None, lookup)
        assert result is None

    def test_score_item_with_empty_string(self, codebook):
        """Empty string answer scores as 'no'."""
        lookup = build_scoring_lookup(codebook)
        item_id = list(lookup.keys())[0]
        result = score_item(item_id, "", lookup)
        assert result is not None
        assert result["score"] in (0, 1)

    def test_reverse_scored_item_correct(self, codebook):
        """Reverse-scored item: Yes=barrier (0), No=enabler (1)."""
        lookup = build_scoring_lookup(codebook)
        reverse_items = [k for k, v in lookup.items() if v["is_reverse"]]
        if not reverse_items:
            pytest.skip("No reverse-scored items in codebook")
        item_id = reverse_items[0]
        yes_result = score_item(item_id, "yes", lookup)
        no_result = score_item(item_id, "no", lookup)
        assert yes_result["classification"] == "barrier"
        assert no_result["classification"] == "enabler"

    def test_all_codebook_items_have_valid_component(self, codebook):
        """Every scoring item in codebook maps to a known component."""
        valid_components = {"context", "policy", "service_delivery",
                            "human_resources", "supply_chain", "barriers",
                            "summary", "unknown"}
        for item in codebook["items"]:
            if item["has_scoring"]:
                comp = get_component_from_item_id(item["id"])
                assert comp in valid_components, \
                    f"Item {item['id']} maps to unexpected component '{comp}'"
                assert comp != "unknown", \
                    f"Scoring item {item['id']} maps to 'unknown' component"

    def test_score_item_with_boolean_true(self, codebook):
        """Boolean True answer is treated as 'yes'."""
        lookup = build_scoring_lookup(codebook)
        for item_id, rules in lookup.items():
            if not rules["is_reverse"]:
                result = score_item(item_id, True, lookup)
                assert result["classification"] == "enabler"
                break

    def test_score_item_with_boolean_false(self, codebook):
        """Boolean False answer is treated as 'no'."""
        lookup = build_scoring_lookup(codebook)
        for item_id, rules in lookup.items():
            if not rules["is_reverse"]:
                result = score_item(item_id, False, lookup)
                assert result["classification"] == "barrier"
                break

    def test_score_all_items_with_empty_list(self):
        """Scoring an empty list returns empty results without error."""
        results = score_all_items([])
        assert results["totals"]["enabler_count"] == 0
        assert results["totals"]["barrier_count"] == 0
        assert len(results["by_component"]) == 0

    def test_score_item_case_insensitive_answer(self, codebook):
        """Answers like 'YES', 'Yes', 'yes' all score the same."""
        lookup = build_scoring_lookup(codebook)
        item_id = list(lookup.keys())[0]
        r1 = score_item(item_id, "yes", lookup)
        r2 = score_item(item_id, "YES", lookup)
        r3 = score_item(item_id, "Yes", lookup)
        assert r1["score"] == r2["score"] == r3["score"]
        assert r1["classification"] == r2["classification"] == r3["classification"]


class TestDatabaseEdgeCases:
    """Test database operation edge cases."""

    def test_save_sehra_with_special_chars_in_country(self, db_session):
        """Country names with special characters are handled."""
        import uuid
        from core.db import SEHRA

        sehra = SEHRA(
            id=str(uuid.uuid4()),
            country="Cote d'Ivoire",
            pdf_filename="test.pdf",
        )
        db_session.add(sehra)
        db_session.commit()

        found = db_session.query(SEHRA).filter(SEHRA.id == sehra.id).first()
        assert found.country == "Cote d'Ivoire"

    def test_list_sehras_empty_database(self, db_session):
        """Empty database returns empty list, not error."""
        from core.db import SEHRA
        sehras = db_session.query(SEHRA).all()
        assert sehras == []

    def test_sehra_default_status(self, db_session):
        """New SEHRA has default status 'draft'."""
        import uuid
        from core.db import SEHRA

        sehra = SEHRA(
            id=str(uuid.uuid4()),
            country="TestCountry",
            pdf_filename="test.pdf",
        )
        db_session.add(sehra)
        db_session.commit()

        found = db_session.query(SEHRA).filter(SEHRA.id == sehra.id).first()
        assert found.status == "draft"

    def test_component_analysis_cascade_delete(self, db_session):
        """Deleting SEHRA cascades to component analyses."""
        import uuid
        from core.db import SEHRA, ComponentAnalysis

        sehra_id = str(uuid.uuid4())
        sehra = SEHRA(id=sehra_id, country="Test", pdf_filename="test.pdf")
        db_session.add(sehra)
        db_session.flush()

        ca = ComponentAnalysis(
            id=str(uuid.uuid4()),
            sehra_id=sehra_id,
            component="context",
            enabler_count=5,
            barrier_count=3,
        )
        db_session.add(ca)
        db_session.commit()

        db_session.delete(sehra)
        db_session.commit()

        remaining = db_session.query(ComponentAnalysis).filter(
            ComponentAnalysis.sehra_id == sehra_id
        ).all()
        assert len(remaining) == 0

    def test_qualitative_entry_fields(self, db_session):
        """QualitativeEntry stores all fields correctly."""
        import uuid
        from core.db import SEHRA, ComponentAnalysis, QualitativeEntry

        sehra_id = str(uuid.uuid4())
        sehra = SEHRA(id=sehra_id, country="Test", pdf_filename="t.pdf")
        db_session.add(sehra)
        db_session.flush()

        ca_id = str(uuid.uuid4())
        ca = ComponentAnalysis(id=ca_id, sehra_id=sehra_id, component="policy")
        db_session.add(ca)
        db_session.flush()

        qe = QualitativeEntry(
            id=str(uuid.uuid4()),
            component_analysis_id=ca_id,
            remark_text="Test remark with details.",
            item_id="S1",
            theme="Funding",
            classification="enabler",
            confidence=0.92,
            edited_by_human=False,
        )
        db_session.add(qe)
        db_session.commit()

        found = db_session.query(QualitativeEntry).filter(
            QualitativeEntry.component_analysis_id == ca_id
        ).first()
        assert found.remark_text == "Test remark with details."
        assert found.theme == "Funding"
        assert found.classification == "enabler"
        assert found.confidence == 0.92
        assert found.edited_by_human is False
