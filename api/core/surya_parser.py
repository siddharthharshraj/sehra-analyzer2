"""SEHRA PDF parser using Surya OCR for scanned/photographed PDFs.

Fallback parser for when the primary widget-first approach (PyMuPDF) finds
no form widgets — i.e., the PDF is a scanned printout or photo rather than
a digitally-filled form.

Strategy:
1. Convert PDF pages to images
2. Run Surya OCR to extract text with bounding boxes
3. Use layout analysis to identify text/form/table regions
4. Detect checkbox states via pixel density analysis
5. Map extracted data to the same output structure as parse_sehra_pdf()
"""

import logging
import re
from datetime import datetime
from pathlib import Path

from core.exceptions import PDFParsingError
from core.pdf_parser import COMPONENT_PAGE_RANGES, get_page_ranges

logger = logging.getLogger("sehra.surya_parser")

# Cached Surya predictors (lazy-loaded)
_surya_predictors = None


def is_surya_available() -> bool:
    """Check if surya-ocr is installed and importable."""
    try:
        import surya  # noqa: F401
        return True
    except ImportError:
        return False


def _init_surya_predictors() -> dict:
    """Lazy-load and cache Surya predictor models.

    Returns dict with keys: ocr, layout, table.
    Models are loaded once and reused across calls.
    """
    global _surya_predictors
    if _surya_predictors is not None:
        return _surya_predictors

    logger.info("Loading Surya predictor models (first use, may take a moment)...")

    try:
        from surya.recognition import RecognitionPredictor
        from surya.detection import DetectionPredictor
        from surya.layout import LayoutPredictor
        from surya.table_rec import TableRecPredictor

        recognition_predictor = RecognitionPredictor()
        detection_predictor = DetectionPredictor()
        layout_predictor = LayoutPredictor()
        table_predictor = TableRecPredictor()

        _surya_predictors = {
            "recognition": recognition_predictor,
            "detection": detection_predictor,
            "layout": layout_predictor,
            "table": table_predictor,
        }
        logger.info("Surya predictors loaded successfully")
        return _surya_predictors
    except Exception as e:
        raise PDFParsingError(f"Failed to load Surya models: {e}") from e


def _load_pdf_images(pdf_path: str, page_range: tuple = None) -> list:
    """Convert PDF pages to PIL Images for Surya input.

    Args:
        pdf_path: Path to PDF file
        page_range: Optional (start, end) 1-indexed page range.
                    If None, loads all pages.

    Returns:
        List of PIL Image objects
    """
    import fitz
    from PIL import Image
    import io

    doc = fitz.open(pdf_path)
    images = []

    if page_range:
        start = max(0, page_range[0] - 1)
        end = min(len(doc), page_range[1])
    else:
        start = 0
        end = len(doc)

    try:
        for page_num in range(start, end):
            page = doc[page_num]
            # Render at 2x resolution for better OCR accuracy
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            images.append(img)
    finally:
        doc.close()

    return images


def _detect_checkbox_state(page_image, bbox: tuple) -> str | None:
    """Detect if a checkbox region is checked by analyzing pixel density.

    SEHRA forms have a standard layout:
        [Question text] [Yes box] [No box] [Remarks]

    We crop each checkbox area, convert to grayscale, threshold, and
    count dark pixels. The checkbox with significantly more dark pixels
    (mark/tick/cross) is the checked one.

    Args:
        page_image: PIL Image of the full page
        bbox: (x0, y0, x1, y1) bounding box of the checkbox region

    Returns:
        'yes', 'no', or None if indeterminate
    """
    from PIL import Image
    import numpy as np

    x0, y0, x1, y1 = [int(v) for v in bbox]
    width = x1 - x0
    height = y1 - y0

    if width <= 0 or height <= 0:
        return None

    # Crop the checkbox region
    cropped = page_image.crop((x0, y0, x1, y1))
    gray = cropped.convert("L")
    pixels = np.array(gray)

    # Threshold: pixels darker than 128 are "marked"
    dark_mask = pixels < 128
    total_pixels = pixels.size
    if total_pixels == 0:
        return None

    dark_ratio = dark_mask.sum() / total_pixels

    # A checked box typically has 15-60% dark pixels (mark/tick)
    # An empty box has <10% dark pixels (just the border)
    if dark_ratio > 0.15:
        return "checked"
    return "empty"


