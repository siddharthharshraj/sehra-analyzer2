"""SEHRA PDF parser using widget-first extraction approach.

Strategy:
1. Extract header info from PDF form text fields (page 1)
2. Extract checkbox pairs from PDF form widgets (type 2)
3. For each checkbox pair, find nearby text using PyMuPDF text blocks
4. Match extracted text to codebook entries using fuzzy text matching
"""

import re
import json
import logging
from pathlib import Path
from datetime import datetime

import fitz  # PyMuPDF
import pymupdf4llm

from core.exceptions import PDFParsingError

logger = logging.getLogger("sehra.pdf_parser")


# Page ranges for each component (1-indexed)
COMPONENT_PAGE_RANGES = {
    "context": (10, 15),
    "policy": (16, 20),
    "service_delivery": (21, 26),
    "human_resources": (27, 30),
    "supply_chain": (31, 35),
    "barriers": (36, 41),
    "summary": (42, 44),
}

# Noise text to filter out when finding question labels
_NOISE_TEXTS = frozenset({
    "yes", "no", "remarks", "lines of enquiry", "available",
    "peek vision v2  09/23",
})


def extract_header_from_form_fields(doc: fitz.Document) -> dict:
    """Extract country, district, date from PDF form text fields on page 1."""
    page = doc[0]
    widgets = list(page.widgets())

    country = ""
    province = ""
    district = ""
    assessment_date = None

    for w in widgets:
        if w.field_type != 7:
            continue
        name = w.field_name or ""
        value = (w.field_value or "").strip()

        if name == "Text Field 1":
            country = value
        elif name == "Text Field 2":
            province = value
        elif name == "Text Field 3":
            district = value
        elif name == "Text Field 45":
            if value:
                for fmt in ["%B %d, %Y", "%d/%m/%Y", "%Y-%m-%d", "%B %Y",
                            "%d %B %Y", "%b %d, %Y", "%m/%d/%Y"]:
                    try:
                        assessment_date = datetime.strptime(value, fmt).date()
                        break
                    except ValueError:
                        continue

    return {
        "country": country,
        "province": province,
        "district": district,
        "assessment_date": assessment_date,
    }


def extract_all_form_fields(doc: fitz.Document) -> dict:
    """Extract all form field values from the PDF.

    Returns:
        {
            "text_fields": {page_num: [{name, value, rect}]},
            "checkboxes": {page_num: [{name, checked, rect}]},
        }
    """
    text_fields = {}
    checkboxes = {}

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_text = []
        page_checks = []

        for w in page.widgets():
            rect = (w.rect.x0, w.rect.y0, w.rect.x1, w.rect.y1)

            if w.field_type == 7:  # text field
                page_text.append({
                    "name": w.field_name or "",
                    "value": (w.field_value or "").strip(),
                    "rect": rect,
                })
            elif w.field_type == 2:  # checkbox
                checked = w.field_value not in ("Off", "", None)
                page_checks.append({
                    "name": w.field_name or "",
                    "checked": checked,
                    "rect": rect,
                })

        if page_text:
            text_fields[page_num + 1] = page_text
        if page_checks:
            checkboxes[page_num + 1] = page_checks

    return {"text_fields": text_fields, "checkboxes": checkboxes}


