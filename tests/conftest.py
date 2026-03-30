"""Pytest fixtures for SEHRA Analyzer tests."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure the project root is on sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "data"
API_DATA_DIR = PROJECT_ROOT / "api" / "data"
SAMPLE_DIR = PROJECT_ROOT / "sample_data"


@pytest.fixture
def codebook():
    """Load the codebook data."""
    with open(DATA_DIR / "codebook.json") as f:
        return json.load(f)


@pytest.fixture
def themes():
    """Load the themes data."""
    with open(DATA_DIR / "themes.json") as f:
        return json.load(f)["themes"]


@pytest.fixture
def keyword_patterns():
    """Load keyword patterns."""
    with open(DATA_DIR / "keyword_patterns.json") as f:
        return json.load(f)


@pytest.fixture
def liberia_pdf_path():
    """Path to Liberia sample PDF (if available)."""
    path = SAMPLE_DIR / "SEHRA_Scoping_Module_Liberia FINAL.pdf"
    if path.exists():
        return str(path)
    pytest.skip("Liberia PDF not available in sample_data/")


@pytest.fixture
def db_session():
    """SQLite in-memory database session for testing."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from core.db import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for AI engine tests."""
    return json.dumps({
        "classifications": [
            {
                "remark_index": 1,
                "item_id": "S1",
                "remark_text": "Test remark",
                "theme": "Institutional Structure and Stakeholders",
                "classification": "enabler",
                "confidence": 0.9,
            }
        ],
        "enabler_summary": [
            {
                "themes": ["Institutional Structure and Stakeholders"],
                "summary": "Test summary of enablers.",
                "action_points": ["Action point 1"],
            }
        ],
        "barrier_summary": [],
    })


@pytest.fixture
def sample_parsed_data():
    """Sample parsed data structure for testing."""
    return {
        "header": {
            "country": "Liberia",
            "district": "Montserrado",
            "province": "",
            "assessment_date": "2024-05-17",
        },
        "full_text": "Sample full text...",
        "components": {
            "context": {
                "items": [
                    {
                        "question": "Are there any standalone school eye health programmes?",
                        "answer": "yes",
                        "remark": "SHIP programme is operational in intervention areas.",
                        "item_id": "O10",
                        "component": "context",
                    }
                ],
                "text": "Context section text...",
            },
            "policy": {
                "items": [
                    {
                        "question": "Is school health included in the National Education Policy?",
                        "answer": "yes",
                        "remark": "School health is included in the National Education Policy.",
                        "item_id": "S1",
                        "component": "policy",
                    }
                ],
                "text": "Policy section text...",
            },
            "service_delivery": {"items": [], "text": ""},
            "human_resources": {"items": [], "text": ""},
            "supply_chain": {"items": [], "text": ""},
            "barriers": {"items": [], "text": ""},
        },
    }


@pytest.fixture
def sample_component_analyses():
    """Sample component analyses as returned from DB."""
    return [
        {
            "id": "ca-1",
            "component": "context",
            "enabler_count": 8,
            "barrier_count": 4,
            "items": [],
            "qualitative_entries": [
                {
                    "id": "qe-1",
                    "remark_text": "SHIP programme is operational",
                    "item_id": "O10",
                    "theme": "Institutional Structure and Stakeholders",
                    "classification": "enabler",
                    "confidence": 0.9,
                    "edited_by_human": False,
                }
            ],
            "report_sections": {
                "enabler_summary": {
                    "id": "rs-1",
                    "content": "Strong institutional framework exists.",
                    "edited_by_human": False,
                },
            },
        },
        {
            "id": "ca-2",
            "component": "policy",
            "enabler_count": 17,
            "barrier_count": 3,
            "items": [],
            "qualitative_entries": [
                {
                    "id": "qe-2",
                    "remark_text": "School health is included in the National Education Policy.",
                    "item_id": "S1",
                    "theme": "Operationalization Strategies",
                    "classification": "enabler",
                    "confidence": 0.88,
                    "edited_by_human": False,
                }
            ],
            "report_sections": {},
        },
    ]


@pytest.fixture
def valid_themes():
    """List of all 11 valid SEHRA themes."""
    return [
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
    ]


@pytest.fixture
def liberia_country_config():
    """Liberia country configuration."""
    return {
        "page_ranges": {
            "context": (10, 15),
            "policy": (16, 20),
            "service_delivery": (21, 26),
            "human_resources": (27, 30),
            "supply_chain": (31, 35),
            "barriers": (36, 41),
            "summary": (42, 44),
        },
        "min_page_count": 40,
        "language": "en",
    }


@pytest.fixture
def full_sample_parsed_data():
    """Comprehensive parsed SEHRA data with all 6 components populated."""
    return {
        "header": {
            "country": "TestCountry",
            "district": "TestDistrict",
            "province": "TestProvince",
            "assessment_date": "2024-01-15",
        },
        "full_text": "Full sample text for testing...",
        "components": {
            "context": {
                "items": [
                    {
                        "question": "Are there any standalone school eye health programmes?",
                        "answer": "yes",
                        "remark": "A national programme exists since 2020 with government support.",
                        "item_id": "O10",
                        "component": "context",
                    },
                    {
                        "question": "Is there a national eye health plan?",
                        "answer": "no",
                        "remark": "No formal plan exists yet.",
                        "item_id": "O11",
                        "component": "context",
                    },
                ],
                "text": "Context section text...",
            },
            "policy": {
                "items": [
                    {
                        "question": "Is school health included in the National Education Policy?",
                        "answer": "yes",
                        "remark": "School health is included in the National Education Policy.",
                        "item_id": "S1",
                        "component": "policy",
                    },
                    {
                        "question": "Does the national health policy address school eye health?",
                        "answer": "no",
                        "remark": "The national health policy does not specifically mention school eye health.",
                        "item_id": "S2",
                        "component": "policy",
                    },
                ],
                "text": "Policy section text...",
            },
            "service_delivery": {
                "items": [
                    {
                        "question": "Are there school-based screening programmes?",
                        "answer": "yes",
                        "remark": "Screening is conducted by trained teachers annually.",
                        "item_id": "I1",
                        "component": "service_delivery",
                    },
                ],
                "text": "Service delivery section text...",
            },
            "human_resources": {
                "items": [
                    {
                        "question": "Are trained eye health professionals available?",
                        "answer": "no",
                        "remark": "Limited trained personnel available in rural areas.",
                        "item_id": "H1",
                        "component": "human_resources",
                    },
                ],
                "text": "Human resources section text...",
            },
            "supply_chain": {
                "items": [
                    {
                        "question": "Are spectacles available through public facilities?",
                        "answer": "yes",
                        "remark": "Basic spectacles are available at district hospitals.",
                        "item_id": "C1",
                        "component": "supply_chain",
                    },
                ],
                "text": "Supply chain section text...",
            },
            "barriers": {
                "items": [
                    {
                        "question": "Are there cultural barriers to wearing spectacles?",
                        "answer": "yes",
                        "remark": "Stigma exists around children wearing spectacles in some communities.",
                        "item_id": "B1",
                        "component": "barriers",
                    },
                ],
                "text": "Barriers section text...",
            },
        },
    }


@pytest.fixture
def multi_country_configs():
    """Configuration for testing multiple countries."""
    config_path = API_DATA_DIR / "country_configs.json"
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    return {"default": {"page_ranges": {}, "min_page_count": 40, "language": "en"}}
