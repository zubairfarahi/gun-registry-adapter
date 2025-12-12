"""
FastAPI Routes for Gun Registry Adapter.

Provides REST API endpoints for eligibility checking.
"""

import base64
import tempfile
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from adapter.core.engine import EligibilityEngine, EligibilityDecision
from adapter.config.logging_config import logger
from adapter.config.settings import settings


# ============================================================================
# Request/Response Models
# ============================================================================

class EligibilityRequest(BaseModel):
    """Request model for eligibility check."""
    applicant_id: str = Field(..., description="Unique applicant identifier")
    id_image_base64: Optional[str] = Field(None, description="Base64-encoded driver license image")
    id_image_url: Optional[str] = Field(None, description="URL to driver license image")

    class Config:
        json_schema_extra = {
            "example": {
                "applicant_id": "550e8400-e29b-41d4-a716-446655440000",
                "id_image_base64": "iVBORw0KGgoAAAANSUhEUg..."
            }
        }


class EligibilityResponse(BaseModel):
    """Response model for eligibility check."""
    applicant_id: str
    decision: str  # "APPROVED", "DENIED", "MANUAL_REVIEW"
    confidence: float
    extracted_data: dict
    risk_assessment: dict
    linkage_result: dict
    requires_manual_review: bool
    decision_rationale: list
    timestamp: str

    class Config:
        json_schema_extra = {
            "example": {
                "applicant_id": "550e8400-e29b-41d4-a716-446655440000",
                "decision": "APPROVED",
                "confidence": 0.92,
                "extracted_data": {
                    "name": "John Doe",
                    "dob": "1985-03-15",
                    "state": "FL",
                    "license_number": "D123456789",
                    "address": "123 Main St, Miami, FL 33101"
                },
                "risk_assessment": {
                    "risk_score": 0.12,
                    "risk_factors": ["Age eligible (38 years)", "No criminal record matches"],
                    "confidence": 0.95
                },
                "linkage_result": {
                    "matched": False,
                    "confidence": 0.25,
                    "requires_review": False
                },
                "requires_manual_review": False,
                "decision_rationale": ["Age eligible: 38 years old", "All checks passed"],
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    details: Optional[dict] = None
    retry_recommended: bool = False
    self_healing_triggered: bool = False


class RegistrySubmitRequest(BaseModel):
    """Request model for registry submission."""
    applicant_id: str
    eligibility_decision: str
    applicant_data: dict


class RegistrySubmitResponse(BaseModel):
    """Response model for registry submission."""
    registry_id: str
    status: str
    timestamp: str


# ============================================================================
# Router
# ============================================================================

router = APIRouter(prefix="/api/v1", tags=["eligibility"])

# Initialize eligibility engine (singleton)
engine: Optional[EligibilityEngine] = None


def get_engine() -> EligibilityEngine:
    """Get or create eligibility engine instance."""
    global engine
    if engine is None:
        engine = EligibilityEngine()
    return engine


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/eligibility", response_model=EligibilityResponse)
async def check_eligibility(request: EligibilityRequest):
    """
    Check firearm eligibility for applicant (JSON with base64/URL).

    Pipeline:
    1. Extract data from ID image (Model A - PaddleOCR)
    2. Link to NICS records (Probabilistic Linkage)
    3. Assess risk (Model B - GPT-4o mini)
    4. Make eligibility decision

    Args:
        request: JSON with applicant_id and id_image_base64 or id_image_url

    Returns:
        EligibilityResponse with decision and all intermediate outputs
    """
    try:
        logger.info(
            "Received eligibility check request",
            extra={"applicant_id_hash": _hash_id(request.applicant_id)}
        )

        # Validate request
        if not request.id_image_base64 and not request.id_image_url:
            raise HTTPException(
                status_code=400,
                detail="Either id_image_base64 or id_image_url must be provided"
            )

        # Handle base64 image
        if request.id_image_base64:
            image_path = _save_base64_image(request.id_image_base64)
        else:
            # TODO: Download image from URL
            raise HTTPException(
                status_code=501,
                detail="id_image_url not yet implemented, use id_image_base64"
            )

        # Run eligibility assessment
        engine = get_engine()
        result = engine.assess_eligibility(
            applicant_id=request.applicant_id,
            id_image_path=image_path
        )

        # Build response
        response = EligibilityResponse(
            applicant_id=result.applicant_id,
            decision=result.decision.value,
            confidence=result.confidence,
            extracted_data=result.extracted_data,
            risk_assessment={
                "risk_score": result.risk_assessment.risk_score,
                "risk_factors": result.risk_assessment.risk_factors,
                "confidence": result.risk_assessment.confidence
            },
            linkage_result={
                "matched": result.linkage_result.matched,
                "confidence": result.linkage_result.confidence,
                "field_scores": result.linkage_result.field_scores,
                "requires_review": result.linkage_result.requires_review
            },
            requires_manual_review=result.requires_manual_review,
            decision_rationale=result.decision_rationale,
            timestamp=result.timestamp.isoformat()
        )

        logger.info(
            "Eligibility check complete",
            extra={
                "applicant_id_hash": _hash_id(request.applicant_id),
                "decision": result.decision.value,
                "confidence": result.confidence
            }
        )

        return response

    except Exception as e:
        logger.error(
            f"Eligibility check failed: {e}",
            extra={"applicant_id_hash": _hash_id(request.applicant_id)},
            exc_info=True
        )

        # Determine error type
        error_type = type(e).__name__
        if "OCR" in error_type:
            error_code = "OCR_FAILED"
            retry_recommended = True
        elif "API" in error_type:
            error_code = "API_ERROR"
            retry_recommended = True
        else:
            error_code = "INTERNAL_ERROR"
            retry_recommended = False

        raise HTTPException(
            status_code=500,
            detail={
                "error": error_code,
                "message": str(e),
                "retry_recommended": retry_recommended,
                "self_healing_triggered": False  # TODO: Integrate Model C
            }
        )


@router.post("/eligibility/upload", response_model=EligibilityResponse)
async def check_eligibility_upload(
    applicant_id: str,
    id_image: UploadFile = File(...)
):
    """
    Check firearm eligibility for applicant (file upload).

    This is an alternative to the /eligibility endpoint that accepts
    direct file upload instead of base64-encoded images.

    Pipeline:
    1. Extract data from ID image (Model A - PaddleOCR)
    2. Link to NICS records (Probabilistic Linkage)
    3. Assess risk (Model B - GPT-4o mini)
    4. Make eligibility decision

    Args:
        applicant_id: Unique applicant identifier (form field)
        id_image: Driver license image file (multipart/form-data)

    Returns:
        EligibilityResponse with decision and all intermediate outputs

    Example using curl:
        curl -X POST http://localhost:8000/api/v1/eligibility/upload \
          -F "applicant_id=12345" \
          -F "id_image=@/path/to/license.png"
    """
    try:
        logger.info(
            "Received eligibility check request (file upload)",
            extra={"applicant_id_hash": _hash_id(applicant_id)}
        )

        # Validate file type
        if not id_image.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {id_image.content_type}. Must be an image."
            )

        # Save uploaded file to temp location
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        content = await id_image.read()
        temp_file.write(content)
        temp_file.close()
        image_path = temp_file.name

        # Run eligibility assessment
        engine = get_engine()
        result = engine.assess_eligibility(
            applicant_id=applicant_id,
            id_image_path=image_path
        )

        # Build response
        response = EligibilityResponse(
            applicant_id=result.applicant_id,
            decision=result.decision.value,
            confidence=result.confidence,
            extracted_data=result.extracted_data,
            risk_assessment={
                "risk_score": result.risk_assessment.risk_score,
                "risk_factors": result.risk_assessment.risk_factors,
                "confidence": result.risk_assessment.confidence
            },
            linkage_result={
                "matched": result.linkage_result.matched,
                "confidence": result.linkage_result.confidence,
                "field_scores": result.linkage_result.field_scores,
                "requires_review": result.linkage_result.requires_review
            },
            requires_manual_review=result.requires_manual_review,
            decision_rationale=result.decision_rationale,
            timestamp=result.timestamp.isoformat()
        )

        logger.info(
            "Eligibility check complete (file upload)",
            extra={
                "applicant_id_hash": _hash_id(applicant_id),
                "decision": result.decision.value,
                "confidence": result.confidence
            }
        )

        return response

    except Exception as e:
        logger.error(
            f"Eligibility check failed (file upload): {e}",
            extra={"applicant_id_hash": _hash_id(applicant_id)},
            exc_info=True
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "ELIGIBILITY_CHECK_FAILED",
                "message": str(e),
                "retry_recommended": True
            }
        )


