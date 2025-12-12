# Gun Registry Adapter - Multi-Stage Dockerfile
# Optimized for PaddleOCR dependencies and production deployment

# ============================================================================
# Stage 1: Base Image with System Dependencies
# ============================================================================
FROM python:3.11-slim as base

# Install system dependencies for PaddleOCR and OpenCV
RUN apt-get update && apt-get install -y \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ============================================================================
# Stage 2: Dependencies
# ============================================================================
FROM base as dependencies

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 3: Application
# ============================================================================
FROM dependencies as application

# Copy application code
COPY adapter/ adapter/
COPY models/ models/
COPY schemas/ schemas/
COPY scripts/ scripts/

# Create directories for data and logs
RUN mkdir -p data/raw data/processed logs

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run FastAPI with Uvicorn
CMD ["uvicorn", "adapter.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
