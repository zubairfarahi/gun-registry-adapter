"""
Model A (Perception Layer) Interface - SOLID Design Pattern.

This interface defines the contract for perception adapters (OCR, image processing).
Follows Open/Closed Principle: Open for extension (new OCR engines), closed for modification.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class OCRResult:
    """
    Normalized OCR output from Model A.

    All Model A implementations must return this standardized format.
    """
    text_fields: Dict[str, str]  # field_name → extracted_text (e.g., {"name": "John Doe", "dob": "1985-03-15"})
    confidence: float  # Overall confidence (0.0-1.0)
    quality_score: float  # Image quality assessment (0.0-1.0)
    tamper_detected: bool  # Whether image shows signs of tampering
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional info (resolution, processing time, etc.)
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate confidence and quality scores are in valid range."""
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")
        if not (0.0 <= self.quality_score <= 1.0):
            raise ValueError(f"Quality score must be 0.0-1.0, got {self.quality_score}")


class PerceptionAdapter(ABC):
    """
    Abstract interface for perception models (Model A).

    All OCR/perception implementations must inherit from this class.
    Enables swapping OCR engines (PaddleOCR, EasyOCR, Tesseract) without changing core logic.
    """

    @abstractmethod
    def extract(self, image_path: str) -> OCRResult:
        """
        Extract structured data from image.

        Args:
            image_path: Path to driver license image

        Returns:
            OCRResult with extracted fields and confidence scores

        Raises:
            OCRFailedError: If extraction fails completely
            LowConfidenceError: If confidence < threshold
            ImageQualityError: If image quality too low
            TamperDetectedError: If tampering detected
        """
        pass

    @abstractmethod
    def validate_quality(self, image_path: str) -> float:
        """
        Assess image quality before OCR.

        Args:
            image_path: Path to image

        Returns:
            Quality score (0.0-1.0), where > 0.7 is acceptable
        """
        pass

    @abstractmethod
    def detect_tampering(self, image_path: str) -> bool:
        """
        Check for image tampering/forgery.

        Uses edge detection, noise analysis, and compression artifacts.

        Args:
            image_path: Path to image

        Returns:
            True if tampering detected, False otherwise
        """
        pass

    @abstractmethod
    def preprocess(self, image_path: str) -> str:
        """
        Preprocess image to enhance OCR accuracy.

        Operations: resize, denoise, contrast enhancement, rotation correction.

        Args:
            image_path: Path to original image

        Returns:
            Path to preprocessed image
        """
        pass