@router.post("/registry/submit", response_model=RegistrySubmitResponse)
async def submit_to_registry(request: RegistrySubmitRequest):
    """
    Submit approved applicant to gun registry.

    This endpoint would integrate with the actual registry system.
    For now, returns mock registration ID.

    Args:
        request: Registry submission request

    Returns:
        RegistrySubmitResponse with registration ID
    """
    logger.info(
        "Registry submission request",
        extra={
            "applicant_id_hash": _hash_id(request.applicant_id),
            "decision": request.eligibility_decision
        }
    )

    if request.eligibility_decision != "APPROVED":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot submit non-approved applicant: {request.eligibility_decision}"
        )

    # Mock registry submission
    registry_id = f"REG-{datetime.now().strftime('%Y%m%d')}-{request.applicant_id[:8]}"

    logger.info(
        "Registry submission complete",
        extra={"registry_id": registry_id}
    )

    return RegistrySubmitResponse(
        registry_id=registry_id,
        status="REGISTERED",
        timestamp=datetime.now().isoformat()
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# ============================================================================
# Utility Functions
# ============================================================================

def _save_base64_image(base64_data: str) -> str:
    """
    Save base64-encoded image to temporary file.

    Args:
        base64_data: Base64-encoded image

    Returns:
        Path to saved image file
    """
    try:
        # Decode base64
        image_data = base64.b64decode(base64_data)

        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        temp_file.write(image_data)
        temp_file.close()

        return temp_file.name

    except Exception as e:
        raise ValueError(f"Failed to decode base64 image: {e}")


def _hash_id(applicant_id: str) -> str:
    """Hash applicant ID for privacy-aware logging."""
    import hashlib
    return hashlib.sha256(applicant_id.encode()).hexdigest()[:16]