def _find_checkbox_pairs_by_position(ocr_lines: list, page_image,
                                      page_width: int) -> list[dict]:
    """Find checkbox pairs by looking for Yes/No text and analyzing nearby regions.

    SEHRA forms have a consistent column layout. After finding question text,
    we look for checkbox regions to the right of the question.

    Args:
        ocr_lines: List of dicts with 'text' and 'bbox' from OCR
        page_image: PIL Image of the page
        page_width: Width of the page image

    Returns:
        List of {question, answer, bbox}
    """
    results = []
    # Typical SEHRA layout: question occupies left ~60% of page,
    # Yes checkbox at ~65%, No checkbox at ~75%
    yes_col_start = int(page_width * 0.60)
    yes_col_end = int(page_width * 0.72)
    no_col_start = int(page_width * 0.72)
    no_col_end = int(page_width * 0.85)

    # Group OCR lines by vertical position (same row)
    for line in ocr_lines:
        text = line["text"].strip()
        bbox = line["bbox"]

        # Skip short text, headers, noise
        if len(text) < 5:
            continue
        if text.lower() in ("yes", "no", "remarks", "lines of enquiry"):
            continue

        # Only consider text in the question column (left portion)
        if bbox[0] > page_width * 0.55:
            continue

        # Look for checkbox regions to the right of this text
        line_y_center = (bbox[1] + bbox[3]) / 2
        cb_height = bbox[3] - bbox[1]
        if cb_height <= 0:
            cb_height = 20

        # Check "Yes" column
        yes_bbox = (yes_col_start, int(line_y_center - cb_height / 2),
                    yes_col_end, int(line_y_center + cb_height / 2))
        yes_state = _detect_checkbox_state(page_image, yes_bbox)

        # Check "No" column
        no_bbox = (no_col_start, int(line_y_center - cb_height / 2),
                   no_col_end, int(line_y_center + cb_height / 2))
        no_state = _detect_checkbox_state(page_image, no_bbox)

        # Determine answer
        answer = None
        if yes_state == "checked" and no_state != "checked":
            answer = "yes"
        elif no_state == "checked" and yes_state != "checked":
            answer = "no"
        elif yes_state == "checked" and no_state == "checked":
            # Both checked is unusual; treat as yes
            answer = "yes"

        results.append({
            "question": text,
            "answer": answer,
            "bbox": bbox,
        })

    return results


def _extract_header_ocr(images: list, predictors: dict) -> dict:
    """OCR page 1 to extract country, district, province, date.

    Args:
        images: List of PIL Images (we use the first one)
        predictors: Dict of Surya predictors

    Returns:
        Dict with country, province, district, assessment_date
    """
    if not images:
        return {
            "country": "",
            "province": "",
            "district": "",
            "assessment_date": None,
        }

    page1_image = images[0]
    recognition = predictors["recognition"]
    detection = predictors["detection"]

    # Run OCR on page 1
    predictions = recognition([page1_image], [None], detection)
    if not predictions:
        return {
            "country": "",
            "province": "",
            "district": "",
            "assessment_date": None,
        }

    # Collect all text lines with positions
    lines = []
    for pred in predictions:
        for line in pred.text_lines:
            lines.append({
                "text": line.text.strip(),
                "bbox": line.bbox,
            })

    # Sort by vertical position
    lines.sort(key=lambda l: l["bbox"][1])

    country = ""
    province = ""
    district = ""
    assessment_date = None

    # Look for labeled fields: "Country:", "Province:", "District:", "Date:"
    for i, line in enumerate(lines):
        text = line["text"]
        text_lower = text.lower()

        if "country" in text_lower:
            # Value may be on the same line after ":" or on the next line
            country = _extract_field_value(text, "country", lines, i)
        elif "province" in text_lower or "state" in text_lower:
            province = _extract_field_value(text, "province", lines, i)
        elif "district" in text_lower:
            district = _extract_field_value(text, "district", lines, i)
        elif "date" in text_lower:
            date_str = _extract_field_value(text, "date", lines, i)
            if date_str:
                for fmt in ["%B %d, %Y", "%d/%m/%Y", "%Y-%m-%d", "%B %Y",
                            "%d %B %Y", "%b %d, %Y", "%m/%d/%Y",
                            "%d-%m-%Y", "%d.%m.%Y"]:
                    try:
                        assessment_date = datetime.strptime(date_str.strip(), fmt).date()
                        break
                    except ValueError:
                        continue

    return {
        "country": country,
        "province": province,
        "district": district,
        "assessment_date": assessment_date,
    }


