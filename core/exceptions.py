"""Custom exception hierarchy for SEHRA Analyzer.

Provides structured error responses with unique error IDs for debugging.
"""

import uuid


def _generate_error_id() -> str:
    """Generate a short unique error ID for tracking (e.g., 'ERR-A3F2')."""
    return f"ERR-{uuid.uuid4().hex[:4].upper()}"


class SEHRAError(Exception):
    """Base exception for all SEHRA Analyzer errors.

    Attributes:
        error_id: Unique short ID for log correlation (e.g., "ERR-A3F2").
        detail: Human-readable explanation.
        status_code: HTTP status code to return (default 500).
    """

    def __init__(self, message: str = "An internal error occurred",
                 detail: str = "", status_code: int = 500):
        super().__init__(message)
        self.error_id = _generate_error_id()
        self.message = message
        self.detail = detail or message
        self.status_code = status_code

    def to_response(self) -> dict:
        """Return a structured JSON error response."""
        return {
            "error": self.message,
            "error_id": self.error_id,
            "detail": self.detail,
        }


class PDFParsingError(SEHRAError):
    """Raised when PDF parsing fails."""

    def __init__(self, message: str = "PDF parsing failed", detail: str = ""):
        super().__init__(message=message, detail=detail, status_code=422)


class ScoringError(SEHRAError):
    """Raised when codebook scoring encounters an error."""

    def __init__(self, message: str = "Scoring error", detail: str = ""):
        super().__init__(message=message, detail=detail, status_code=500)


class AIAnalysisError(SEHRAError):
    """Raised when AI/LLM analysis fails."""

    def __init__(self, message: str = "AI analysis failed", detail: str = ""):
        super().__init__(message=message, detail=detail, status_code=502)


class ShareError(SEHRAError):
    """Raised when share link operations fail."""

    def __init__(self, message: str = "Share operation failed", detail: str = ""):
        super().__init__(message=message, detail=detail, status_code=400)


class ValidationError(SEHRAError):
    """Raised when input validation fails."""

    def __init__(self, message: str = "Validation error", detail: str = ""):
        super().__init__(message=message, detail=detail, status_code=422)
