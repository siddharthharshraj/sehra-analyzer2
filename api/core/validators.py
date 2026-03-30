"""Input validation for SEHRA Analyzer."""

import logging

import fitz  # PyMuPDF

from core.exceptions import ValidationError
from core.pdf_parser import get_min_page_count

logger = logging.getLogger("sehra.validators")

MAX_PDF_SIZE = 10 * 1024 * 1024  # 10 MB
MIN_PAGE_COUNT = 40  # Default; use get_min_page_count(country) for country-specific


def validate_sehra_pdf(uploaded_file, country: str = "default") -> dict:
    """Validate an uploaded file is a valid SEHRA PDF.

    Checks:
    - File size <= 10 MB
    - File is a PDF (by type attribute)
    - Page count >= min_page_count (country-configurable, default 40)
    - Has form widgets on page 1 (SEHRA PDFs have header form fields)

    Args:
        uploaded_file: Streamlit UploadedFile object
        country: Country key for country-specific validation thresholds

    Returns:
        dict with validation details: {pages, widgets_on_page1}

    Raises:
        ValidationError: If any check fails
    """
    # Check file size
    size = uploaded_file.size
    if size > MAX_PDF_SIZE:
        raise ValidationError(
            f"File too large: {size / 1024 / 1024:.1f} MB (max {MAX_PDF_SIZE // 1024 // 1024} MB)"
        )

    # Check MIME type
    file_type = getattr(uploaded_file, "type", "")
    if file_type and "pdf" not in file_type.lower():
        raise ValidationError(f"Not a PDF file (type: {file_type})")

    # Read bytes and validate with PyMuPDF
    pdf_bytes = uploaded_file.getvalue()
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise ValidationError(f"Cannot open as PDF: {e}")

    try:
        page_count = len(doc)
        min_pages = get_min_page_count(country)
        if page_count < min_pages:
            raise ValidationError(
                f"PDF has {page_count} pages (expected >= {min_pages} for SEHRA)"
            )

        # Check for form widgets on page 1
        page1 = doc[0]
        widgets = list(page1.widgets())
        has_widgets = len(widgets) > 0

        if not has_widgets:
            # No widgets — this is likely a scanned PDF.
            # Check if Surya OCR is available as a fallback.
            from core.surya_parser import is_surya_available
            if not is_surya_available():
                raise ValidationError(
                    "No form fields found and OCR support not installed. "
                    "Install surya-ocr for scanned PDF support."
                )
            logger.info(
                "PDF validated (scanned): %d pages, no widgets — will use OCR",
                page_count,
            )
        else:
            logger.info(
                "PDF validated: %d pages, %d widgets on page 1",
                page_count, len(widgets),
            )

        return {
            "pages": page_count,
            "widgets_on_page1": len(widgets),
            "is_scanned": not has_widgets,
        }
    finally:
        doc.close()
