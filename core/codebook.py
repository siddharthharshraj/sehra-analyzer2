"""Codebook scoring engine for SEHRA quantitative analysis.

Scores each yes/no item as enabler (1) or barrier (0) using deterministic rules.
Handles standard scoring (yes=enabler) and reverse scoring (yes=barrier).
"""

import json
import logging
import os
from pathlib import Path

from core.exceptions import ScoringError

logger = logging.getLogger("sehra.codebook")

DATA_DIR = Path(__file__).parent.parent / "data"

# Component display names
COMPONENT_NAMES = {
    "context": "Context",
    "policy": "Sectoral Legislation, Policy and Strategy",
    "service_delivery": "Institutional and Service Delivery Environment",
    "human_resources": "Human Resources",
    "supply_chain": "Supply Chain",
    "barriers": "Barriers",
    "summary": "Summary",
}

# Component short codes (item_id prefixes -> component)
ITEM_PREFIX_TO_COMPONENT = {
    "O": "context",
    "S": "policy",
    "I": "service_delivery",
    "H": "human_resources",
    "C": "supply_chain",
    "B": "barriers",
    "M": "summary",
}


def load_codebook(country: str = "default") -> dict:
    """Load codebook: DB override first (country-specific), then country file, then default file."""
    country_key = country.lower().strip() if country else "default"

    # Try DB-backed codebook (persists admin edits across deploys)
    try:
        from core.db import get_codebook_override
        override = get_codebook_override(country_key)
        if override:
            logger.info("Codebook loaded from DB for %s: %d items", country_key, len(override.get("items", [])))
            return override
    except Exception:
        pass  # DB not available, fall back to file

    # Try country-specific file
    country_path = DATA_DIR / "countries" / country_key / "codebook.json"
    if country_path.exists():
        try:
            with open(country_path) as f:
                data = json.load(f)
            logger.info("Codebook loaded from country file (%s): %d items", country_key, len(data.get("items", [])))
            return data
        except Exception as e:
            logger.warning("Failed to load country codebook for %s: %s", country_key, e)

    # Fall back to default codebook
    default_path = DATA_DIR / "codebook.json"
    try:
        with open(default_path) as f:
            data = json.load(f)
        logger.info("Codebook loaded from default file: %d items", len(data.get("items", [])))
        return data
    except Exception as e:
        raise ScoringError(f"Failed to load codebook: {e}") from e


def get_component_from_item_id(item_id: str) -> str:
    """Determine component from item ID prefix (O=context, S=policy, etc.)."""
    if not item_id:
        return "unknown"
    prefix = item_id[0].upper()
    return ITEM_PREFIX_TO_COMPONENT.get(prefix, "unknown")


def build_scoring_lookup(codebook: dict) -> dict:
    """Build a lookup dict: item_id -> {is_reverse, score_yes, score_no, question, section}."""
    lookup = {}
    for item in codebook["items"]:
        if item["has_scoring"]:
            lookup[item["id"]] = {
                "is_reverse": item["is_reverse"],
                "score_yes": item["score_yes"],
                "score_no": item["score_no"],
                "question": item["question"],
                "section": item["section"],
            }
    return lookup


def score_item(item_id: str, answer: str | bool | None, scoring_lookup: dict) -> dict | None:
    """Score a single item.

    Args:
        item_id: The item identifier (e.g., "O10", "S1", "B5")
        answer: "yes", "no", True, False, or None
        scoring_lookup: From build_scoring_lookup()

    Returns:
        {score: 0|1, classification: "enabler"|"barrier", is_reverse: bool} or None if not scorable
    """
    if item_id not in scoring_lookup:
        return None

    rules = scoring_lookup[item_id]

    # Normalize answer
    if answer is None:
        return None
    if isinstance(answer, bool):
        is_yes = answer
    elif isinstance(answer, str):
        is_yes = answer.strip().lower() in ("yes", "y", "true", "1")
    else:
        return None

    score = rules["score_yes"] if is_yes else rules["score_no"]
    classification = "enabler" if score == 1 else "barrier"

    return {
        "score": score,
        "classification": classification,
        "is_reverse": rules["is_reverse"],
    }


