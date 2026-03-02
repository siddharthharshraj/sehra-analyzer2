"""Custom exception hierarchy for SEHRA Analyzer."""


class SEHRAError(Exception):
    """Base exception for all SEHRA Analyzer errors."""
    pass


class PDFParsingError(SEHRAError):
    """Raised when PDF parsing fails."""
    pass


class ScoringError(SEHRAError):
    """Raised when codebook scoring encounters an error."""
    pass


class AIAnalysisError(SEHRAError):
    """Raised when AI/LLM analysis fails."""
    pass


class ShareError(SEHRAError):
    """Raised when share link operations fail."""
    pass


class ValidationError(SEHRAError):
    """Raised when input validation fails."""
    pass
