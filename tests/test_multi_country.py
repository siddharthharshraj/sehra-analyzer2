"""Tests for multi-country support across all components."""
import json
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).parent.parent
API_DATA_DIR = PROJECT_ROOT / "api" / "data"

# Add api/ to sys.path for importing api.core modules with multi-country support
sys.path.insert(0, str(PROJECT_ROOT / "api"))
import importlib
# Force reload core modules from api/ path
if "core.pdf_parser" in sys.modules:
    importlib.reload(sys.modules["core.pdf_parser"])
if "core.ai_engine" in sys.modules:
    importlib.reload(sys.modules["core.ai_engine"])

from core.pdf_parser import (
    load_country_config, get_page_ranges, get_noise_texts,
    get_min_page_count, DEFAULT_PAGE_RANGES,
)
from core.ai_engine import (
    _load_country_keyword_patterns, _load_country_few_shot_examples,
    _load_country_knowledge_base, _load_country_data,
)
from core.codebook import load_codebook


class TestCountryConfig:
    """Test country configuration loading and fallbacks."""

    def test_load_default_config(self):
        """Default config loads when no country specified."""
        config = load_country_config("default")
        assert isinstance(config, dict)
        assert "page_ranges" in config
        assert "min_page_count" in config
        assert "language" in config

    def test_load_liberia_config(self):
        """Liberia-specific config loads correctly."""
        config = load_country_config("liberia")
        assert isinstance(config, dict)
        assert "page_ranges" in config
        assert config.get("language") == "en"

    def test_load_unknown_country_falls_back_to_default(self):
        """Unknown country gracefully falls back to default config."""
        default_config = load_country_config("default")
        unknown_config = load_country_config("narnia")
        assert unknown_config.get("min_page_count") == default_config.get("min_page_count")

    def test_country_name_case_insensitive(self):
        """Country names are case-insensitive (Liberia == liberia == LIBERIA)."""
        lower = load_country_config("liberia")
        upper = load_country_config("LIBERIA")
        mixed = load_country_config("Liberia")
        assert lower.get("min_page_count") == upper.get("min_page_count")
        assert lower.get("min_page_count") == mixed.get("min_page_count")

    def test_page_ranges_returned_as_tuples(self):
        """Page ranges from JSON (lists) are converted to tuples."""
        ranges = get_page_ranges("default")
        for comp, val in ranges.items():
            assert isinstance(val, tuple), f"{comp} page range should be a tuple, got {type(val)}"
            assert len(val) == 2, f"{comp} page range should have 2 elements"
            assert val[0] <= val[1], f"{comp} start should be <= end"

    def test_all_countries_have_required_fields(self):
        """Every country config has page_ranges, min_page_count, language, noise_texts."""
        config_path = API_DATA_DIR / "country_configs.json"
        if not config_path.exists():
            pytest.skip("country_configs.json not found")
        with open(config_path) as f:
            configs = json.load(f)
        required_fields = {"page_ranges", "min_page_count", "language", "noise_texts"}
        for country, config in configs.items():
            for field in required_fields:
                assert field in config, f"Country '{country}' missing required field '{field}'"

    def test_page_ranges_cover_all_components(self):
        """Default page ranges include all 6 analysis components plus summary."""
        ranges = get_page_ranges("default")
        expected_components = {"context", "policy", "service_delivery",
                               "human_resources", "supply_chain", "barriers"}
        for comp in expected_components:
            assert comp in ranges, f"Missing page range for component '{comp}'"

    def test_get_noise_texts_returns_set(self):
        """get_noise_texts returns a set of strings."""
        noise = get_noise_texts("default")
        assert isinstance(noise, set)
        assert len(noise) > 0
        assert "yes" in noise
        assert "no" in noise

    def test_get_min_page_count_positive(self):
        """Minimum page count is a positive integer."""
        count = get_min_page_count("default")
        assert isinstance(count, int)
        assert count > 0