def pair_checkboxes(checkboxes: list[dict], y_tolerance: float = 15.0) -> list[dict]:
    """Pair Yes/No checkboxes that are at the same Y position.

    In SEHRA PDFs, checkbox pairs are side-by-side: Yes (left) and No (right).
    When 4+ checkboxes share a Y-position (grid tables), they are split into
    sequential pairs by X-position (every 2 consecutive = 1 yes/no pair).

    Returns list of {y, x, yes_checked, no_checked, answer, extra_checkboxes}.
    """
    if not checkboxes:
        return []

    # Group by Y position
    groups = {}
    for cb in checkboxes:
        y = cb["rect"][1]
        matched = False
        for key_y in list(groups.keys()):
            if abs(y - key_y) < y_tolerance:
                groups[key_y].append(cb)
                matched = True
                break
        if not matched:
            groups[y] = [cb]

    pairs = []
    for y, cbs in sorted(groups.items()):
        cbs_sorted = sorted(cbs, key=lambda c: c["rect"][0])

        if len(cbs_sorted) >= 4 and len(cbs_sorted) % 2 == 0:
            # Grid row: split into sequential pairs of 2
            for i in range(0, len(cbs_sorted), 2):
                yes_cb = cbs_sorted[i]
                no_cb = cbs_sorted[i + 1]
                pairs.append({
                    "y": y,
                    "x": yes_cb["rect"][0],
                    "yes_checked": yes_cb["checked"],
                    "no_checked": no_cb["checked"],
                    "answer": "yes" if yes_cb["checked"] else (
                        "no" if no_cb["checked"] else None),
                    "extra_checkboxes": [],
                })
        elif len(cbs_sorted) >= 2:
            # Standard pair: first 2 are yes/no, rest are extras
            yes_checked = cbs_sorted[0]["checked"]
            no_checked = cbs_sorted[1]["checked"]
            extras = cbs_sorted[2:]
            # When neither yes nor no is checked but an extra checkbox
            # (e.g. "Does not exist") is checked, treat as "no"
            extra_checked = any(e["checked"] for e in extras)
            if yes_checked:
                answer = "yes"
            elif no_checked:
                answer = "no"
            elif extra_checked:
                answer = "no"
            else:
                answer = None
            pairs.append({
                "y": y,
                "x": cbs_sorted[0]["rect"][0],
                "yes_checked": yes_checked,
                "no_checked": no_checked,
                "answer": answer,
                "extra_checkboxes": extras,
            })
        elif len(cbs_sorted) == 1:
            pairs.append({
                "y": y,
                "x": cbs_sorted[0]["rect"][0],
                "yes_checked": cbs_sorted[0]["checked"],
                "no_checked": False,
                "answer": "yes" if cbs_sorted[0]["checked"] else None,
                "extra_checkboxes": [],
            })

    return pairs


def _get_text_blocks(page) -> list[dict]:
    """Get text blocks with their bounding boxes from a PyMuPDF page.

    Each block combines all lines into a single text string.
    """
    raw_blocks = page.get_text("dict")["blocks"]
    result = []
    for b in raw_blocks:
        if "lines" not in b:
            continue
        text_parts = []
        for line in b["lines"]:
            line_text = " ".join(span["text"] for span in line["spans"]).strip()
            if line_text:
                text_parts.append(line_text)
        if text_parts:
            full_text = " ".join(text_parts)
            result.append({
                "text": full_text,
                "x0": b["bbox"][0],
                "y0": b["bbox"][1],
                "x1": b["bbox"][2],
                "y1": b["bbox"][3],
            })
    return result


def _is_noise_text(text: str) -> bool:
    """Check if text is noise (column headers, page labels, etc.)."""
    stripped = text.strip().lower()
    if stripped in _NOISE_TEXTS:
        return True
    # Page numbers
    if stripped.isdigit():
        return True
    # "Yes No" header patterns at start
    if re.match(r'^(yes\s+no|no\s+yes)(\s|$)', stripped):
        return True
    # Section header rows: contain "Yes No" with "Remarks" or "Lines of enquiry"
    if "yes" in stripped and "no" in stripped and (
        "remarks" in stripped or "lines of enquiry" in stripped
    ):
        return True
    # Section sub-headers like "Information and awareness", "Does the information highlight..."
    if stripped.startswith("does the information highlight"):
        return True
    if stripped == "information and awareness":
        return True
    return False


