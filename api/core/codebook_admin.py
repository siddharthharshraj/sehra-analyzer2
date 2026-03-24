"""Admin operations for managing codebook.json questions.

Uses DB-backed storage so edits persist across deploys (ephemeral filesystems).
Falls back to the on-disk codebook.json as the baseline.
"""

import json
import logging
import time
import threading
from pathlib import Path

logger = logging.getLogger("sehra.codebook_admin")

CODEBOOK_PATH = Path(__file__).parent.parent / "data" / "codebook.json"

# In-memory codebook cache with TTL
_codebook_cache: dict | None = None
_codebook_cache_time: float = 0.0
_codebook_cache_lock = threading.Lock()
_CODEBOOK_CACHE_TTL = 30  # seconds


def load_codebook() -> dict:
    """Load codebook with TTL-based caching.

    Returns cached data if within TTL, otherwise reloads from
    DB override (preferred) or on-disk fallback.
    """
    global _codebook_cache, _codebook_cache_time

    now = time.time()
    if _codebook_cache is not None and (now - _codebook_cache_time) < _CODEBOOK_CACHE_TTL:
        return _codebook_cache

    with _codebook_cache_lock:
        # Double-check inside lock
        if _codebook_cache is not None and (time.time() - _codebook_cache_time) < _CODEBOOK_CACHE_TTL:
            return _codebook_cache

        data = _load_codebook_from_source()
        _codebook_cache = data
        _codebook_cache_time = time.time()
        return data


def _load_codebook_from_source() -> dict:
    """Load codebook from DB or disk (uncached)."""
    try:
        from core.db import get_codebook_override
        override = get_codebook_override()
        if override:
            return override
    except Exception:
        pass  # DB not available, fall back to file
    with open(CODEBOOK_PATH) as f:
        return json.load(f)


def invalidate_codebook_cache():
    """Clear the codebook cache (call after writes)."""
    global _codebook_cache, _codebook_cache_time
    with _codebook_cache_lock:
        _codebook_cache = None
        _codebook_cache_time = 0.0


def save_codebook(codebook: dict):
    """Save codebook to both DB (persistent) and disk (cache)."""
    # Always try DB first (survives redeploys)
    try:
        from core.db import save_codebook_override
        save_codebook_override(codebook)
    except Exception as e:
        logger.warning("Failed to save codebook to DB: %s", e)

    # Also write to disk (works for local dev, acts as cache)
    try:
        with open(CODEBOOK_PATH, "w") as f:
            json.dump(codebook, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning("Failed to save codebook to disk: %s", e)

    invalidate_codebook_cache()
    logger.info("Codebook saved: %d items", len(codebook.get("items", [])))


def get_sections() -> list[str]:
    """Get unique section names from codebook."""
    codebook = load_codebook()
    return sorted(set(item["section"] for item in codebook["items"]))


def get_items_by_section(section: str) -> list[dict]:
    """Get all items for a given section."""
    codebook = load_codebook()
    return [item for item in codebook["items"] if item["section"] == section]


def add_item(section: str, question: str, item_type: str,
             has_scoring: bool, is_reverse: bool, item_id: str = "") -> dict:
    """Add a new item to the codebook."""
    codebook = load_codebook()

    if not item_id:
        prefix_map = {
            "context": "O", "policy": "S", "service_delivery": "I",
            "human_resources": "H", "supply_chain": "C", "barriers": "B",
        }
        prefix = prefix_map.get(section, "X")
        existing_ids = [
            item["id"] for item in codebook["items"]
            if item["id"].startswith(prefix)
        ]
        max_num = 0
        for eid in existing_ids:
            try:
                num = int(eid[len(prefix):])
                max_num = max(max_num, num)
            except ValueError:
                pass
        item_id = f"{prefix}{max_num + 1}"

    new_item = {
        "id": item_id,
        "section": section,
        "question": question,
        "type": item_type,
        "has_scoring": has_scoring,
        "is_reverse": is_reverse,
        "score_yes": 0 if (has_scoring and is_reverse) else (1 if has_scoring else None),
        "score_no": 1 if (has_scoring and is_reverse) else (0 if has_scoring else None),
    }

    codebook["items"].append(new_item)
    save_codebook(codebook)
    logger.info("Added item %s to section %s", item_id, section)
    return new_item


def remove_item(item_id: str) -> bool:
    """Remove an item from the codebook by ID."""
    codebook = load_codebook()
    original_len = len(codebook["items"])
    codebook["items"] = [item for item in codebook["items"] if item["id"] != item_id]

    if len(codebook["items"]) < original_len:
        save_codebook(codebook)
        logger.info("Removed item %s", item_id)
        return True
    return False


def update_item(item_id: str, **kwargs) -> bool:
    """Update an existing item's fields."""
    codebook = load_codebook()
    for item in codebook["items"]:
        if item["id"] == item_id:
            for key, value in kwargs.items():
                if key in item:
                    item[key] = value
            if "has_scoring" in kwargs or "is_reverse" in kwargs:
                if item["has_scoring"]:
                    if item["is_reverse"]:
                        item["score_yes"] = 0
                        item["score_no"] = 1
                    else:
                        item["score_yes"] = 1
                        item["score_no"] = 0
                else:
                    item["score_yes"] = None
                    item["score_no"] = None
            save_codebook(codebook)
            logger.info("Updated item %s", item_id)
            return True
    return False
