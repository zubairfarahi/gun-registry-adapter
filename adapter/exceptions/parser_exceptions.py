"""
Custom exceptions for Gun Registry Adapter.

These exceptions enable Model C self-healing by providing structured error context.
"""


class GunRegistryAdapterError(Exception):
    """Base exception for all adapter errors."""
    pass


# ============================================================================
# Model A (Perception) Exceptions
# ============================================================================

class PerceptionError(GunRegistryAdapterError):
    """Base exception for Model A perception errors."""
    pass


class OCRFailedError(PerceptionError):
    """OCR extraction completely failed."""
    def __init__(self, message: str, image_path: str = None, confidence: float = 0.0):
        super().__init__(message)
        self.image_path = image_path
        self.confidence = confidence


class LowConfidenceError(PerceptionError):
    """OCR confidence below threshold."""
    def __init__(self, message: str, confidence: float, threshold: float):
        super().__init__(message)
        self.confidence = confidence
        self.threshold = threshold


class ImageQualityError(PerceptionError):
    """Image quality too low for OCR processing."""
    def __init__(self, message: str, quality_score: float):
        super().__init__(message)
        self.quality_score = quality_score


class TamperDetectedError(PerceptionError):
    """Image tampering detected."""
    def __init__(self, message: str, tamper_indicators: list = None):
        super().__init__(message)
        self.tamper_indicators = tamper_indicators or []


# ============================================================================
# Model B (Reasoning) Exceptions
# ============================================================================

class ReasoningError(GunRegistryAdapterError):
    """Base exception for Model B reasoning errors."""
    pass


class FuzzyMatchAmbiguousError(ReasoningError):
    """Multiple ambiguous matches found during fuzzy matching."""
    def __init__(self, message: str, candidates: list, confidences: list):
        super().__init__(message)
        self.candidates = candidates
        self.confidences = confidences


class RiskAssessmentError(ReasoningError):
    """Error during risk assessment calculation."""
    pass


class APITimeoutError(ReasoningError):
    """External API (OpenAI/Claude) timeout."""
    def __init__(self, message: str, api_name: str, timeout_seconds: int):
        super().__init__(message)
        self.api_name = api_name
        self.timeout_seconds = timeout_seconds


# ============================================================================
# Linkage Exceptions
# ============================================================================

class LinkageError(GunRegistryAdapterError):
    """Base exception for linkage errors."""
    pass


class NoMatchFoundError(LinkageError):
    """No match found in linkage attempt."""
    def __init__(self, message: str, best_confidence: float):
        super().__init__(message)
        self.best_confidence = best_confidence


# ============================================================================
# Validation Exceptions
# ============================================================================

class ValidationError(GunRegistryAdapterError):
    """Data validation error."""
    pass


class SchemaValidationError(ValidationError):
    """Schema validation failed."""
    def __init__(self, message: str, field: str, constraint: str):
        super().__init__(message)
        self.field = field
        self.constraint = constraint


# ============================================================================
# Self-Healing Exceptions
# ============================================================================

class SelfHealingError(GunRegistryAdapterError):
    """Error during self-healing process."""
    pass


class FixValidationFailedError(SelfHealingError):
    """Proposed fix failed validation."""
    def __init__(self, message: str, fix_code: str, validation_errors: list):
        super().__init__(message)
        self.fix_code = fix_code
        self.validation_errors = validation_errors


class UnsupportedErrorCategoryError(SelfHealingError):
    """Error category not supported for self-healing."""
    def __init__(self, message: str, error_category: str):
        super().__init__(message)
        self.error_category = error_category
