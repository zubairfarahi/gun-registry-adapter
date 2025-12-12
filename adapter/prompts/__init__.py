"""Prompt templates for Gun Registry Adapter.

This module contains structured prompts for LLM-based operations.
"""

from adapter.prompts.risk_assessment_prompts import (
    generate_risk_assessment_prompt,
    generate_text_interpretation_prompt,
    ROLE_RISK_EXPERT,
)

__all__ = [
    "generate_risk_assessment_prompt",
    "generate_text_interpretation_prompt",
    "ROLE_RISK_EXPERT",
]