def score_all_items(parsed_items: list[dict], country: str = "default") -> dict:
    """Score all items from parsed PDF data.

    Args:
        parsed_items: List of {item_id, question, answer, remark, component}
            where answer is "yes", "no", or None
        country: Country identifier for loading country-specific codebook

    Returns:
        {
            "by_component": {
                "context": {"enabler_count": 8, "barrier_count": 4, "items": [...]},
                "policy": {...},
                ...
            },
            "totals": {"enabler_count": 77, "barrier_count": 55}
        }
    """
    codebook = load_codebook(country=country)
    scoring_lookup = build_scoring_lookup(codebook)

    by_component = {}
    total_enablers = 0
    total_barriers = 0

    for item in parsed_items:
        item_id = item.get("item_id", "")
        answer = item.get("answer")
        component = item.get("component") or get_component_from_item_id(item_id)

        if component not in by_component:
            by_component[component] = {
                "enabler_count": 0,
                "barrier_count": 0,
                "items": [],
            }

        result = score_item(item_id, answer, scoring_lookup)

        scored_item = {
            "item_id": item_id,
            "question": item.get("question", ""),
            "answer": answer,
            "remark": item.get("remark", ""),
            "component": component,
        }

        if result:
            scored_item["score"] = result["score"]
            scored_item["classification"] = result["classification"]
            scored_item["is_reverse"] = result["is_reverse"]

            if result["classification"] == "enabler":
                by_component[component]["enabler_count"] += 1
                total_enablers += 1
            else:
                by_component[component]["barrier_count"] += 1
                total_barriers += 1
        else:
            scored_item["score"] = None
            scored_item["classification"] = None
            scored_item["is_reverse"] = False

        by_component[component]["items"].append(scored_item)

    logger.info(
        "Scoring complete: %d enablers, %d barriers across %d components",
        total_enablers, total_barriers, len(by_component),
    )
    return {
        "by_component": by_component,
        "totals": {
            "enabler_count": total_enablers,
            "barrier_count": total_barriers,
        },
    }


def load_keyword_patterns(country: str = "default") -> dict:
    """Load keyword patterns: country-specific first, then default."""
    country_key = country.lower().strip() if country else "default"

    country_path = DATA_DIR / "countries" / country_key / "keyword_patterns.json"
    if country_path.exists():
        try:
            with open(country_path) as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to load keyword patterns for %s: %s", country_key, e)

    default_path = DATA_DIR / "keyword_patterns.json"
    if default_path.exists():
        try:
            with open(default_path) as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to load default keyword patterns: %s", e)
    return {}


def load_few_shot_examples(country: str = "default") -> dict:
    """Load few-shot examples: country-specific first, then default."""
    country_key = country.lower().strip() if country else "default"

    country_path = DATA_DIR / "countries" / country_key / "few_shot_examples.json"
    if country_path.exists():
        try:
            with open(country_path) as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to load few-shot examples for %s: %s", country_key, e)

    default_path = DATA_DIR / "few_shot_examples.json"
    if default_path.exists():
        try:
            with open(default_path) as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to load default few-shot examples: %s", e)
    return {}


def load_knowledge_base(country: str = "default") -> dict:
    """Load SEHRA knowledge base: country-specific first, then default."""
    country_key = country.lower().strip() if country else "default"

    country_path = DATA_DIR / "countries" / country_key / "knowledge.json"
    if country_path.exists():
        try:
            with open(country_path) as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to load knowledge base for %s: %s", country_key, e)

    default_path = DATA_DIR / "sehra_knowledge.json"
    if default_path.exists():
        try:
            with open(default_path) as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to load default knowledge base: %s", e)
    return {}


def load_expected_counts(country: str) -> dict | None:
    """Load expected counts for validation (if available for country)."""
    country_key = country.lower().strip() if country else ""
    if not country_key:
        return None
    path = DATA_DIR / "countries" / country_key / "expected_counts.json"
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to load expected counts for %s: %s", country_key, e)
    return None


# Backward-compatible alias: load from Liberia expected_counts.json
def _load_liberia_expected() -> dict:
    """Load Liberia expected counts for backward compatibility."""
    counts = load_expected_counts("liberia")
    if counts:
        return counts
    # Hardcoded fallback if file not found
    return {
        "context": {"enablers": 8, "barriers": 4},
        "policy": {"enablers": 17, "barriers": 3},
        "service_delivery": {"enablers": 13, "barriers": 2},
        "human_resources": {"enablers": 2, "barriers": 3},
        "supply_chain": {"enablers": 27, "barriers": 5},
        "barriers": {"enablers": 10, "barriers": 38},
    }

# Keep as module-level variable for backward compatibility with tests
LIBERIA_EXPECTED = _load_liberia_expected()