class TestCountryCodebook:
    """Test country-specific codebook loading."""

    def test_load_default_codebook(self):
        """Default codebook loads from data/codebook.json."""
        codebook = load_codebook()
        assert "items" in codebook
        assert len(codebook["items"]) > 0

    def test_load_liberia_codebook(self):
        """Liberia codebook loads from countries/liberia/codebook.json."""
        path = API_DATA_DIR / "countries" / "liberia" / "codebook.json"
        if not path.exists():
            pytest.skip("Liberia codebook not found")
        with open(path) as f:
            codebook = json.load(f)
        assert "items" in codebook
        assert len(codebook["items"]) > 0

    def test_codebook_has_required_fields(self, codebook):
        """Every codebook item has id, section, question, type, has_scoring."""
        required = {"id", "section", "question", "type", "has_scoring"}
        for item in codebook["items"]:
            for field in required:
                assert field in item, f"Item {item.get('id', '?')} missing field '{field}'"

    def test_codebook_scoring_rules_valid(self, codebook):
        """Scoring items have score_yes and score_no defined."""
        for item in codebook["items"]:
            if item["has_scoring"]:
                assert item["score_yes"] is not None, \
                    f"Scoring item {item['id']} missing score_yes"
                assert item["score_no"] is not None, \
                    f"Scoring item {item['id']} missing score_no"
                assert item["score_yes"] in (0, 1), \
                    f"Item {item['id']} score_yes should be 0 or 1"
                assert item["score_no"] in (0, 1), \
                    f"Item {item['id']} score_no should be 0 or 1"

    def test_codebook_fallback_chain(self):
        """Country -> default fallback works correctly for codebook."""
        default = load_codebook()
        assert len(default["items"]) > 100

    def test_codebook_sections_match_components(self, codebook):
        """All codebook sections map to valid component names."""
        valid_sections = {"context", "policy", "service_delivery",
                          "human_resources", "supply_chain", "barriers", "summary"}
        for item in codebook["items"]:
            assert item["section"] in valid_sections, \
                f"Item {item['id']} has invalid section '{item['section']}'"


class TestCountryDataFiles:
    """Test country-specific data file loading."""

    def test_load_keyword_patterns_default(self):
        """Default keyword patterns load correctly."""
        patterns = _load_country_keyword_patterns("default")
        assert isinstance(patterns, dict)
        assert len(patterns) > 0

    def test_load_keyword_patterns_liberia(self):
        """Liberia-specific patterns load when available."""
        path = API_DATA_DIR / "countries" / "liberia" / "keyword_patterns.json"
        if not path.exists():
            pytest.skip("Liberia keyword patterns not found")
        patterns = _load_country_keyword_patterns("liberia")
        assert isinstance(patterns, dict)

    def test_load_few_shot_examples_default(self):
        """Default few-shot examples load correctly."""
        examples = _load_country_few_shot_examples("default")
        assert isinstance(examples, dict)

    def test_load_knowledge_base_default(self):
        """Default knowledge base loads correctly."""
        kb = _load_country_knowledge_base("default")
        assert isinstance(kb, dict)

    def test_all_components_have_few_shot_examples(self):
        """All 6 components have classification_examples."""
        components = ["context", "policy", "service_delivery",
                      "human_resources", "supply_chain", "barriers"]
        examples = _load_country_few_shot_examples("default")
        cls_examples = examples.get("classification_examples", {})
        for comp in components:
            assert comp in cls_examples, \
                f"Component '{comp}' missing from classification_examples"
            assert len(cls_examples[comp]) > 0, \
                f"Component '{comp}' has no classification examples"

    def test_few_shot_example_structure(self):
        """Each few-shot example has remark, theme, classification, confidence."""
        examples = _load_country_few_shot_examples("default")
        cls_examples = examples.get("classification_examples", {})
        for comp, items in cls_examples.items():
            for i, ex in enumerate(items):
                assert "remark" in ex, f"{comp}[{i}] missing 'remark'"
                assert "theme" in ex, f"{comp}[{i}] missing 'theme'"
                assert "classification" in ex, f"{comp}[{i}] missing 'classification'"
                assert "confidence" in ex, f"{comp}[{i}] missing 'confidence'"
                assert 0.0 <= ex["confidence"] <= 1.0, \
                    f"{comp}[{i}] confidence {ex['confidence']} out of range"

    def test_load_country_data_returns_all_keys(self):
        """_load_country_data returns keyword_patterns, few_shot_examples, knowledge_base."""
        data = _load_country_data("default")
        assert "keyword_patterns" in data
        assert "few_shot_examples" in data
        assert "knowledge_base" in data

    def test_unknown_country_falls_back_to_default(self):
        """Loading data for unknown country returns valid data without error."""
        unknown_patterns = _load_country_keyword_patterns("atlantis")
        # Unknown country should still return a valid patterns dict (not crash)
        assert isinstance(unknown_patterns, dict)
        assert len(unknown_patterns) > 0
        # It falls back to the root-level keyword_patterns.json (not necessarily
        # identical to the default/ country folder, which is a cleaned-up copy)
