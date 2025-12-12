"""
Eligibility Engine - Core Orchestrator.

Coordinates Model A (Perception), Model B (Reasoning), and Probabilistic Linkage
to make firearm eligibility decisions.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from adapter.core.model_a.paddleocr_adapter import PaddleOCRAdapter
from adapter.core.model_b.gpt4o_adapter import GPT4oMiniAdapter
from adapter.core.linkage import ProbabilisticLinkageEngine
from adapter.core.interfaces.perception_interface import OCRResult
from adapter.core.interfaces.reasoning_interface import RiskAssessment, LinkageResult
from adapter.config.settings import settings
from adapter.config.logging_config import logger


class EligibilityDecision(str, Enum):
    """Eligibility decision outcomes."""
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    MANUAL_REVIEW = "MANUAL_REVIEW"


@dataclass
class EligibilityResult:
    """
    Complete eligibility assessment result.

    Combines outputs from Model A, Model B, and linkage.
    """
    applicant_id: str
    decision: EligibilityDecision
    confidence: float  # Overall decision confidence (0.0-1.0)

    # Model A (Perception) outputs
    ocr_result: OCRResult
    extracted_data: Dict[str, str]

    # Model B (Reasoning) outputs
    risk_assessment: RiskAssessment

    # Linkage results
    linkage_result: LinkageResult

    # Decision metadata
    requires_manual_review: bool
    decision_rationale: List[str]  # Human-readable reasons for decision
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class EligibilityEngine:
    """
    Core eligibility engine orchestrating all models.

    Pipeline:
    1. Model A: Extract data from ID image (PaddleOCR)
    2. Linkage: Match applicant to NICS records (probabilistic)
    3. Model B: Assess risk (GPT-4o mini)
    4. Decision: Combine all factors to make eligibility decision
    """

    def __init__(
        self,
        perception_adapter: Optional[PaddleOCRAdapter] = None,
        reasoning_adapter: Optional[GPT4oMiniAdapter] = None,
        linkage_engine: Optional[ProbabilisticLinkageEngine] = None,
        nics_records: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Initialize eligibility engine.

        Args:
            perception_adapter: Model A adapter (creates default if None)
            reasoning_adapter: Model B adapter (creates default if None)
            linkage_engine: Linkage engine (creates default if None)
            nics_records: NICS records for linkage (loads from file if None)
        """
        self.perception = perception_adapter or PaddleOCRAdapter()
        self.reasoning = reasoning_adapter or GPT4oMiniAdapter()
        self.linkage = linkage_engine or ProbabilisticLinkageEngine()

        # Load NICS records
        if nics_records is not None:
            self.nics_records = nics_records
        else:
            self.nics_records = self._load_nics_records()

        logger.info(
            "Eligibility engine initialized",
            extra={"num_nics_records": len(self.nics_records)}
        )

    def assess_eligibility(
        self,
        applicant_id: str,
        id_image_path: str
    ) -> EligibilityResult:
        """
        Perform complete eligibility assessment.

        Pipeline:
        1. Extract data from ID (Model A)
        2. Link to NICS records (Probabilistic Linkage)
        3. Assess risk (Model B)
        4. Make decision

        Args:
            applicant_id: Unique applicant identifier
            id_image_path: Path to driver license image

        Returns:
            EligibilityResult with decision and all intermediate outputs
        """
        logger.info(
            "Starting eligibility assessment",
            extra={"applicant_id_hash": self._hash_id(applicant_id)}
        )

        # Step 1: Model A - Extract data from ID
        ocr_result = self.perception.extract(id_image_path)
        extracted_data = ocr_result.text_fields

        logger.info(
            "OCR extraction complete",
            extra={
                "confidence": ocr_result.confidence,
                "fields_extracted": len(extracted_data)
            }
        )

        # Step 2: Probabilistic Linkage
        linkage_result = self.linkage.link(extracted_data, self.nics_records)

        logger.info(
            "Linkage complete",
            extra={
                "matched": linkage_result.matched,
                "confidence": linkage_result.confidence,
                "requires_review": linkage_result.requires_review
            }
        )

        # Step 3: Model B - Risk Assessment
        # Include linkage result in risk assessment data
        applicant_data_with_background = extracted_data.copy()
        if linkage_result.matched and linkage_result.best_match:
            applicant_data_with_background["background_check"] = (
                f"Match found: {linkage_result.best_match.get('outcome', 'Unknown')} "
                f"(confidence: {linkage_result.confidence:.2f})"
            )
        else:
            applicant_data_with_background["background_check"] = "No match found in NICS records"

        risk_assessment = self.reasoning.assess_risk(applicant_data_with_background)

        logger.info(
            "Risk assessment complete",
            extra={
                "risk_score": risk_assessment.risk_score,
                "confidence": risk_assessment.confidence,
                "requires_review": risk_assessment.requires_manual_review
            }
        )

        # Step 4: Make eligibility decision
        decision, confidence, rationale, requires_review = self._make_decision(
            ocr_result=ocr_result,
            risk_assessment=risk_assessment,
            linkage_result=linkage_result,
            extracted_data=extracted_data
        )

        logger.info(
            "Eligibility decision complete",
            extra={
                "decision": decision.value,
                "confidence": confidence,
                "requires_review": requires_review
            }
        )

        return EligibilityResult(
            applicant_id=applicant_id,
            decision=decision,
            confidence=confidence,
            ocr_result=ocr_result,
            extracted_data=extracted_data,
            risk_assessment=risk_assessment,
            linkage_result=linkage_result,
            requires_manual_review=requires_review,
            decision_rationale=rationale,
            timestamp=datetime.now(),
            metadata={
                "model_a_confidence": ocr_result.confidence,
                "model_b_confidence": risk_assessment.confidence,
                "linkage_confidence": linkage_result.confidence
            }
        )

    def _make_decision(
        self,
        ocr_result: OCRResult,
        risk_assessment: RiskAssessment,
        linkage_result: LinkageResult,
        extracted_data: Dict[str, str]
    ) -> tuple[EligibilityDecision, float, List[str], bool]:
        """
        Make final eligibility decision based on all factors.

        Decision Logic:
        1. If OCR confidence < 0.5 → MANUAL_REVIEW
        2. If risk score > 0.7 → DENIED
        3. If linkage matched AND outcome = "denied" → DENIED
        4. If age < 21 → DENIED
        5. If any requires_manual_review flag → MANUAL_REVIEW
        6. Otherwise → APPROVED

        Args:
            ocr_result: Model A OCR result
            risk_assessment: Model B risk assessment
            linkage_result: Probabilistic linkage result
            extracted_data: Extracted applicant data

        Returns:
            (decision, confidence, rationale, requires_manual_review)
        """
        rationale = []
        requires_review = False

        # Calculate overall confidence (weighted average)
        overall_confidence = (
            0.4 * ocr_result.confidence +
            0.4 * risk_assessment.confidence +
            0.2 * linkage_result.confidence
        )

        # Rule 1: Low OCR confidence
        if ocr_result.confidence < 0.5:
            rationale.append(f"OCR confidence too low: {ocr_result.confidence:.2f}")
            return EligibilityDecision.MANUAL_REVIEW, overall_confidence, rationale, True

        # Rule 2: Age eligibility check (must be 21+)
        age = self._calculate_age(extracted_data.get("dob"))
        if age is not None:
            if age < 21:
                rationale.append(f"Age ineligible: {age} years old (must be 21+)")
                return EligibilityDecision.DENIED, overall_confidence, rationale, False
            else:
                rationale.append(f"Age eligible: {age} years old")
        else:
            rationale.append("Age unknown (DOB not extracted)")
            requires_review = True

        # Rule 3: High risk score
        if risk_assessment.risk_score > settings.model_b_risk_threshold:
            rationale.extend(risk_assessment.risk_factors)
            return EligibilityDecision.DENIED, overall_confidence, rationale, False

        # Rule 4: NICS match with denied outcome
        if linkage_result.matched and linkage_result.best_match:
            outcome = linkage_result.best_match.get("outcome", "").lower()
            if outcome == "denied":
                rationale.append(f"Background check failed: denied in NICS records (confidence: {linkage_result.confidence:.2f})")
                return EligibilityDecision.DENIED, overall_confidence, rationale, False
            elif outcome == "approved":
                rationale.append(f"Background check passed (confidence: {linkage_result.confidence:.2f})")
            else:
                rationale.append(f"Background check result unclear: {outcome}")
                requires_review = True

        # Rule 5: Manual review flags
        if risk_assessment.requires_manual_review:
            rationale.append("Risk assessment flagged for manual review")
            requires_review = True

        if linkage_result.requires_review:
            rationale.append("Linkage flagged for manual review (ambiguous match)")
            requires_review = True

        if ocr_result.tamper_detected:
            rationale.append("ID tampering detected")
            return EligibilityDecision.MANUAL_REVIEW, overall_confidence, rationale, True

        # Rule 6: If any manual review flag set
        if requires_review:
            return EligibilityDecision.MANUAL_REVIEW, overall_confidence, rationale, True

        # Rule 7: Default - APPROVED
        rationale.append("All checks passed")
        return EligibilityDecision.APPROVED, overall_confidence, rationale, False

    def _calculate_age(self, dob: Optional[str]) -> Optional[int]:
        """
        Calculate age from date of birth.

        Args:
            dob: Date of birth in YYYY-MM-DD format

        Returns:
            Age in years, or None if DOB invalid
        """
        if not dob:
            return None

        try:
            from datetime import datetime
            dob_date = datetime.strptime(dob, "%Y-%m-%d")
            age = (datetime.now() - dob_date).days // 365
            return age
        except:
            return None

    def _load_nics_records(self) -> List[Dict[str, Any]]:
        """
        Load NICS records from file.

        Returns:
            List of NICS records (or synthetic records)
        """
        import json
        from pathlib import Path

        if settings.use_synthetic_nics:
            # Load synthetic NICS records
            nics_path = Path(settings.synthetic_nics_path)
            if nics_path.exists():
                with open(nics_path, 'r') as f:
                    records = json.load(f)
                logger.info(f"Loaded {len(records)} synthetic NICS records")
                return records
            else:
                logger.warning(f"Synthetic NICS file not found: {nics_path}, using empty list")
                return []
        else:
            logger.warning("Real NICS API integration not implemented, using empty list")
            return []

    def _hash_id(self, applicant_id: str) -> str:
        """Hash applicant ID for privacy-aware logging."""
        import hashlib
        return hashlib.sha256(applicant_id.encode()).hexdigest()[:16]
