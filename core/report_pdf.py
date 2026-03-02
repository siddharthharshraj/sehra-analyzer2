"""PDF report generator using WeasyPrint (HTML → PDF conversion).

Falls back gracefully if WeasyPrint is not installed.
"""

import io
import logging

logger = logging.getLogger("sehra.report_pdf")


def generate_pdf_report(html_content: str) -> io.BytesIO:
    """Convert an HTML report string to a PDF.

    Args:
        html_content: Self-contained HTML (from report_html.generate_html_report)

    Returns:
        BytesIO containing the PDF file
    """
    try:
        from weasyprint import HTML
    except ImportError:
        raise RuntimeError(
            "WeasyPrint is not installed. Install with: pip install weasyprint"
        )

    # Add print-optimized CSS overrides
    print_css = """
    <style>
        @page { size: A4; margin: 2cm; }
        body { max-width: 100%; padding: 0; }
        .header { page-break-after: always; }
        details { break-inside: avoid; }
        details[open] summary ~ * { break-inside: avoid; }
        .chart-container { break-inside: avoid; page-break-inside: avoid; }
        table { font-size: 8pt; }
    </style>
    """
    # Inject print CSS before </head>
    html_with_print = html_content.replace("</head>", print_css + "</head>")

    buf = io.BytesIO()
    HTML(string=html_with_print).write_pdf(buf)
    buf.seek(0)
    logger.info("PDF report generated: %d bytes", buf.getbuffer().nbytes)
    return buf
