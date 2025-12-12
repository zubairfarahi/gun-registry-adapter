"""
Probabilistic Data Linkage Engine.

CRITICAL: Never uses exact matching. Always returns confidence scores.
Implements multi-criteria weighted scoring as specified in requirements.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from adapter.core.interfaces.reasoning_interface import LinkageResult
from adapter.core.model_b.rapidfuzz_matcher import RapidFuzzMatcher
from adapter.exceptions.parser_exceptions import LinkageError, NoMatchFoundError
from adapter.config.settings import settings
from adapter.config.logging_config import logger


class ProbabilisticLinkageEngine:
    """
    Probabilistic linkage between applicant data and NICS records.

    Uses weighted multi-criteria scoring:
    - Name match (fuzzy): 40% weight
    - DOB exact match: 30% weight
    - State match: 20% weight
    - Address match (fuzzy): 10% weight

    Confidence thresholds:
    - >= 0.9: Auto-match (high confidence)
    - 0.7 - 0.9: Probable match, requires manual review
    - < 0.7: No match
    """

    def __init__(self, fuzzy_matcher: Optional[RapidFuzzMatcher] = None):
        """
        Initialize linkage engine.

        Args:
            fuzzy_matcher: FuzzyMatcher instance (creates default if None)
        """
        self.fuzzy_matcher = fuzzy_matcher or RapidFuzzMatcher()
        self.threshold = settings.linkage_confidence_threshold
        self.manual_review_min = settings.linkage_manual_review_min
        self.manual_review_max = settings.linkage_manual_review_max

        logger.info(
            "Probabilistic linkage engine initialized",
            extra={
                "threshold": self.threshold,
                "manual_review_range": f"{self.manual_review_min}-{self.manual_review_max}"
            }
        )

    def link(
        self,
        applicant: Dict[str, Any],
        nics_records: List[Dict[str, Any]]
    ) -> LinkageResult:
        """
        Perform probabilistic linkage between applicant and NICS records.

        NEVER uses exact matching - always returns confidence scores.

        Args:
            applicant: Extracted data from driver license (name, DOB, state, address)
            nics_records: List of NICS individual records (or synthetic)

        Returns:
            LinkageResult with confidence scores and best match

        Raises:
            LinkageError: If linkage process fails
        """
        try:
            if not nics_records:
                logger.warning("No NICS records provided for linkage")
                return LinkageResult(
                    matched=False,
                    confidence=0.0,
                    field_scores={},
                    assumptions=["No NICS records available for matching"],
                    requires_review=False,
                    best_match=None
                )

            best_match = None
            best_score = 0.0
            best_field_scores = {}

            # Iterate through all NICS records
            for record in nics_records:
                field_scores = self._calculate_field_scores(applicant, record)

                # Weighted composite score
                composite_score = (
                    0.4 * field_scores["name"] +
                    0.3 * field_scores["dob"] +
                    0.2 * field_scores["state"] +
                    0.1 * field_scores["address"]
                )

                if composite_score > best_score:
                    best_score = composite_score
                    best_match = record
                    best_field_scores = field_scores

            # Document assumptions
            assumptions = self._document_assumptions(applicant, best_match, best_field_scores)

            # Determine if match found
            matched = best_score >= self.threshold

            # Determine if manual review required
            requires_review = (
                self.manual_review_min <= best_score < self.manual_review_max
            ) or (
                len([r for r in nics_records if self._calculate_field_scores(applicant, r)["name"] > 0.8]) > 1
            )

            logger.info(
                "Linkage complete",
                extra={
                    "matched": matched,
                    "confidence": best_score,
                    "requires_review": requires_review,
                    "num_records_searched": len(nics_records)
                }
            )

            return LinkageResult(
                matched=matched,
                confidence=best_score,
                field_scores=best_field_scores,
                assumptions=assumptions,
                requires_review=requires_review,
                best_match=best_match if matched else None,
                metadata={
                    "num_records_searched": len(nics_records),
                    "threshold": self.threshold
                },
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Linkage failed: {e}", exc_info=True)
            raise LinkageError(f"Linkage failed: {str(e)}")

    def _calculate_field_scores(
        self,
        applicant: Dict[str, Any],
        record: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate per-field match scores.

        Args:
            applicant: Applicant data
            record: NICS record

        Returns:
            Dictionary of field scores (0.0-1.0)
        """
        scores = {}

        # 1. Name fuzzy match (40% weight)
        applicant_name = applicant.get("name", "").strip()
        record_name = record.get("name", "").strip()

        if applicant_name and record_name:
            scores["name"] = self.fuzzy_matcher.match_score(applicant_name, record_name)
        else:
            scores["name"] = 0.0

        # 2. DOB exact match (30% weight)
        applicant_dob = applicant.get("dob", "").strip()
        record_dob = record.get("dob", "").strip()

        if applicant_dob and record_dob:
            # Exact match only (no fuzzy matching on dates for safety)
            scores["dob"] = 1.0 if applicant_dob == record_dob else 0.0
        else:
            scores["dob"] = 0.0

        # 3. State exact match (20% weight)
        applicant_state = applicant.get("state", "").strip().upper()
        record_state = record.get("state", "").strip().upper()

        if applicant_state and record_state:
            scores["state"] = 1.0 if applicant_state == record_state else 0.0
        else:
            scores["state"] = 0.0

        # 4. Address fuzzy match (10% weight)
        applicant_address = applicant.get("address", "").strip()
        record_address = record.get("address", "").strip()

        if applicant_address and record_address:
            # Use partial ratio (addresses may have different formatting)
            scores["address"] = self.fuzzy_matcher.match_score_partial(applicant_address, record_address)
        else:
            scores["address"] = 0.0

        return scores

    def _document_assumptions(
        self,
        applicant: Dict[str, Any],
        record: Optional[Dict[str, Any]],
        field_scores: Dict[str, float]
    ) -> List[str]:
        """
        Document assumptions made during linkage.

        Args:
            applicant: Applicant data
            record: Matched NICS record (or None)
            field_scores: Per-field scores

        Returns:
            List of assumption statements
        """
        assumptions = [
            "Name matching uses token_set_ratio to handle word order variations (e.g., 'John Doe' vs 'Doe, John')",
            "DOB requires exact match (no fuzzy matching on dates for safety)",
            f"Confidence threshold set at {self.threshold} (configurable via LINKAGE_CONFIDENCE_THRESHOLD env var)",
            "Weights: name=40%, DOB=30%, state=20%, address=10% (tunable based on field reliability)"
        ]

        # Document missing fields
        missing_fields = []
        if not applicant.get("name"):
            missing_fields.append("name (applicant)")
        if not applicant.get("dob"):
            missing_fields.append("DOB (applicant)")
        if not applicant.get("state"):
            missing_fields.append("state (applicant)")
        if not applicant.get("address"):
            missing_fields.append("address (applicant)")

        if record:
            if not record.get("name"):
                missing_fields.append("name (NICS record)")
            if not record.get("dob"):
                missing_fields.append("DOB (NICS record)")
            if not record.get("state"):
                missing_fields.append("state (NICS record)")
            if not record.get("address"):
                missing_fields.append("address (NICS record)")

        if missing_fields:
            assumptions.append(f"Missing fields (scored as 0.0): {', '.join(missing_fields)}")

        # Document field-specific notes
        if field_scores.get("name", 0) < 0.5:
            assumptions.append("Low name match score - possible name variation or different person")

        if field_scores.get("dob", 0) == 0.0 and applicant.get("dob") and record and record.get("dob"):
            assumptions.append(f"DOB mismatch: applicant DOB does not match NICS record")

        return assumptions
