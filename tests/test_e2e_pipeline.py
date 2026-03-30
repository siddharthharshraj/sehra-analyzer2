"""End-to-end pipeline tests covering full analysis workflow."""
import json
import sys
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Import from api/core which has the newer multi-country functions
sys.path.insert(0, str(PROJECT_ROOT / "api"))
import importlib
for mod_name in list(sys.modules):
    if mod_name.startswith("core."):
        del sys.modules[mod_name]
if "core" in sys.modules:
    del sys.modules["core"]

from core.codebook import (
    load_codebook, build_scoring_lookup, score_all_items,
    score_item, get_component_from_item_id, LIBERIA_EXPECTED,
)
import core.ai_engine as ai_engine_mod
from core.ai_engine import (
    analyze_component, analyze_full_sehra, _validate_and_fix_themes,
    _calibrate_confidence, _load_themes, build_system_prompt,
    _load_keyword_patterns, _build_few_shot_messages,
)


def _make_mock_llm_response(num_remarks=1):
    """Helper to build a valid mock LLM JSON response."""
    themes = _load_themes()
    theme_name = themes[0]["name"]
    classifications = []
    for i in range(num_remarks):
        classifications.append({
            "remark_index": i + 1,
            "item_id": f"S{i + 1}",
            "remark_text": f"Test remark number {i + 1} for analysis.",
            "theme": theme_name,
            "classification": "enabler" if i % 2 == 0 else "barrier",
            "confidence": 0.85 + (i * 0.02),
        })
    return json.dumps({
        "classifications": classifications,
        "enabler_summary": [
            {
                "themes": [theme_name],
                "summary": "Summary of enablers found in the assessment.",
                "action_points": ["Strengthen programme governance"],
            }
        ] if any(c["classification"] == "enabler" for c in classifications) else [],
        "barrier_summary": [
            {
                "themes": [theme_name],
                "summary": "Summary of barriers found in the assessment.",
                "action_points": ["Address identified gaps"],
            }
        ] if any(c["classification"] == "barrier" for c in classifications) else [],
    })


class TestFullPipeline:
    """Test complete analysis pipeline: parse -> score -> analyze -> report."""

    def test_score_and_analyze_mock_data(self, sample_parsed_data, mock_llm_response):
        """Full pipeline with mock parsed data and mocked LLM."""
        all_items = []
        for comp_name, comp_data in sample_parsed_data["components"].items():
            for item in comp_data.get("items", []):
                all_items.append({**item, "component": comp_name})

        scores = score_all_items(all_items)
        assert "by_component" in scores
        assert "totals" in scores

        with patch("core.ai_engine._call_llm", return_value=mock_llm_response):
            ai_results = analyze_full_sehra(sample_parsed_data)

        assert isinstance(ai_results, dict)
        assert "context" in ai_results or "policy" in ai_results

    def test_generic_country_pipeline(self, sample_parsed_data, mock_llm_response):
        """Pipeline works with default/generic country config."""
        sample_parsed_data["header"]["country"] = "GenericLand"

        all_items = []
        for comp_name, comp_data in sample_parsed_data["components"].items():
            for item in comp_data.get("items", []):
                all_items.append({**item, "component": comp_name})

        scores = score_all_items(all_items)
        assert scores["totals"]["enabler_count"] >= 0
        assert scores["totals"]["barrier_count"] >= 0

    def test_pipeline_with_all_enablers(self):
        """Pipeline handles assessment where all items are enablers."""
        codebook = load_codebook()
        lookup = build_scoring_lookup(codebook)

        items = []
        for item_id, rules in list(lookup.items())[:10]:
            if not rules["is_reverse"]:
                items.append({
                    "item_id": item_id,
                    "question": rules["question"],
                    "answer": "yes",
                    "remark": "",
                    "component": get_component_from_item_id(item_id),
                })

        results = score_all_items(items)
        assert results["totals"]["barrier_count"] == 0
        assert results["totals"]["enabler_count"] == len(items)

    def test_pipeline_with_all_barriers(self):
        """Pipeline handles assessment where all items are barriers."""
        codebook = load_codebook()
        lookup = build_scoring_lookup(codebook)

        items = []
        for item_id, rules in list(lookup.items())[:10]:
            if not rules["is_reverse"]:
                items.append({
                    "item_id": item_id,
                    "question": rules["question"],
                    "answer": "no",
                    "remark": "",
                    "component": get_component_from_item_id(item_id),
                })

        results = score_all_items(items)
        assert results["totals"]["enabler_count"] == 0
        assert results["totals"]["barrier_count"] == len(items)

    def test_pipeline_with_no_remarks(self):
        """Pipeline handles assessment with no qualitative remarks."""
        parsed_data = {
            "header": {"country": "TestCountry", "district": "TestDistrict"},
            "components": {
                "policy": {
                    "items": [
                        {"item_id": "S1", "question": "Test", "answer": "yes",
                         "remark": "", "component": "policy"},
                    ],
                    "text": "",
                },
            },
        }

        with patch("core.ai_engine._call_llm") as mock_llm:
            ai_results = analyze_full_sehra(parsed_data)
            mock_llm.assert_not_called()

        assert ai_results["policy"]["classifications"] == []

    def test_pipeline_with_mixed_scoring(self):
        """Pipeline correctly handles mix of standard and reverse-scored items."""
        codebook = load_codebook()
        lookup = build_scoring_lookup(codebook)

        standard_items = [(k, v) for k, v in lookup.items() if not v["is_reverse"]]
        reverse_items = [(k, v) for k, v in lookup.items() if v["is_reverse"]]

        items = []
        for item_id, rules in standard_items[:5]:
            items.append({
                "item_id": item_id, "question": rules["question"],
                "answer": "yes", "remark": "",
                "component": get_component_from_item_id(item_id),
            })
        for item_id, rules in reverse_items[:3]:
            items.append({
                "item_id": item_id, "question": rules["question"],
                "answer": "yes", "remark": "",
                "component": get_component_from_item_id(item_id),
            })

        results = score_all_items(items)
        assert results["totals"]["enabler_count"] == 5
        assert results["totals"]["barrier_count"] == len(reverse_items[:3])


