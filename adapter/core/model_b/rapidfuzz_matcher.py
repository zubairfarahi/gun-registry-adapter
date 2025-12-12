"""
RapidFuzz-based Fuzzy Matcher for Probabilistic Linkage.

Implements FuzzyMatcher interface for name matching across datasets.
"""

from typing import List, Tuple
from rapidfuzz import fuzz, process

from adapter.core.interfaces.reasoning_interface import FuzzyMatcher
from adapter.exceptions.parser_exceptions import FuzzyMatchAmbiguousError
from adapter.config.logging_config import logger


class RapidFuzzMatcher(FuzzyMatcher):
    """
    RapidFuzz implementation for fuzzy string matching.

    Uses multiple matching algorithms:
    - Token Set Ratio: Handles word order variations ("John Doe" vs "Doe, John")
    - Partial Ratio: Handles substrings
    - Levenshtein Distance: Handles typos
    """

    def __init__(self, ambiguity_threshold: int = 10):
        """
        Initialize RapidFuzz matcher.

        Args:
            ambiguity_threshold: Max number of high-confidence matches before flagging ambiguity
        """
        self.ambiguity_threshold = ambiguity_threshold
        logger.info(f"RapidFuzz matcher initialized with ambiguity_threshold={ambiguity_threshold}")

    def fuzzy_match(
        self,
        query: str,
        candidates: List[str],
        threshold: float = 0.7
    ) -> List[Tuple[str, float]]:
        """
        Perform fuzzy matching with confidence scores.

        Uses token_set_ratio algorithm (best for name matching).

        Args:
            query: String to match (e.g., applicant name)
            candidates: List of candidate strings (e.g., names from NICS dataset)
            threshold: Minimum confidence to include in results (0.0-1.0)

        Returns:
            List of (candidate, confidence) tuples, sorted by confidence desc

        Raises:
            FuzzyMatchAmbiguousError: If too many high-confidence matches
        """
        if not query or not candidates:
            return []

        # Use token_set_ratio for robust name matching
        matches = []
        for candidate in candidates:
            score = fuzz.token_set_ratio(query.lower(), candidate.lower()) / 100.0
            if score >= threshold:
                matches.append((candidate, score))

        # Sort by confidence descending
        matches.sort(key=lambda x: x[1], reverse=True)

        # Check for ambiguity (too many high-confidence matches)
        high_confidence_matches = [m for m in matches if m[1] > 0.8]
        if len(high_confidence_matches) > self.ambiguity_threshold:
            logger.warning(
                f"Ambiguous fuzzy match: {len(high_confidence_matches)} candidates > {self.ambiguity_threshold}",
                extra={"query": query, "num_matches": len(high_confidence_matches)}
            )
            raise FuzzyMatchAmbiguousError(
                f"Too many ambiguous matches: {len(high_confidence_matches)} candidates with confidence > 0.8",
                candidates=[m[0] for m in high_confidence_matches],
                confidences=[m[1] for m in high_confidence_matches]
            )

        logger.info(
            f"Fuzzy match found {len(matches)} results",
            extra={"query": query, "num_results": len(matches), "threshold": threshold}
        )

        return matches

    def match_score(self, str1: str, str2: str) -> float:
        """
        Calculate match score between two strings.

        Uses token_set_ratio for consistency with fuzzy_match.

        Args:
            str1: First string
            str2: Second string

        Returns:
            Match confidence (0.0-1.0)
        """
        if not str1 or not str2:
            return 0.0

        score = fuzz.token_set_ratio(str1.lower(), str2.lower()) / 100.0
        return score

    def match_score_partial(self, str1: str, str2: str) -> float:
        """
        Calculate partial match score (for addresses, partial names).

        Args:
            str1: First string
            str2: Second string

        Returns:
            Match confidence (0.0-1.0)
        """
        if not str1 or not str2:
            return 0.0

        score = fuzz.partial_ratio(str1.lower(), str2.lower()) / 100.0
        return score

    def match_score_levenshtein(self, str1: str, str2: str) -> float:
        """
        Calculate Levenshtein distance-based score (typo handling).

        Args:
            str1: First string
            str2: Second string

        Returns:
            Match confidence (0.0-1.0)
        """
        if not str1 or not str2:
            return 0.0

        score = fuzz.ratio(str1.lower(), str2.lower()) / 100.0
        return score
