"""Tests for AI engine module."""

import json
import pytest
from unittest.mock import patch, MagicMock

from core.ai_engine import (
    build_system_prompt, _parse_llm_json, _validate_response,
    analyze_component, _build_few_shot_messages,
    generate_executive_summary, generate_recommendations,
    ComponentAnalysisResponse,
)
from core.exceptions import AIAnalysisError


class TestBuildSystemPrompt:
    def test_contains_component(self, keyword_patterns, themes):
        prompt = build_system_prompt("policy", keyword_patterns, themes)
        assert "Sectoral Legislation" in prompt
        assert "SEHRA" in prompt

    def test_contains_themes(self, keyword_patterns, themes):
        prompt = build_system_prompt("context", keyword_patterns, themes)
        assert "Institutional Structure" in prompt
        assert "Funding" in prompt

    def test_contains_classification_rules(self, keyword_patterns, themes):
        prompt = build_system_prompt("barriers", keyword_patterns, themes)
        assert "enabler" in prompt.lower()
        assert "barrier" in prompt.lower()

    def test_all_components(self, keyword_patterns, themes):
        for comp in ["context", "policy", "service_delivery",
                     "human_resources", "supply_chain", "barriers"]:
            prompt = build_system_prompt(comp, keyword_patterns, themes)
            assert len(prompt) > 500


class TestParseLLMJson:
    def test_clean_json(self):
        data = {"classifications": [{"theme": "Funding"}]}
        result = _parse_llm_json(json.dumps(data))
        assert result["classifications"][0]["theme"] == "Funding"

    def test_markdown_fenced(self):
        text = "```json\n{\"classifications\": []}\n```"
        result = _parse_llm_json(text)
        assert result["classifications"] == []

    def test_partial_json(self):
        text = "Here is the analysis:\n{\"classifications\": [{\"theme\": \"Funding\"}]}"
        result = _parse_llm_json(text)
        assert len(result["classifications"]) == 1

    def test_invalid_json(self):
        result = _parse_llm_json("not json at all")
        assert "error" in result or result["classifications"] == []


class TestValidateResponse:
    def test_valid_response(self):
        raw = {
            "classifications": [
                {"remark_index": 1, "theme": "Funding", "classification": "enabler", "confidence": 0.9}
            ],
            "enabler_summary": [],
            "barrier_summary": [],
        }
        result = _validate_response(raw)
        assert isinstance(result, ComponentAnalysisResponse)
        assert len(result.classifications) == 1

    def test_empty_response(self):
        result = _validate_response({})
        assert isinstance(result, ComponentAnalysisResponse)
        assert len(result.classifications) == 0

    def test_partial_response(self):
        raw = {"classifications": [{"theme": "Funding"}]}
        result = _validate_response(raw)
        assert isinstance(result, ComponentAnalysisResponse)


class TestFewShotMessages:
    def test_returns_messages_for_known_component(self):
        msgs = _build_few_shot_messages("context")
        assert isinstance(msgs, list)
        if msgs:
            assert msgs[0]["role"] == "user"
            assert msgs[1]["role"] == "assistant"

    def test_returns_empty_for_unknown(self):
        msgs = _build_few_shot_messages("nonexistent_component")
        assert msgs == []


class TestAnalyzeComponent:
    @patch("core.ai_engine._call_llm")
    def test_basic_analysis(self, mock_llm, mock_llm_response):
        mock_llm.return_value = mock_llm_response

        items = [
            {
                "item_id": "S1",
                "question": "Test question",
                "answer": "yes",
                "remark": "School health is included in the National Education Policy.",
            }
        ]
        result = analyze_component("policy", items)

        assert "classifications" in result
        assert "enabler_summary" in result
        assert "barrier_summary" in result
        mock_llm.assert_called_once()

    @patch("core.ai_engine._call_llm")
    def test_empty_items(self, mock_llm):
        result = analyze_component("policy", [])
        assert result["classifications"] == []
        mock_llm.assert_not_called()

    @patch("core.ai_engine._call_llm")
    def test_no_remarks(self, mock_llm):
        items = [{"item_id": "S1", "question": "Test", "answer": "yes", "remark": ""}]
        result = analyze_component("policy", items)
        assert result["classifications"] == []
        mock_llm.assert_not_called()


class TestGenerateExecutiveSummary:
    @patch("core.ai_engine._call_llm")
    def test_generates_summary(self, mock_llm):
        mock_llm.return_value = "This is an executive summary."
        header = {"country": "Liberia", "district": "Montserrado"}
        all_results = {
            "policy": {
                "classifications": [
                    {"classification": "enabler", "theme": "Funding", "remark_text": "Budget allocated"}
                ]
            }
        }
        result = generate_executive_summary(all_results, header)
        assert "executive summary" in result.lower()


class TestGenerateRecommendations:
    @patch("core.ai_engine._call_llm")
    def test_generates_recommendations(self, mock_llm):
        mock_llm.return_value = "1. Address funding gaps.\n2. Strengthen coordination."
        header = {"country": "Liberia"}
        all_results = {
            "policy": {
                "classifications": [
                    {"classification": "barrier", "theme": "Funding", "remark_text": "Limited budget"}
                ]
            }
        }
        result = generate_recommendations(all_results, header)
        assert "1." in result