def _extract_field_value(text: str, field_name: str,
                          lines: list, current_idx: int) -> str:
    """Extract field value from OCR text, handling 'Label: Value' patterns.

    Tries:
    1. Split on ':' and take the right side
    2. Remove the field name and take remainder
    3. Look at the next line if current line only has the label
    """
    # Try splitting on ':'
    if ":" in text:
        parts = text.split(":", 1)
        value = parts[1].strip()
        if value:
            return value

    # Try removing the field name
    pattern = re.compile(re.escape(field_name), re.IGNORECASE)
    cleaned = pattern.sub("", text).strip(" :-")
    if cleaned and len(cleaned) > 1:
        return cleaned

    # Look at the next line (same horizontal region)
    if current_idx + 1 < len(lines):
        next_line = lines[current_idx + 1]
        next_text = next_line["text"].strip()
        # Only use if it doesn't look like another label
        if next_text and ":" not in next_text and len(next_text) < 100:
            return next_text

    return ""


def _extract_items_ocr(images: list, predictors: dict,
                        page_range: tuple) -> list[dict]:
    """Extract question-answer pairs from scanned pages using OCR.

    Process:
    1. Run OCR on each page to get text with bounding boxes
    2. Identify question text in the left column
    3. Detect checkbox states via pixel density analysis
    4. Use table recognition for grid sections

    Args:
        images: List of PIL Images for the component's pages
        predictors: Dict of Surya predictors
        page_range: (start, end) 1-indexed page range

    Returns:
        List of {question, answer, page_num, remark}
    """
    recognition = predictors["recognition"]
    detection = predictors["detection"]
    layout_predictor = predictors["layout"]
    table_predictor = predictors["table"]

    items = []

    for i, page_image in enumerate(images):
        page_num = page_range[0] + i
        page_width = page_image.width

        # Run OCR
        predictions = recognition([page_image], [None], detection)
        if not predictions:
            continue

        # Collect OCR lines
        ocr_lines = []
        for pred in predictions:
            for line in pred.text_lines:
                ocr_lines.append({
                    "text": line.text.strip(),
                    "bbox": line.bbox,
                })

        # Run layout analysis to find table regions
        layout_preds = layout_predictor([page_image])
        table_regions = []
        if layout_preds:
            for pred in layout_preds:
                for block in pred.bboxes:
                    if block.label.lower() in ("table", "form", "figure"):
                        table_regions.append(block.bbox)

        # Check if this page has a grid/table section
        has_table = len(table_regions) > 0

        if has_table:
            # Use table recognition for grid sections
            table_items = _extract_table_items(
                page_image, table_predictor, recognition,
                detection, page_num
            )
            items.extend(table_items)

        # Extract regular (non-table) items via checkbox position analysis
        regular_items = _find_checkbox_pairs_by_position(
            ocr_lines, page_image, page_width
        )

        for item in regular_items:
            # Skip items that overlap with table regions
            if has_table and _bbox_in_regions(item["bbox"], table_regions):
                continue

            items.append({
                "question": _clean_question_text(item["question"]),
                "answer": item["answer"],
                "page_num": page_num,
                "remark": "",
            })

    return items


def _extract_table_items(page_image, table_predictor,
                          recognition, detection, page_num: int) -> list[dict]:
    """Extract items from grid/table regions using Surya table recognition.

    SEHRA grid tables have rows (questions) and columns (sectors/categories).
    Each cell contains a Yes/No checkbox pair.

    Args:
        page_image: PIL Image of the page
        table_predictor: Surya TableRecPredictor
        recognition: Surya RecognitionPredictor
        detection: Surya DetectionPredictor
        page_num: 1-indexed page number

    Returns:
        List of {question, answer, page_num, remark}
    """
    items = []

    table_preds = table_predictor([page_image])
    if not table_preds:
        return items

    for table_pred in table_preds:
        if not table_pred.tables:
            continue

        for table in table_pred.tables:
            # Extract row and column headers
            rows = {}  # row_idx -> row_label
            cols = {}  # col_idx -> col_header

            for cell in table.cells:
                # Get text in this cell via OCR
                cell_bbox = cell.bbox
                cell_crop = page_image.crop(cell_bbox)
                cell_preds = recognition([cell_crop], [None], detection)

                cell_text = ""
                if cell_preds:
                    for pred in cell_preds:
                        for line in pred.text_lines:
                            cell_text += line.text.strip() + " "
                cell_text = cell_text.strip()

                row_idx = cell.row
                col_idx = cell.col

                # First column typically has row labels (questions)
                if col_idx == 0 and cell_text:
                    rows[row_idx] = cell_text
                # First row typically has column headers
                elif row_idx == 0 and cell_text:
                    cols[col_idx] = cell_text
                # Data cells contain checkboxes
                elif row_idx > 0 and col_idx > 0:
                    state = _detect_checkbox_state(page_image, cell_bbox)
                    row_label = rows.get(row_idx, "")
                    col_header = cols.get(col_idx, "")

                    if row_label:
                        question = f"{row_label} {col_header}".strip()
                        question = _clean_question_text(question)

                        answer = None
                        if state == "checked":
                            # In a grid, we need to determine if this is
                            # a Yes or No column. Check column header.
                            col_text = col_header.lower()
                            if "no" in col_text:
                                answer = "no"
                            else:
                                answer = "yes"
                        # For empty cells, answer stays None

                        items.append({
                            "question": question,
                            "answer": answer,
                            "page_num": page_num,
                            "remark": "",
                        })

    return items


