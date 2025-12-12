"""Risk assessment prompts for OpenAI GPT-4o mini.

This module contains structured prompts for firearm eligibility risk assessment
and text interpretation.
"""

from typing import Dict, Any
from datetime import datetime


# =============================================================================
# Role Definition
# =============================================================================

ROLE_RISK_EXPERT = """
You are an expert risk assessment specialist for firearm background checks with 10+ years
of experience in analyzing applicant eligibility, interpreting background check data,
and identifying risk factors for firearm purchases.
"""


# =============================================================================
# Risk Assessment Prompts
# =============================================================================

RISK_ASSESSMENT_INSTRUCTION = """
Assess the risk level for the following firearm purchase applicant:

**Applicant Data:**
- Name: {name}
- Date of Birth: {dob}
- Age: {age}
- State: {state}
- License Number: {license_number}
- Address: {address}

**Background Check Result:**
{background_check}

**Risk Assessment Criteria:**
1. **Age Eligibility**: Must be 21+ years old
2. **Background Check**: Any criminal record matches
3. **ID Validity**: License number format and state consistency
4. **Data Completeness**: Missing critical fields increase risk

**Instructions:**
Return a JSON object with:
- `risk_score`: Float 0.0 (low risk) to 1.0 (high risk)
- `risk_factors`: List of human-readable risk reasons
- `confidence`: Your confidence in this assessment (0.0-1.0)
- `requires_manual_review`: Boolean - true if ambiguous or borderline

**Example:**
```json
{{
  "risk_score": 0.15,
  "risk_factors": ["Age eligible (38 years old)", "No criminal record matches", "Valid state license"],
  "confidence": 0.95,
  "requires_manual_review": false
}}
```

Respond with JSON only:
"""


def generate_risk_assessment_prompt(applicant_data: Dict[str, Any]) -> str:
    """
    Generate prompt for risk assessment.

    Args:
        applicant_data: Dictionary containing applicant information:
            - name: Full name
            - dob: Date of birth (YYYY-MM-DD)
            - state: 2-letter state code
            - license_number: Driver license number
            - address: Full address
            - background_check: Background check result text

    Returns:
        Formatted prompt for GPT-4o mini

    Example:
        >>> applicant = {
        ...     "name": "John Doe",
        ...     "dob": "1985-03-15",
        ...     "state": "FL",
        ...     "license_number": "D123456789",
        ...     "address": "123 Main St, Miami, FL 33101",
        ...     "background_check": "No criminal record matches"
        ... }
        >>> prompt = generate_risk_assessment_prompt(applicant)
    """
    # Calculate age if DOB provided
    age = "Unknown"
    if "dob" in applicant_data and applicant_data["dob"]:
        try:
            dob = datetime.strptime(applicant_data["dob"], "%Y-%m-%d")
            age = str((datetime.now() - dob).days // 365)
        except:
            age = "Unknown"

    # Build prompt with role and instruction
    prompt = f"""{ROLE_RISK_EXPERT}

{RISK_ASSESSMENT_INSTRUCTION.format(
    name=applicant_data.get('name', 'Unknown'),
    dob=applicant_data.get('dob', 'Unknown'),
    age=age,
    state=applicant_data.get('state', 'Unknown'),
    license_number=applicant_data.get('license_number', 'Unknown'),
    address=applicant_data.get('address', 'Unknown'),
    background_check=applicant_data.get('background_check', 'No background check data available')
)}"""

    return prompt


# =============================================================================
# Text Interpretation Prompts
# =============================================================================

TEXT_INTERPRETATION_INSTRUCTION = """
I need you to interpret the following text in the context of {context}.

**Text to Interpret:**
"{text}"

**Context:** {context}

**Instructions:**
- Provide your best interpretation of the text
- Consider common variations, abbreviations, and typos
- Return a JSON object with your interpretation and confidence

**Response Format:**
```json
{{
  "interpretation": "your clear interpretation",
  "confidence": 0.0-1.0,
  "alternatives": ["alternative 1", "alternative 2"]
}}
```

IMPORTANT:
- Your response must be a single, valid, raw JSON object
- Do not add any comments, introductory text, or markdown formatting
- Only return the JSON object

Please place your answer here (JSON object only):
"""


def generate_text_interpretation_prompt(text: str, context: str) -> str:
    """
    Generate prompt for text interpretation.

    This is used when Model B needs to interpret ambiguous OCR output or
    unclear text from Model A.

    Args:
        text: Text to interpret (e.g., unclear state abbreviation, ambiguous date)
        context: Context for interpretation (e.g., "state_abbreviation", "denial_reason", "date_format")

    Returns:
        Formatted prompt for GPT-4o mini

    Example:
        >>> prompt = generate_text_interpretation_prompt("CA", "state_abbreviation")
        >>> # Returns interpretation: "California (CA)"
    """
    prompt = f"""{ROLE_RISK_EXPERT}

{TEXT_INTERPRETATION_INSTRUCTION.format(
    text=text,
    context=context
)}"""

    return prompt


# =============================================================================
# Field-Specific Enhancement Prompts (Optional - for future use)
# =============================================================================

NAME_ENHANCEMENT_INSTRUCTION = """
I have extracted a name from OCR that may contain errors. Please clean it up.

**OCR Extracted Name:** {name}

**Instructions:**
- Fix obvious OCR errors (e.g., "0" instead of "O", "1" instead of "I")
- Correct capitalization
- Remove extra spaces or characters
- Keep original if unclear

**Response Format:**
```json
{{
  "corrected_name": "Corrected Name",
  "confidence": 0.0-1.0,
  "changes_made": ["description of changes"]
}}
```

Respond with JSON only:
"""


def generate_name_enhancement_prompt(name: str) -> str:
    """
    Generate prompt for name correction/enhancement.

    Args:
        name: OCR-extracted name that may contain errors

    Returns:
        Formatted prompt for GPT-4o mini

    Example:
        >>> prompt = generate_name_enhancement_prompt("J0HN D0E")
        >>> # Returns corrected: "JOHN DOE"
    """
    prompt = f"""{ROLE_RISK_EXPERT}

{NAME_ENHANCEMENT_INSTRUCTION.format(name=name)}"""

    return prompt


# =============================================================================
# Date Format Standardization
# =============================================================================

DATE_STANDARDIZATION_INSTRUCTION = """
I need you to standardize a date extracted from OCR into YYYY-MM-DD format.

**OCR Extracted Date:** {date_text}

**Instructions:**
- Convert to YYYY-MM-DD format
- Handle common formats: MM/DD/YYYY, DD/MM/YYYY, Month DD, YYYY, etc.
- If ambiguous, make reasonable assumptions (e.g., US format MM/DD/YYYY)
- If unclear or invalid, return null

**Response Format:**
```json
{{
  "standardized_date": "YYYY-MM-DD or null",
  "confidence": 0.0-1.0,
  "original_format_detected": "format description"
}}
```

Respond with JSON only:
"""


def generate_date_standardization_prompt(date_text: str) -> str:
    """
    Generate prompt for date format standardization.

    Args:
        date_text: Date text from OCR (any format)

    Returns:
        Formatted prompt for GPT-4o mini

    Example:
        >>> prompt = generate_date_standardization_prompt("03/15/1985")
        >>> # Returns: "1985-03-15"
    """
    prompt = f"""{ROLE_RISK_EXPERT}

{DATE_STANDARDIZATION_INSTRUCTION.format(date_text=date_text)}"""

    return prompt