def _find_question_for_pair(text_blocks: list[dict], pair_x: float,
                            pair_y: float, is_grid: bool = False,
                            grid_col_headers: dict | None = None) -> str:
    """Find the question text for a checkbox pair using spatial proximity.

    For regular pairs: finds the text block to the left at similar Y.
    For grid pairs: combines row label with column header.
    """
    y_tol = 15

    if is_grid and grid_col_headers:
        # Grid pair: find row label (leftmost text at same Y)
        row_candidates = []
        for block in text_blocks:
            if block["x0"] >= pair_x - 10:
                continue
            if _is_noise_text(block["text"]):
                continue
            if block["y0"] - y_tol <= pair_y <= block["y1"] + y_tol:
                row_candidates.append(block)

        row_candidates.sort(key=lambda b: b["x0"])
        row_label = ""
        for cand in row_candidates:
            text = cand["text"].strip()
            if len(text) >= 3 and not _is_noise_text(text):
                row_label = text
                break

        # Find column header for this pair's X position
        col_header = ""
        best_x_dist = float("inf")
        for col_x, header_text in grid_col_headers.items():
            dist = abs(col_x - pair_x)
            if dist < best_x_dist:
                best_x_dist = dist
                col_header = header_text

        if row_label and col_header:
            return f"{row_label} {col_header}"
        return row_label or col_header or ""

    # Regular pair: find text block to the left at similar Y
    candidates = []
    for block in text_blocks:
        if block["x0"] >= pair_x:
            continue
        if _is_noise_text(block["text"]):
            continue
        # Block's Y range should overlap with checkbox Y
        if block["y0"] - y_tol <= pair_y <= block["y1"] + y_tol:
            candidates.append(block)

    if not candidates:
        return ""

    # Prefer closest by Y centroid distance, then longest text
    candidates.sort(key=lambda b: (abs((b["y0"] + b["y1"]) / 2 - pair_y),
                                    -len(b["text"])))
    return candidates[0]["text"]


def _find_grid_column_headers(text_blocks: list[dict],
                               grid_pairs: list[dict]) -> dict:
    """Find column headers for grid checkbox pairs.

    Looks for text blocks above the first grid row at similar X positions
    to each pair's X coordinate.

    Returns: {x_position: header_text}
    """
    if not grid_pairs:
        return {}

    min_y = min(p["y"] for p in grid_pairs)
    pair_xs = sorted(set(round(p["x"]) for p in grid_pairs))

    headers = {}
    for pair_x in pair_xs:
        best = None
        best_dist = float("inf")
        for block in text_blocks:
            if _is_noise_text(block["text"]):
                continue
            if len(block["text"].strip()) < 3:
                continue
            # Must be above the first grid row
            if block["y1"] > min_y - 5:
                continue
            # X must be close to the pair's X
            x_dist = abs(block["x0"] - pair_x)
            if x_dist > 40:
                continue
            if x_dist < best_dist:
                best_dist = x_dist
                best = block
        if best:
            headers[pair_x] = best["text"].strip()

    return headers


def extract_items_widget_first(doc: fitz.Document, page_range: tuple) -> list[dict]:
    """Widget-first extraction: start from checkboxes, find nearby text.

    This replaces the old question-first approach (extract_questions_and_remarks +
    merge_questions_with_checkboxes) with a more reliable method that starts from
    the checkbox widgets and looks for nearby text.

    Returns list of {question, answer, page_num, remark}.
    """
    items = []

    for page_num in range(page_range[0], min(page_range[1] + 1, len(doc) + 1)):
        page = doc[page_num - 1]

        # Extract checkboxes on this page
        cbs = []
        for w in page.widgets():
            if w.field_type == 2:
                checked = w.field_value not in ("Off", "", None)
                cbs.append({
                    "name": w.field_name or "",
                    "checked": checked,
                    "rect": (w.rect.x0, w.rect.y0, w.rect.x1, w.rect.y1),
                })

        if not cbs:
            continue

        pairs = pair_checkboxes(cbs)
        text_blocks = _get_text_blocks(page)

        # Detect grid rows: group pairs by Y to find rows with multiple pairs
        y_groups = {}
        for pair in pairs:
            y = pair["y"]
            matched_y = None
            for ky in y_groups:
                if abs(y - ky) < 15:
                    matched_y = ky
                    break
            if matched_y is not None:
                y_groups[matched_y].append(pair)
            else:
                y_groups[y] = [pair]

        # Collect all grid pairs and find column headers
        grid_pairs_all = []
        for y, group in y_groups.items():
            if len(group) > 1:
                grid_pairs_all.extend(group)

        grid_col_headers = _find_grid_column_headers(text_blocks, grid_pairs_all)

        # Extract question text for each pair
        for pair in pairs:
            is_grid = any(
                abs(pair["y"] - ky) < 15 and len(group) > 1
                for ky, group in y_groups.items()
            )

            question = _find_question_for_pair(
                text_blocks, pair["x"], pair["y"],
                is_grid=is_grid,
                grid_col_headers=grid_col_headers,
            )

            # Clean up question text
            question = re.sub(r'\s+', ' ', question).strip()

            if question:
                items.append({
                    "question": question,
                    "answer": pair["answer"],
                    "page_num": page_num,
                    "remark": "",
                })

    return items