def _bbox_in_regions(bbox: tuple, regions: list[tuple],
                      overlap_threshold: float = 0.5) -> bool:
    """Check if a bounding box overlaps significantly with any region."""
    bx0, by0, bx1, by1 = bbox
    b_area = max((bx1 - bx0) * (by1 - by0), 1)

    for rx0, ry0, rx1, ry1 in regions:
        # Compute intersection
        ix0 = max(bx0, rx0)
        iy0 = max(by0, ry0)
        ix1 = min(bx1, rx1)
        iy1 = min(by1, ry1)

        if ix0 < ix1 and iy0 < iy1:
            intersection = (ix1 - ix0) * (iy1 - iy0)
            if intersection / b_area > overlap_threshold:
                return True

    return False


def _clean_question_text(text: str) -> str:
    """Clean up OCR-extracted question text."""
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove leading bullets, numbers, dashes
    text = re.sub(r'^[\d\.\-\)\]]+\s*', '', text)
    # Remove trailing punctuation noise
    text = text.rstrip('.-:;,')
    return text.strip()


def surya_parse_sehra(pdf_path: str, country: str = "default") -> dict:
    """Parse a scanned SEHRA PDF using Surya OCR.

    This is the main entry point for the Surya parser. It produces the same
    output structure as parse_sehra_pdf() so downstream pipeline (scoring,
    AI analysis, DB save) works unchanged.

    Args:
        pdf_path: Path to the scanned SEHRA PDF
        country: Country key for country-specific page ranges and config

    Returns:
        Dict with same structure as parse_sehra_pdf():
        {
            "header": {country, province, district, assessment_date},
            "full_text": str,
            "components": {
                comp_name: {
                    "items": [{question, answer, page_num, remark}],
                    "text_field_values": {},
                    "text": str,
                }
            }
        }

    Raises:
        PDFParsingError: If parsing fails
    """
    if not is_surya_available():
        raise PDFParsingError(
            "Surya OCR is not installed. Install with: pip install surya-ocr"
        )

    logger.info("Starting Surya OCR parse for %s", pdf_path)

    try:
        predictors = _init_surya_predictors()

        # Load page 1 for header extraction
        header_images = _load_pdf_images(pdf_path, page_range=(1, 1))
        header = _extract_header_ocr(header_images, predictors)
        logger.info("Header extracted: country=%s, district=%s",
                     header["country"], header["district"])

        # Extract full text via OCR (for AI context)
        all_images = _load_pdf_images(pdf_path)
        recognition = predictors["recognition"]
        detection = predictors["detection"]

        full_text_parts = []
        for img in all_images:
            preds = recognition([img], [None], detection)
            if preds:
                for pred in preds:
                    for line in pred.text_lines:
                        full_text_parts.append(line.text)
        full_text = "\n".join(full_text_parts)

        # Auto-detect country from header if not explicitly provided
        detected_country = header.get("country", "").strip()
        if country == "default" and detected_country:
            country = detected_country
            logger.info("Auto-detected country from OCR header: %s", country)

        # Extract items per component
        page_ranges = get_page_ranges(country)
        components = {}
        for comp_name, page_range in page_ranges.items():
            comp_images = _load_pdf_images(pdf_path, page_range=page_range)

            items = _extract_items_ocr(comp_images, predictors, page_range)

            # Extract component text for AI context
            comp_text_parts = []
            for img in comp_images:
                preds = recognition([img], [None], detection)
                if preds:
                    for pred in preds:
                        for line in pred.text_lines:
                            comp_text_parts.append(line.text)

            components[comp_name] = {
                "items": items,
                "text_field_values": {},
                "text": "\n".join(comp_text_parts),
            }
            logger.info("Component %s: %d items extracted (OCR)",
                         comp_name, len(items))

        total_items = sum(len(c["items"]) for c in components.values())
        logger.info("Surya parse complete: %d total items", total_items)

        return {
            "header": {
                "country": header["country"],
                "district": header["district"],
                "province": header["province"],
                "assessment_date": (header["assessment_date"].isoformat()
                                    if header["assessment_date"] else None),
            },
            "full_text": full_text,
            "components": components,
        }

    except PDFParsingError:
        raise
    except Exception as e:
        raise PDFParsingError(f"Surya OCR parsing failed: {e}") from e
