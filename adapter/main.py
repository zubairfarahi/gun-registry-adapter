"""
Gun Registry Adapter - FastAPI Application.

Main entry point for the REST API server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from adapter.api.routes import router
from adapter.config.settings import settings
from adapter.config.logging_config import logger


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Gun Registry Adapter",
    description="AI-powered firearm eligibility assessment system using multi-model architecture",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================================================
# CORS Middleware
# ============================================================================

# Parse CORS origins from settings
cors_origins = [origin.strip() for origin in settings.api_cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Include Routers
# ============================================================================

app.include_router(router)

# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Gun Registry Adapter",
        "version": "1.0.0",
        "description": "AI-powered firearm eligibility assessment system",
        "models": {
            "model_a": "PaddleOCR (Perception/OCR)",
            "model_b": "OpenAI GPT-4o mini (Reasoning/Risk Assessment)",
            "model_c": "Anthropic Claude (Self-Healing)"
        },
        "endpoints": {
            "eligibility": "/api/v1/eligibility",
            "registry_submit": "/api/v1/registry/submit",
            "health": "/api/v1/health",
            "docs": "/docs"
        }
    }

# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("=" * 80)
    logger.info("Gun Registry Adapter Starting")
    logger.info("=" * 80)
    logger.info(
        "Configuration loaded",
        extra={
            "model_a_enabled": settings.enable_model_a,
            "model_b_enabled": settings.enable_model_b,
            "model_c_enabled": settings.enable_model_c,
            "self_healing_enabled": settings.self_healing_enabled,
            "use_synthetic_nics": settings.use_synthetic_nics
        }
    )
    logger.info(f"API server listening on {settings.api_host}:{settings.api_port}")
    logger.info("=" * 80)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Gun Registry Adapter Shutting Down")


# ============================================================================
# Global Exception Handler
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle all uncaught exceptions."""
    logger.error(
        f"Uncaught exception: {exc}",
        extra={"path": request.url.path},
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": str(exc) if settings.debug else None
        }
    )


# ============================================================================
# Run with Uvicorn (for development)
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "adapter.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