def parse_sehra_pdf(pdf_path: str) -> dict:
    """Main entry point: parse a SEHRA PDF into structured data.

    Uses a widget-first approach:
    - PyMuPDF form fields for header info
    - Checkbox widgets as the starting point for item extraction
    - Text block proximity for question text identification
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise PDFParsingError(f"Failed to open PDF: {e}") from e

    try:
        full_md = pymupdf4llm.to_markdown(pdf_path)

        # Step 1: Extract header from form fields
        header = extract_header_from_form_fields(doc)
        logger.info("Header extracted: country=%s, district=%s",
                     header["country"], header["district"])

        # Step 2: Extract all form fields (for text field remarks)
        form_data = extract_all_form_fields(doc)
        logger.info(
            "Form fields: %d pages with checkboxes, %d pages with text fields",
            len(form_data["checkboxes"]), len(form_data["text_fields"]),
        )

        # Step 3: Widget-first extraction per component
        components = {}
        for comp_name, page_range in COMPONENT_PAGE_RANGES.items():
            merged = extract_items_widget_first(doc, page_range)

            # Collect text field values as additional remarks
            text_remarks = {}
            for page_num in range(page_range[0], page_range[1] + 1):
                for tf in form_data["text_fields"].get(page_num, []):
                    if tf["value"]:
                        text_remarks[page_num] = text_remarks.get(page_num, [])
                        text_remarks[page_num].append(tf["value"])

            # Collect page text for AI context
            page_texts = []
            for page_num in range(page_range[0],
                                   min(page_range[1] + 1, len(doc) + 1)):
                page_texts.append(doc[page_num - 1].get_text("text"))

            components[comp_name] = {
                "items": merged,
                "text_field_values": text_remarks,
                "text": "\n".join(page_texts),
            }
            logger.info("Component %s: %d items extracted",
                         comp_name, len(merged))

        return {
            "header": {
                "country": header["country"],
                "district": header["district"],
                "province": header["province"],
                "assessment_date": (header["assessment_date"].isoformat()
                                    if header["assessment_date"] else None),
            },
            "full_text": full_md,
            "components": components,
        }
    except PDFParsingError:
        raise
    except Exception as e:
        raise PDFParsingError(f"PDF parsing failed: {e}") from e
    finally:
        doc.close()


def match_items_to_codebook(parsed_items: list[dict], codebook_items: list[dict],
                            component: str) -> list[dict]:
    """Match parsed PDF items to codebook entries using fuzzy text matching.

    Improvements over the basic approach:
    - Lower threshold (0.30) for better recall on short labels
    - When text is short, also match against distinguishing parts of codebook questions
    - Bidirectional substring containment
    """
    from difflib import SequenceMatcher

    def normalize(text: str) -> str:
        return re.sub(r'\s+', ' ', text.lower().strip())

    def extract_key_words(text: str) -> str:
        """Extract distinguishing words from a codebook question."""
        # Remove common preamble words
        cleaned = re.sub(
            r'^(are there any|is there a|does a|do any|are the|is a|is |are |does |do )',
            '', text, flags=re.IGNORECASE,
        )
        return cleaned.strip()

    comp_codebook = [cb for cb in codebook_items if cb["section"] == component]

    matched = []
    used_codebook_ids = set()

    for item in parsed_items:
        q_norm = normalize(item["question"])
        best_match = None
        best_ratio = 0.0

        for cb in comp_codebook:
            if cb["id"] in used_codebook_ids:
                continue
            cb_norm = normalize(cb["question"])
            ratio = SequenceMatcher(None, q_norm, cb_norm).ratio()

            # Bidirectional substring containment
            if cb_norm in q_norm or q_norm in cb_norm:
                ratio = max(ratio, 0.85)

            # Check first 30 chars match (handles truncated text)
            if q_norm[:30] == cb_norm[:30] and len(q_norm) > 20:
                ratio = max(ratio, 0.80)

            # For short extracted text, try matching against the
            # distinguishing part of the codebook question
            if len(q_norm) < 30:
                cb_key = normalize(extract_key_words(cb["question"]))
                if q_norm in cb_key or cb_key in q_norm:
                    ratio = max(ratio, 0.85)
                else:
                    key_ratio = SequenceMatcher(None, q_norm, cb_key).ratio()
                    ratio = max(ratio, key_ratio)

            if ratio > best_ratio and ratio > 0.30:
                best_ratio = ratio
                best_match = cb

        enriched = {**item, "component": component}
        if best_match:
            enriched["item_id"] = best_match["id"]
            enriched["codebook_question"] = best_match["question"]
            enriched["match_confidence"] = best_ratio
            used_codebook_ids.add(best_match["id"])
        else:
            enriched["item_id"] = ""
            enriched["match_confidence"] = 0.0

        matched.append(enriched)

    return matched


def extract_numeric_data(component_text: str, component: str) -> list[dict]:
    """Extract numeric/demographic data from context pages using pattern matching.

    Looks for patterns like "Total population: 5,000,000" or tabular numeric data.

    Args:
        component_text: Raw text of the component's pages
        component: Component key (mainly useful for 'context')

    Returns:
        List of {label, value, unit} dicts
    """
    import re
    results = []

    # Pattern: "Label: number" or "Label = number"
    patterns = [
        r'([A-Z][a-zA-Z\s,/()]+?)[:=]\s*([\d,]+(?:\.\d+)?)\s*(%|per\s*cent|million|thousand)?',
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, component_text):
            label = match.group(1).strip()
            value_str = match.group(2).replace(",", "")
            unit = match.group(3) or ""

            # Skip noise
            if len(label) < 3 or len(label) > 100:
                continue
            if label.lower() in ("yes", "no", "page", "v2"):
                continue

            try:
                value = float(value_str)
                results.append({
                    "label": label,
                    "value": value,
                    "unit": unit.strip(),
                })
            except ValueError:
                pass

    logger.info("Extracted %d numeric data points from %s", len(results), component)
    return results


def parse_and_enrich(pdf_path: str, codebook_path: str = None) -> dict:
    """Parse PDF and enrich with codebook item IDs.

    This is the main function to call from the pipeline.
    """
    logger.info("Starting parse_and_enrich for %s", pdf_path)

    if codebook_path is None:
        codebook_path = str(Path(__file__).parent.parent / "data" / "codebook.json")

    with open(codebook_path) as f:
        codebook = json.load(f)

    parsed = parse_sehra_pdf(pdf_path)

    for comp_name, comp_data in parsed["components"].items():
        if comp_data["items"]:
            comp_data["items"] = match_items_to_codebook(
                comp_data["items"],
                codebook["items"],
                comp_name,
            )

    total_items = sum(len(c.get("items", [])) for c in parsed["components"].values())
    logger.info("Parse complete: %d total items across %d components",
                 total_items, len(parsed["components"]))
    return parsed


def parse_and_enrich_auto(pdf_path: str, codebook_path: str = None) -> dict:
    """Auto-detect PDF type and parse accordingly.

    Uses widget-first parsing for digital PDFs, Surya OCR for scanned PDFs.
    Both paths produce the same output structure.

    Args:
        pdf_path: Path to the SEHRA PDF
        codebook_path: Optional path to codebook JSON

    Returns:
        Same structure as parse_and_enrich()
    """
    doc = fitz.open(pdf_path)
    has_widgets = any(list(doc[0].widgets()))
    doc.close()

    if has_widgets:
        return parse_and_enrich(pdf_path, codebook_path)

    # Scanned PDF — use Surya OCR
    from core.surya_parser import surya_parse_sehra
    logger.info("No widgets detected — routing to Surya OCR parser")
    parsed = surya_parse_sehra(pdf_path)

    # Enrich with codebook IDs
    if codebook_path is None:
        codebook_path = str(Path(__file__).parent.parent / "data" / "codebook.json")

    with open(codebook_path) as f:
        codebook = json.load(f)

    for comp_name, comp_data in parsed["components"].items():
        if comp_data["items"]:
            comp_data["items"] = match_items_to_codebook(
                comp_data["items"],
                codebook["items"],
                comp_name,
            )

    total_items = sum(len(c.get("items", [])) for c in parsed["components"].values())
    logger.info("Auto-parse complete: %d total items across %d components",
                 total_items, len(parsed["components"]))
    return parsed
