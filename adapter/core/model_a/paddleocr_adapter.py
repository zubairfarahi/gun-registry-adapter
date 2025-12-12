"""
Model A: PaddleOCR Perception Adapter.

Extracts structured data from driver license images using PaddleOCR.
Implements PerceptionAdapter interface (Open/Closed Principle).
"""

import cv2
import numpy as np
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import re

from adapter.core.interfaces.perception_interface import PerceptionAdapter, OCRResult
from adapter.exceptions.parser_exceptions import (
    OCRFailedError,
    LowConfidenceError,
    ImageQualityError,
    TamperDetectedError
)
from adapter.config.settings import settings
from adapter.config.logging_config import logger


class PaddleOCRAdapter(PerceptionAdapter):
    """
    PaddleOCR implementation of PerceptionAdapter.

    Extracts text from driver license images with confidence scores.
    """

    def __init__(self, confidence_threshold: float = None):
        """
        Initialize PaddleOCR adapter.

        Args:
            confidence_threshold: Minimum OCR confidence (0.0-1.0). Uses settings if None.
        """
        try:
            from paddleocr import PaddleOCR
            self.ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
        except ImportError:
            raise ImportError(
                "PaddleOCR not installed. Run: pip install paddleocr"
            )

        self.confidence_threshold = confidence_threshold or settings.model_a_confidence_threshold

        logger.info(
            "PaddleOCR adapter initialized",
            extra={"confidence_threshold": self.confidence_threshold}
        )

    def extract(self, image_path: str) -> OCRResult:
        """
        Extract text using PaddleOCR with preprocessing.

        Pipeline:
        1. Validate image quality
        2. Check for tampering
        3. Preprocess image (enhance, denoise)
        4. Run OCR
        5. Parse into structured fields
        6. Calculate confidence

        Args:
            image_path: Path to driver license image

        Returns:
            OCRResult with extracted fields and confidence

        Raises:
            ImageQualityError: If quality too low
            TamperDetectedError: If tampering detected (and enabled)
            LowConfidenceError: If OCR confidence below threshold
            OCRFailedError: If extraction fails completely
        """
        try:
            # 1. Validate quality
            quality = self.validate_quality(image_path)
            if quality < settings.image_quality_threshold:
                raise ImageQualityError(
                    f"Image quality too low: {quality:.2f} < {settings.image_quality_threshold}",
                    quality_score=quality
                )

            # 2. Check tampering
            if settings.enable_tamper_detection:
                tamper_detected = self.detect_tampering(image_path)
                if tamper_detected:
                    raise TamperDetectedError(
                        "Image tampering detected",
                        tamper_indicators=["edge_discontinuities", "noise_anomalies"]
                    )
            else:
                tamper_detected = False

            # 3. Preprocess
            preprocessed_path = self.preprocess(image_path)

            # 4. Run OCR
            logger.info(f"Running OCR on image", extra={"image_path": Path(image_path).name})
            result = self.ocr.ocr(preprocessed_path, cls=True)

            if not result or not result[0]:
                raise OCRFailedError(
                    "OCR returned no results",
                    image_path=image_path,
                    confidence=0.0
                )

            # 5. Parse structured fields
            text_fields = self._parse_driver_license(result[0])

            # 6. Calculate overall confidence
            confidences = [line[1][1] for line in result[0]]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            if avg_confidence < self.confidence_threshold:
                raise LowConfidenceError(
                    f"OCR confidence too low: {avg_confidence:.2f} < {self.confidence_threshold}",
                    confidence=avg_confidence,
                    threshold=self.confidence_threshold
                )

            logger.info(
                "OCR extraction successful",
                extra={
                    "confidence": avg_confidence,
                    "quality": quality,
                    "fields_extracted": len(text_fields)
                }
            )

            return OCRResult(
                text_fields=text_fields,
                confidence=avg_confidence,
                quality_score=quality,
                tamper_detected=tamper_detected,
                metadata={
                    "num_text_blocks": len(result[0]),
                    "image_path": str(Path(image_path).name),
                    "preprocessed": True
                },
                timestamp=datetime.now()
            )

        except (ImageQualityError, TamperDetectedError, LowConfidenceError):
            # Re-raise known errors
            raise
        except Exception as e:
            logger.error(
                "OCR extraction failed",
                extra={"error": str(e), "image_path": Path(image_path).name},
                exc_info=True
            )
            raise OCRFailedError(
                f"OCR extraction failed: {str(e)}",
                image_path=image_path,
                confidence=0.0
            )

    def validate_quality(self, image_path: str) -> float:
        """
        Assess image quality using blur detection and contrast analysis.

        Args:
            image_path: Path to image

        Returns:
            Quality score (0.0-1.0)
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                return 0.0

            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 1. Blur detection (Laplacian variance)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            # Normalize: higher variance = sharper image
            blur_score = min(laplacian_var / 1000.0, 1.0)  # Typical sharp images have var > 500

            # 2. Contrast analysis
            contrast = gray.std() / 128.0  # Normalize by half of grayscale range
            contrast_score = min(contrast, 1.0)

            # 3. Brightness (avoid over/under exposure)
            brightness = gray.mean() / 255.0
            # Ideal brightness: 0.3-0.7 range
            if 0.3 <= brightness <= 0.7:
                brightness_score = 1.0
            else:
                brightness_score = max(0.0, 1.0 - abs(brightness - 0.5) * 2)

            # Weighted average
            quality = (
                0.5 * blur_score +
                0.3 * contrast_score +
                0.2 * brightness_score
            )

            return quality

        except Exception as e:
            logger.warning(f"Quality validation failed: {e}")
            return 0.0

    def detect_tampering(self, image_path: str) -> bool:
        """
        Detect image tampering using edge analysis and noise detection.

        Basic tampering detection - production would use more sophisticated methods.

        Args:
            image_path: Path to image

        Returns:
            True if tampering detected
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                return False

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 1. Edge discontinuities (tampered images often have irregular edges)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size

            # Typical driver licenses have consistent edge density (0.05-0.15)
            if edge_density < 0.02 or edge_density > 0.25:
                logger.warning(f"Suspicious edge density: {edge_density:.3f}")
                return True

            # 2. Noise analysis (JPEG compression artifacts)
            # Compute noise level using high-frequency component
            fft = np.fft.fft2(gray)
            fft_shift = np.fft.fftshift(fft)
            magnitude = np.abs(fft_shift)

            # High noise in specific frequency bands indicates tampering
            high_freq_noise = np.mean(magnitude[magnitude.shape[0]//4:3*magnitude.shape[0]//4,
                                               magnitude.shape[1]//4:3*magnitude.shape[1]//4])

            # Threshold increased to 50000 to avoid false positives on compressed images
            if high_freq_noise > 50000:  # Threshold tuned for synthetic/compressed images
                logger.warning(f"Suspicious high-frequency noise: {high_freq_noise:.1f}")
                return True

            return False

        except Exception as e:
            logger.warning(f"Tamper detection failed: {e}")
            return False  # Fail open (don't reject image on detection failure)

    def preprocess(self, image_path: str) -> str:
        """
        Preprocess image to enhance OCR accuracy.

        Operations:
        - Resize to standard dimensions
        - Denoise
        - Contrast enhancement (CLAHE)
        - Rotation correction

        Args:
            image_path: Path to original image

        Returns:
            Path to preprocessed image
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                return image_path  # Return original if preprocessing fails

            # 1. Denoise
            denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)

            # 2. Convert to grayscale for processing
            gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)

            # 3. Contrast enhancement (CLAHE - Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # 4. Rotation correction (basic - check if text is rotated)
            # This is simplified - production would use more sophisticated deskewing

            # 5. Resize to standard dimensions (if too small)
            height, width = enhanced.shape
            if width < 800 or height < 600:
                scale = max(800 / width, 600 / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                enhanced = cv2.resize(enhanced, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

            # Save preprocessed image
            preprocessed_path = str(Path(image_path).with_suffix('.preprocessed.png'))
            cv2.imwrite(preprocessed_path, enhanced)

            return preprocessed_path

        except Exception as e:
            logger.warning(f"Preprocessing failed: {e}, using original image")
            return image_path

    def _parse_driver_license(self, ocr_result: list) -> Dict[str, str]:
        """
        Parse OCR output into structured driver license fields.

        Args:
            ocr_result: Raw PaddleOCR output

        Returns:
            Dictionary of structured fields (name, dob, state, license_number, address)
        """
        fields = {}

        # Extract all text blocks
        text_blocks = [line[1][0] for line in ocr_result]
        full_text = " ".join(text_blocks)

        # 1. Extract name (heuristic: look for "NAME" keyword or typical name patterns)
        name_match = re.search(r'(?:NAME|LN)\s*[:;]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', full_text, re.IGNORECASE)
        if name_match:
            fields["name"] = name_match.group(1).strip()
        else:
            # Fallback: first capitalized multi-word phrase
            name_fallback = re.search(r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', full_text)
            if name_fallback:
                fields["name"] = name_fallback.group(1).strip()

        # 2. Extract DOB (common formats: MM/DD/YYYY, YYYY-MM-DD)
        dob_match = re.search(r'(?:DOB|DATE OF BIRTH)\s*[:;]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{4}-\d{2}-\d{2})', full_text, re.IGNORECASE)
        if dob_match:
            dob = dob_match.group(1).strip()
            # Normalize to YYYY-MM-DD
            fields["dob"] = self._normalize_date(dob)
        else:
            # Fallback: any date pattern
            dob_fallback = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{4}-\d{2}-\d{2})', full_text)
            if dob_fallback:
                fields["dob"] = self._normalize_date(dob_fallback.group(1).strip())

        # 3. Extract state (2-letter abbreviation)
        state_match = re.search(r'\b([A-Z]{2})\b', full_text)
        if state_match:
            fields["state"] = state_match.group(1)

        # 4. Extract license number (alphanumeric, typically 8-12 characters)
        license_match = re.search(r'(?:DL|LIC|LICENSE)\s*#?\s*[:;]?\s*([A-Z0-9]{6,15})', full_text, re.IGNORECASE)
        if license_match:
            fields["license_number"] = license_match.group(1).strip()
        else:
            # Fallback: any alphanumeric sequence 8-12 chars
            license_fallback = re.search(r'\b([A-Z0-9]{8,12})\b', full_text)
            if license_fallback:
                fields["license_number"] = license_fallback.group(1).strip()

        # 5. Extract address (this is challenging - use multi-line heuristic)
        address_match = re.search(r'(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way)[,\s]+[A-Za-z\s]+,?\s*[A-Z]{2}\s+\d{5})', full_text, re.IGNORECASE)
        if address_match:
            fields["address"] = address_match.group(1).strip()

        return fields

    def _normalize_date(self, date_str: str) -> str:
        """
        Normalize date to YYYY-MM-DD format.

        Args:
            date_str: Date in various formats (MM/DD/YYYY, M/D/YYYY, YYYY-MM-DD)

        Returns:
            Date in YYYY-MM-DD format
        """
        from datetime import datetime

        # Try common formats
        formats = [
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d/%m/%Y",  # European format
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # If all formats fail, return original
        return date_str
