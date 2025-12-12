"""
Unit Tests for Probabilistic Linkage Engine.

Tests the core linkage logic that matches applicants to NICS records.
"""

import pytest
from adapter.core.linkage import ProbabilisticLinkageEngine
from adapter.core.model_b.rapidfuzz_matcher import RapidFuzzMatcher


class TestProbabilisticLinkageEngine:
    """Test suite for probabilistic linkage."""

    @pytest.fixture
    def linkage_engine(self):
        """Create linkage engine instance."""
        return ProbabilisticLinkageEngine()

    @pytest.fixture
    def sample_applicant(self):
        """Sample applicant data."""
        return {
            "name": "John Michael Doe",
            "dob": "1985-03-15",
            "state": "FL",
            "address": "123 Main St, Miami, FL 33101"
        }

    @pytest.fixture
    def sample_nics_records(self):
        """Sample NICS records for testing."""
        return [
            {
                "name": "John M. Doe",  # Slightly different format
                "dob": "1985-03-15",  # Exact match
                "state": "FL",
                "address": "123 Main Street, Miami, FL 33101",  # Different formatting
                "outcome": "approved"
            },
            {
                "name": "Jane Smith",
                "dob": "1990-05-20",
                "state": "CA",
                "address": "456 Oak Ave, Los Angeles, CA 90001",
                "outcome": "denied"
            },
            {
                "name": "Robert Johnson",
                "dob": "1975-12-01",
                "state": "TX",
                "address": "789 Pine Rd, Houston, TX 77001",
                "outcome": "approved"
            }
        ]

    def test_exact_match_high_confidence(self, linkage_engine, sample_applicant, sample_nics_records):
        """Test linkage with near-exact match returns high confidence."""
        result = linkage_engine.link(sample_applicant, sample_nics_records)

        # Should match first record (John Doe)
        assert result.matched is True
        assert result.confidence > 0.8  # High confidence due to name fuzzy match + exact DOB
        assert result.best_match is not None
        assert result.best_match["name"] == "John M. Doe"
        assert result.requires_review is False  # High confidence, no review needed

    def test_no_match_low_confidence(self, linkage_engine, sample_nics_records):
        """Test linkage with no good match returns low confidence."""
        # Completely different applicant
        different_applicant = {
            "name": "Alice Williams",
            "dob": "2000-01-01",
            "state": "NY",
            "address": "999 Broadway, New York, NY 10001"
        }

        result = linkage_engine.link(different_applicant, sample_nics_records)

        assert result.matched is False  # Confidence below threshold
        assert result.confidence < 0.7  # Low confidence
        assert result.best_match is None

    def test_fuzzy_name_matching(self, linkage_engine, sample_nics_records):
        """Test fuzzy name matching handles variations."""
        # Different name format
        applicant = {
            "name": "Doe, John Michael",  # Last name first
            "dob": "1985-03-15",
            "state": "FL",
            "address": "123 Main St, Miami, FL 33101"
        }

        result = linkage_engine.link(applicant, sample_nics_records)

        # Should still match due to fuzzy matching (token_set_ratio handles word order)
        assert result.matched is True
        assert result.field_scores["name"] > 0.8  # High name similarity

    def test_dob_exact_match_only(self, linkage_engine, sample_nics_records):
        """Test DOB requires exact match (no fuzzy matching on dates)."""
        # Same name, different DOB
        applicant = {
            "name": "John M. Doe",
            "dob": "1985-03-16",  # Off by 1 day
            "state": "FL",
            "address": "123 Main St, Miami, FL 33101"
        }

        result = linkage_engine.link(applicant, sample_nics_records)

        # DOB field score should be 0.0 (no fuzzy matching)
        assert result.field_scores["dob"] == 0.0

    def test_manual_review_threshold(self, linkage_engine, sample_nics_records):
        """Test manual review flag for medium confidence."""
        # Partial match (name similar, but different state)
        applicant = {
            "name": "John M. Doe",
            "dob": "1985-03-15",
            "state": "CA",  # Different state
            "address": "Different address"
        }

        result = linkage_engine.link(applicant, sample_nics_records)

        # Might fall into manual review range (0.7-0.9)
        if 0.7 <= result.confidence < 0.9:
            assert result.requires_review is True

    def test_empty_nics_records(self, linkage_engine, sample_applicant):
        """Test linkage with no NICS records."""
        result = linkage_engine.link(sample_applicant, [])

        assert result.matched is False
        assert result.confidence == 0.0
        assert result.best_match is None
        assert "No NICS records available" in result.assumptions[0]

    def test_field_scores_calculated(self, linkage_engine, sample_applicant, sample_nics_records):
        """Test per-field scores are calculated correctly."""
        result = linkage_engine.link(sample_applicant, sample_nics_records)

        # Check all field scores present
        assert "name" in result.field_scores
        assert "dob" in result.field_scores
        assert "state" in result.field_scores
        assert "address" in result.field_scores

        # All scores should be in valid range
        for field, score in result.field_scores.items():
            assert 0.0 <= score <= 1.0

    def test_assumptions_documented(self, linkage_engine, sample_applicant, sample_nics_records):
        """Test assumptions are documented in result."""
        result = linkage_engine.link(sample_applicant, sample_nics_records)

        assert len(result.assumptions) > 0
        # Should document matching algorithm
        assert any("token_set_ratio" in assumption for assumption in result.assumptions)
        # Should document threshold
        assert any("threshold" in assumption.lower() for assumption in result.assumptions)


class TestRapidFuzzMatcher:
    """Test suite for RapidFuzz fuzzy matcher."""

    @pytest.fixture
    def matcher(self):
        """Create fuzzy matcher instance."""
        return RapidFuzzMatcher()

    def test_exact_match_high_score(self, matcher):
        """Test exact match returns score of 1.0."""
        score = matcher.match_score("John Doe", "John Doe")
        assert score == 1.0

    def test_case_insensitive(self, matcher):
        """Test matching is case-insensitive."""
        score = matcher.match_score("John Doe", "JOHN DOE")
        assert score == 1.0

    def test_word_order_insensitive(self, matcher):
        """Test token_set_ratio handles word order."""
        score = matcher.match_score("John Doe", "Doe, John")
        assert score > 0.9  # Should be very high

    def test_typo_tolerance(self, matcher):
        """Test fuzzy matching tolerates typos."""
        score = matcher.match_score("John Doe", "Jon Doe")  # Typo in first name
        assert score > 0.8  # Should still match well

    def test_fuzzy_match_threshold(self, matcher):
        """Test fuzzy_match filters by threshold."""
        candidates = [
            "John Doe",
            "John Smith",
            "Jane Doe",
            "Bob Johnson"
        ]

        matches = matcher.fuzzy_match("John Doe", candidates, threshold=0.7)

        # Should only return high-confidence matches
        assert len(matches) >= 1
        assert all(confidence >= 0.7 for _, confidence in matches)
        # Results should be sorted by confidence
        confidences = [conf for _, conf in matches]
        assert confidences == sorted(confidences, reverse=True)
