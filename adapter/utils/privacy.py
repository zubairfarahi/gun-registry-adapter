"""
Privacy-aware utilities for PII handling.

CRITICAL: NEVER log raw PII (names, DOBs, addresses, license numbers).
"""

import hashlib
import json
from typing import Dict, Any
from adapter.config.settings import settings


def hash_pii(value: str) -> str:
    """
    Hash PII for logging purposes.

    Args:
        value: PII value to hash (applicant ID, name, etc.)

    Returns:
        First 16 characters of SHA-256 hash
    """
    if not value:
        return "None"

    return hashlib.sha256(value.encode()).hexdigest()[:16]


def sanitize_for_logging(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove PII from data before logging.

    Args:
        data: Dictionary potentially containing PII

    Returns:
        Sanitized dictionary with PII hashed or removed
    """
    if not settings.enable_pii_hashing:
        # If PII hashing disabled (dev mode), log everything (NEVER do this in production!)
        if settings.log_pii:
            return data

    sanitized = {}

    # PII fields to hash
    pii_fields = {"name", "full_name", "address", "license_number", "ssn", "email", "phone"}

    # Sensitive fields to hash
    id_fields = {"applicant_id", "registry_id", "check_id"}

    for key, value in data.items():
        key_lower = key.lower()

        if any(pii_field in key_lower for pii_field in pii_fields):
            # Hash PII fields
            sanitized[key] = hash_pii(str(value)) if value else None
        elif any(id_field in key_lower for id_field in id_fields):
            # Hash ID fields
            sanitized[f"{key}_hash"] = hash_pii(str(value)) if value else None
        elif isinstance(value, dict):
            # Recursively sanitize nested dictionaries
            sanitized[key] = sanitize_for_logging(value)
        elif key_lower == "dob" or key_lower == "date_of_birth":
            # Hash DOB
            sanitized[key] = hash_pii(str(value)) if value else None
        else:
            # Keep non-PII fields as-is
            sanitized[key] = value

    return sanitized


def redact_pii(text: str) -> str:
    """
    Redact PII from error messages and stack traces.

    Args:
        text: Text that might contain PII

    Returns:
        Text with PII redacted
    """
    # Simple redaction - replace common PII patterns
    import re

    # Redact email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]', text)

    # Redact SSN patterns (XXX-XX-XXXX)
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]', text)

    # Redact phone numbers
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE_REDACTED]', text)

    # Redact dates that look like DOBs (MM/DD/YYYY or YYYY-MM-DD)
    text = re.sub(r'\b\d{4}-\d{2}-\d{2}\b', '[DATE_REDACTED]', text)
    text = re.sub(r'\b\d{2}/\d{2}/\d{4}\b', '[DATE_REDACTED]', text)

    return text
