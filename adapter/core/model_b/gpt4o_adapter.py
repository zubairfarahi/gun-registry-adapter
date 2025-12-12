"""
Model B: GPT-4o Mini Reasoning Adapter.

Uses OpenAI GPT-4o mini for semantic analysis and risk assessment.
Implements ReasoningAdapter interface.
"""

import json
from typing import Dict, List, Any
from datetime import datetime

from adapter.core.interfaces.reasoning_interface import ReasoningAdapter, RiskAssessment
from adapter.exceptions.parser_exceptions import RiskAssessmentError, APITimeoutError
from adapter.config.settings import settings
from adapter.config.logging_config import logger
from adapter.prompts.risk_assessment_prompts import (
    generate_risk_assessment_prompt,
    generate_text_interpretation_prompt,
    ROLE_RISK_EXPERT,
)


class GPT4oMiniAdapter(ReasoningAdapter):
    """
    GPT-4o mini implementation for semantic analysis and risk assessment.

    Uses structured JSON output for deterministic, parseable responses.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize GPT-4o mini adapter.

        Args:
            api_key: OpenAI API key (uses settings if None)
        """
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key or settings.openai_api_key)
        except ImportError:
            raise ImportError("OpenAI SDK not installed. Run: pip install openai")

        self.model = settings.openai_model
        self.temperature = settings.openai_temperature
        self.max_tokens = settings.openai_max_tokens

        logger.info(
            "GPT-4o mini adapter initialized",
            extra={"model": self.model, "temperature": self.temperature}
        )

    def assess_risk(self, applicant_data: Dict[str, Any]) -> RiskAssessment:
        """
        Calculate risk score using GPT-4o mini.

        Analyzes:
        - Age eligibility (must be 21+)
        - Background check matches
        - Address stability
        - License validity

        Args:
            applicant_data: Extracted data from Model A

        Returns:
            RiskAssessment with score, factors, and confidence

        Raises:
            RiskAssessmentError: If risk calculation fails
            APITimeoutError: If OpenAI API times out
        """
        try:
            # Generate prompt using structured prompt template
            prompt = generate_risk_assessment_prompt(applicant_data)

            logger.info("Calling OpenAI API for risk assessment")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=settings.api_request_timeout
            )

            # Parse JSON response
            response_text = response.choices[0].message.content
            risk_data = self._parse_risk_response(response_text)

            logger.info(
                "Risk assessment complete",
                extra={
                    "risk_score": risk_data["risk_score"],
                    "num_factors": len(risk_data["risk_factors"]),
                    "requires_review": risk_data["requires_manual_review"]
                }
            )

            return RiskAssessment(
                risk_score=risk_data["risk_score"],
                risk_factors=risk_data["risk_factors"],
                confidence=risk_data["confidence"],
                requires_manual_review=risk_data["requires_manual_review"],
                metadata={
                    "model": self.model,
                    "tokens_used": response.usage.total_tokens
                },
                timestamp=datetime.now()
            )

        except TimeoutError as e:
            raise APITimeoutError(
                f"OpenAI API timeout after {settings.api_request_timeout}s",
                api_name="OpenAI",
                timeout_seconds=settings.api_request_timeout
            )
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}", exc_info=True)
            raise RiskAssessmentError(f"Risk assessment failed: {str(e)}")

    def interpret_text(self, text: str, context: str) -> Dict[str, Any]:
        """
        Interpret ambiguous text using semantic analysis.

        Use cases:
        - Unclear state abbreviations
        - Denial reason classification
        - Name disambiguation

        Args:
            text: Text to interpret
            context: Context hint (e.g., "state_abbreviation", "denial_reason")

        Returns:
            Interpreted result with confidence
        """
        try:
            # Generate prompt using structured prompt template
            prompt = generate_text_interpretation_prompt(text, context)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=500
            )

            response_text = response.choices[0].message.content
            return json.loads(self._extract_json(response_text))

        except Exception as e:
            logger.warning(f"Text interpretation failed: {e}")
            return {
                "interpretation": text,  # Fallback to original
                "confidence": 0.0,
                "alternatives": []
            }

    def _parse_risk_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse GPT-4o mini response into structured risk data.

        Args:
            response_text: Raw response from OpenAI

        Returns:
            Parsed risk data dictionary
        """
        try:
            # Extract JSON from response (sometimes wrapped in markdown)
            json_str = self._extract_json(response_text)
            risk_data = json.loads(json_str)

            # Validate required fields
            required = ["risk_score", "risk_factors", "confidence", "requires_manual_review"]
            for field in required:
                if field not in risk_data:
                    raise ValueError(f"Missing required field: {field}")

            # Validate ranges
            if not (0.0 <= risk_data["risk_score"] <= 1.0):
                raise ValueError(f"Invalid risk_score: {risk_data['risk_score']}")
            if not (0.0 <= risk_data["confidence"] <= 1.0):
                raise ValueError(f"Invalid confidence: {risk_data['confidence']}")

            return risk_data

        except Exception as e:
            logger.error(f"Failed to parse risk response: {e}")
            # Fallback: high risk with low confidence
            return {
                "risk_score": 0.8,
                "risk_factors": ["Unable to assess risk - parsing error"],
                "confidence": 0.3,
                "requires_manual_review": True
            }

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from text (handles markdown code blocks).

        Args:
            text: Text potentially containing JSON

        Returns:
            Extracted JSON string
        """
        import re

        # Try to find JSON in markdown code block
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            return json_match.group(1)

        # Try to find raw JSON object
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)

        # If no JSON found, assume entire text is JSON
        return text.strip()