class TestCountrySpecificPipeline:
    """Test that country-specific data flows through entire pipeline."""

    def test_country_codebook_used_in_scoring(self):
        """Scoring uses the main codebook."""
        codebook = load_codebook()
        assert "items" in codebook
        assert len(codebook["items"]) > 100

    def test_country_patterns_used_in_ai(self):
        """AI analysis uses keyword patterns for prompt construction."""
        themes = _load_themes()
        patterns = _load_keyword_patterns()
        prompt = build_system_prompt("policy", patterns, themes, country="liberia")
        assert "Sectoral Legislation" in prompt
        assert len(prompt) > 500

    def test_country_examples_used_in_prompts(self):
        """Few-shot examples are available for prompts."""
        msgs = _build_few_shot_messages("context")
        assert isinstance(msgs, list)
        if msgs:
            assert msgs[0]["role"] == "user"
            assert msgs[1]["role"] == "assistant"

    def test_country_in_report_output(self, sample_component_analyses):
        """Generated reports include correct country name."""
        from core.report_gen import generate_report
        header = {"country": "Liberia", "district": "Montserrado",
                  "assessment_date": "2024-05-17"}
        sehra_data = {"id": "test-id", "country": "Liberia"}

        buf = generate_report(sehra_data, sample_component_analyses, header)
        from docx import Document
        buf.seek(0)
        doc = Document(buf)
        full_text = "\n".join(p.text for p in doc.paragraphs)
        assert "Liberia" in full_text


class TestDataIntegrity:
    """Test data integrity through the pipeline."""

    def test_no_items_lost_in_scoring(self):
        """Every item passed to score_all_items appears in results."""
        items = [
            {"item_id": "O10", "answer": "yes", "component": "context",
             "question": "Test", "remark": ""},
            {"item_id": "S1", "answer": "no", "component": "policy",
             "question": "Test", "remark": ""},
            {"item_id": "UNKNOWN99", "answer": "yes", "component": "context",
             "question": "Unknown", "remark": ""},
        ]
        results = score_all_items(items)
        total_items = sum(
            len(comp["items"])
            for comp in results["by_component"].values()
        )
        assert total_items == len(items)

    def test_all_remarks_classified(self, mock_llm_response):
        """Every remark sent to LLM gets a classification in response."""
        items = [
            {"item_id": "S1", "question": "Test question",
             "answer": "yes",
             "remark": "School health is included in the National Education Policy."},
        ]
        with patch.object(ai_engine_mod, "_call_llm", return_value=mock_llm_response):
            result = analyze_component("policy", items)
        assert len(result["classifications"]) >= 1

    def test_enabler_barrier_counts_consistent(self):
        """Sum of enablers + barriers matches total scored items."""
        items = [
            {"item_id": "O10", "answer": "yes", "component": "context",
             "question": "Test", "remark": ""},
            {"item_id": "S1", "answer": "no", "component": "policy",
             "question": "Test", "remark": ""},
        ]
        results = score_all_items(items)
        total_from_components = sum(
            comp["enabler_count"] + comp["barrier_count"]
            for comp in results["by_component"].values()
        )
        total_from_totals = (results["totals"]["enabler_count"] +
                             results["totals"]["barrier_count"])
        assert total_from_components == total_from_totals

    def test_confidence_scores_in_valid_range(self):
        """All confidence scores from calibration are between 0.0 and 1.0."""
        entries = [
            {"remark_text": "Short", "confidence": 0.99, "theme_validated": True},
            {"remark_text": "A" * 300, "confidence": 0.01, "theme_validated": False},
            {"remark_text": "Medium length remark for testing.", "confidence": 0.5,
             "theme_validated": True},
        ]
        result = _calibrate_confidence(entries, "policy")
        for entry in result:
            assert 0.0 <= entry["confidence"] <= 1.0, \
                f"Confidence {entry['confidence']} out of range"

    def test_theme_validation_preserves_all_entries(self):
        """Theme validation doesn't drop any entries."""
        themes = _load_themes()
        theme_names = [t["name"] for t in themes]
        entries = [
            {"theme": "Funding", "confidence": 0.9},
            {"theme": "Invalid Theme", "confidence": 0.8},
            {"theme": "", "confidence": 0.7},
        ]
        result = _validate_and_fix_themes(entries, theme_names)
        assert len(result) == len(entries)

    def test_scoring_results_structure(self):
        """score_all_items returns correctly structured results."""
        items = [
            {"item_id": "O10", "answer": "yes", "component": "context",
             "question": "Test question", "remark": "Some remark"},
        ]
        results = score_all_items(items)
        assert "by_component" in results
        assert "totals" in results
        assert "enabler_count" in results["totals"]
        assert "barrier_count" in results["totals"]

        for comp_name, comp_data in results["by_component"].items():
            assert "enabler_count" in comp_data
            assert "barrier_count" in comp_data
            assert "items" in comp_data
            for item in comp_data["items"]:
                assert "item_id" in item
                assert "question" in item
                assert "component" in item
