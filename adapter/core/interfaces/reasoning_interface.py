"""
Model B (Reasoning Layer) Interface - Strategy Pattern.

Handles risk assessment, fuzzy matching, and semantic analysis.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RiskAssessment:
    """
    Risk scoring output from Model B.

    All risk assessments must be probabilistic (confidence scores), never binary.
    """
    risk_score: float  # 0.0 (low risk) to 1.0 (high risk)
    risk_factors: List[str]  # Human-readable reasons (e.g., ["Criminal record match", "Age < 21"])
    confidence: float  # Model confidence in assessment (0.0-1.0)
    requires_manual_review: bool  # True if confidence < 0.7 or ambiguous
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate risk score and confidence are in valid range."""
        if not (0.0 <= self.risk_score <= 1.0):
            raise ValueError(f"Risk score must be 0.0-1.0, got {self.risk_score}")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")


@dataclass
class LinkageResult:
    """
    Result of probabilistic data linkage.

    CRITICAL: Never use exact matching. Always return confidence scores.
    """
    matched: bool  # Confidence >= threshold
    confidence: float  # Overall confidence (0.0-1.0)
    field_scores: Dict[str, float]  # Per-field match scores (e.g., {"name": 0.95, "dob": 1.0})
    assumptions: List[str]  # Documented assumptions for this linkage
    requires_review: bool  # True if 0.7 <= confidence < 0.9
    best_match: Optional[Dict[str, Any]] = None  # Best matching record (if any)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate confidence is in valid range."""
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")

        # Validate field scores
        for field, score in self.field_scores.items():
            if not (0.0 <= score <= 1.0):
                raise ValueError(f"Field score for '{field}' must be 0.0-1.0, got {score}")


class ReasoningAdapter(ABC):
    """
    Abstract interface for reasoning models (Model B).

    Handles semantic analysis, risk scoring, and fuzzy matching.
    """

    @abstractmethod
    def assess_risk(self, applicant_data: Dict[str, Any]) -> RiskAssessment:
        """
        Calculate risk score for applicant.

        Args:
            applicant_data: Extracted data from Model A (name, DOB, address, etc.)

        Returns:
            RiskAssessment with score, factors, and confidence

        Raises:
            RiskAssessmentError: If risk calculation fails
            APITimeoutError: If external API times out
        """
        pass

    @abstractmethod
    def interpret_text(self, text: str, context: str) -> Dict[str, Any]:
        """
        Interpret ambiguous or unclear text using semantic analysis.

        Example: Classify denial reasons, interpret unclear state abbreviations.

        Args:
            text: Text to interpret
            context: Context for interpretation (e.g., "state_abbreviation", "denial_reason")

        Returns:
            Interpreted result with confidence
        """
        pass


class FuzzyMatcher(ABC):
    """
    Abstract interface for fuzzy string matching.

    Used for probabilistic linkage across datasets with typos/variations.
    """

    @abstractmethod
    def fuzzy_match(self, query: str, candidates: List[str], threshold: float = 0.7) -> List[Tuple[str, float]]:
        """
        Perform fuzzy matching with confidence scores.

        Args:
            query: String to match (e.g., applicant name)
            candidates: List of candidate strings (e.g., names from NICS dataset)
            threshold: Minimum confidence to include in results

        Returns:
            List of (candidate, confidence) tuples, sorted by confidence desc

        Raises:
            FuzzyMatchAmbiguousError: If multiple high-confidence matches (>10 candidates > 0.8)
        """
        pass

    @abstractmethod
    def match_score(self, str1: str, str2: str) -> float:
        """
        Calculate match score between two strings.

        Args:
            str1: First string
            str2: Second string

        Returns:
            Match confidence (0.0-1.0)
        """
        pass
