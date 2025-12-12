# Gun Registry Adapter - AI-Powered Eligibility Assessment System

A production-ready multi-model AI system for firearm eligibility assessment, implementing a three-tier architecture with self-healing capabilities.

## 🎯 Overview

The Gun Registry Adapter demonstrates advanced AI engineering through a sophisticated three-model architecture:

- **Model A (Perception)**: PaddleOCR for driver license OCR extraction with image quality assessment
- **Model B (Reasoning)**: OpenAI GPT-4o mini for risk assessment + RapidFuzz for probabilistic data linkage
- **Model C (Self-Healing)**: Anthropic Claude Sonnet 4.5 for autonomous error detection, code fix generation, and system healing

This system processes driver license images, extracts applicant data, performs background checks via probabilistic linkage, assesses risk, and makes eligibility decisions—all while automatically detecting and fixing errors using AI-powered self-healing.

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      n8n Workflow Engine                        │
│  (Orchestration: Ingest → Process → Decide → Submit → Notify)  │
└────────────┬────────────────────────────────────────────────────┘
             │ REST API
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Gun Registry Adapter (FastAPI)                │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │  Eligibility Engine (Core Orchestrator)                     │ │
│ └───┬─────────────┬───────────────────┬─────────────────────┘ │
│     │             │                   │                         │
│ ┌───▼──────┐  ┌───▼───────────┐  ┌───▼───────────────────┐    │
│ │ Model A  │  │   Linkage     │  │      Model B          │    │
│ │PaddleOCR │  │ Probabilistic │  │  GPT-4o mini +        │    │
│ │  (OCR)   │  │   Fuzzy       │  │   RapidFuzz           │    │
│ │          │  │   Matching    │  │ (Risk Assessment)     │    │
│ └──────────┘  └───────────────┘  └───────────────────────┘    │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │  Model C: Self-Healing (Claude Sonnet 4.5)                  ││
│ │  Detect → Propose → Validate → Apply → Learn                ││
│ └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### n8n Workflow Visualization

The complete end-to-end workflow orchestrated by n8n, from image ingestion to decision notification:

![n8n Workflow](docs/n8n.png)

**Workflow Steps:**

1. **Trigger**: Webhook receives driver license image upload
2. **API Call**: POST request to `/api/v1/eligibility` endpoint
3. **Model A (OCR)**: Extract applicant data from image
4. **Linkage**: Probabilistic matching against NICS records
5. **Model B (Risk Assessment)**: Calculate risk score and factors
6. **Decision Logic**: Route based on eligibility decision
   - ✅ **APPROVED** → Submit to registry → Send approval notification
   - ❌ **DENIED** → Send denial notification with reasons
   - ⚠️ **MANUAL_REVIEW** → Escalate to human reviewer
7. **Model C (Self-Healing)**: Monitor for errors and auto-fix issues
8. **Notification**: Email/SMS to applicant with decision

## 📊 Dataset Handling

### CRITICAL: NICS Data Limitation

The FBI NICS dataset contains **state-level monthly aggregates**, NOT individual records. Example:

```csv
month,state,permit,handgun,long_gun,totals
2023-09,Florida,8399,51223,20945,95281
```

**Mitigation Strategy**: Generate synthetic individual records from aggregates using demographic distributions.

See [docs/dataset_eval.md](docs/dataset_eval.md) for full analysis.

## 🚀 Quick Start

Choose between **Docker** (recommended for quick setup) or **Local Development** (for active development).

### Prerequisites

**For Docker Setup:**
- Docker Engine 20.10+
- Docker Compose 2.0+

**For Local Development:**
- Python 3.11+
- pip and virtualenv
- curl (for testing)

**API Keys (required for both):**
- OpenAI API key (for GPT-4o mini - Model B)
- Anthropic API key (for Claude Sonnet 4.5 - Model C)

---

## 🐳 Option 1: Docker Setup (Recommended)

This runs both the **adapter** and **n8n** services in Docker containers.

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd gun-registry-adapter
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and configure API keys
nano .env  # or use your preferred editor
```

**Required configurations in `.env`:**
```bash
# CRITICAL: Add your API keys
OPENAI_API_KEY=sk-proj-your-actual-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here

# n8n credentials (change from defaults!)
N8N_USER=admin
N8N_PASSWORD=your-secure-password-here

# Optional: Adjust ports if needed
API_PORT=8000
N8N_PORT=5678
```

### Step 3: Prepare Data Directories

```bash
# Create required directories
mkdir -p data/raw/nics_data data/raw/synthetic_cards data/processed logs

# Download NICS aggregate data (optional - for synthetic record generation)
# From: https://github.com/BuzzFeedNews/nics-firearm-background-checks/
# Save as: data/raw/nics_data/nics-firearm-background-checks.csv
```

### Step 4: Build and Start Services

```bash
# Build Docker images
docker-compose build

# Start both adapter and n8n services
docker-compose up -d

# Verify containers are running
docker-compose ps
```

**Expected output:**
```
NAME                    STATUS              PORTS
gun_registry_adapter    Up 10 seconds       0.0.0.0:8000->8000/tcp
n8n_workflow            Up 10 seconds       0.0.0.0:5678->5678/tcp
```

### Step 5: Verify Services

```bash
# Check adapter health
curl http://localhost:8000/api/v1/health

# View logs
docker-compose logs -f adapter  # Press Ctrl+C to exit
docker-compose logs -f n8n
```

### Step 6: Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **FastAPI Adapter** | http://localhost:8000 | No auth (dev mode) |
| **API Documentation** | http://localhost:8000/docs | No auth |
| **n8n Workflow Editor** | http://localhost:5678 | Username: `admin`<br>Password: (from `.env`) |
| **Health Check** | http://localhost:8000/api/v1/health | No auth |

### Docker Management Commands

```bash
# Stop all services
docker-compose down

# Stop and remove all data (including n8n workflows!)
docker-compose down -v

# Restart services
docker-compose restart

# View real-time logs
docker-compose logs -f

# Rebuild after code changes
docker-compose up -d --build

# Access adapter container shell
docker exec -it gun_registry_adapter /bin/bash

# Access n8n container shell
docker exec -it n8n_workflow /bin/sh
```

---

## 💻 Option 2: Local Development Setup

For active development with hot-reload and debugging.

### Step 1: Clone and Create Virtual Environment

```bash
git clone <repository-url>
cd gun-registry-adapter

# Create Python 3.11 virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows
```

### Step 2: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

**Note:** PaddleOCR has heavy dependencies (PaddlePaddle, OpenCV). Installation may take 5-10 minutes.

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use VS Code: code .env
```

### Step 4: Prepare Data

```bash
# Create required directories
mkdir -p data/raw/nics_data data/raw/synthetic_cards data/processed logs

# (Optional) Generate synthetic NICS records
# First, download NICS data from:
# https://github.com/BuzzFeedNews/nics-firearm-background-checks/
# Save as: data/raw/nics_data/nics-firearm-background-checks.csv

# Then generate synthetic individual records
python scripts/generate_synthetic_nics.py
```

### Step 5: Run Adapter Locally

```bash
# Option A: Using Makefile (recommended)
make run

# Option B: Direct uvicorn command
uvicorn adapter.main:app --reload --host 0.0.0.0 --port 8000

# Option C: Using Python module
python -m uvicorn adapter.main:app --reload
```

The API will be available at http://localhost:8000

### Step 6: Run n8n (Optional - for workflow testing)

**In a separate terminal:**

```bash
# Option A: Using Docker for n8n only
docker run -d \
  --name n8n_local \
  -p 5678:5678 \
  -e N8N_BASIC_AUTH_ACTIVE=true \
  -e N8N_BASIC_AUTH_USER=admin \
  -e N8N_BASIC_AUTH_PASSWORD=changeme \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n

# Option B: Using npx (requires Node.js)
npx n8n
```

Access n8n at http://localhost:5678

---

## 🛠️ Using Makefile Commands

The project includes a comprehensive Makefile for common tasks:

### Setup Commands

```bash
make setup          # Complete setup (venv + dependencies + .env)
make install        # Install dependencies only
make check-env      # Verify .env is configured correctly
make check-data     # Verify required data files exist
```

### Development Commands

```bash
make run            # Start development server with hot-reload
make dev            # Alias for 'make run'
make shell          # Open Python shell with venv activated
```

### Docker Commands

```bash
make docker-build   # Build Docker images
make docker-up      # Start containers (adapter + n8n)
make docker-down    # Stop containers
make docker-restart # Restart containers
make docker-logs    # View real-time logs
make docker-clean   # Remove containers, volumes, and images
```

### Testing Commands

```bash
make test           # Run all tests
make test-unit      # Run unit tests only
make test-integration  # Run integration tests only
make test-cov       # Run tests with coverage report
```

### Code Quality Commands

```bash
make format         # Format code with black and isort
make lint           # Run ruff linter
make lint-fix       # Auto-fix linting issues
make check          # Run all quality checks
make fix            # Auto-fix all issues (format + lint-fix)
```

### Data Commands

```bash
make generate-nics  # Generate synthetic NICS records
make check-data     # Verify data files exist
```

### Cleanup Commands

```bash
make clean          # Remove Python cache files
make clean-logs     # Remove log files
make clean-data     # Remove generated data
make clean-all      # Complete cleanup (includes Docker)
```

### View all commands:

```bash
make help
```

## 📡 API Usage

### Check Eligibility

```bash
curl -X POST http://localhost:8000/api/v1/eligibility \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "test-12345",
    "id_image_base64": "<base64-encoded-image>"
  }'
```

**Response**:
```json
{
  "applicant_id": "test-12345",
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
    "matched": false,
    "confidence": 0.25,
    "requires_review": false
  },
  "requires_manual_review": false,
  "decision_rationale": ["Age eligible: 38 years old", "All checks passed"],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=adapter --cov-report=html

# Run specific test file
pytest tests/unit/test_paddleocr_adapter.py

# Run integration tests
pytest tests/integration/
```

## 📝 Project Structure

Detailed explanation of the codebase organization:

```
gun-registry-adapter/
├── adapter/                          # Core application code
│   ├── __init__.py
│   ├── main.py                       # FastAPI application entry point
│   │
│   ├── api/                          # REST API layer
│   │   ├── __init__.py
│   │   ├── routes.py                 # API endpoints (/eligibility, /registry/submit, etc.)
│   │   └── middleware.py             # CORS, rate limiting, logging middleware
│   │
│   ├── core/                         # Business logic (Model A, B, C)
│   │   ├── __init__.py
│   │   │
│   │   ├── interfaces/               # Abstract interfaces (SOLID design)
│   │   │   ├── __init__.py
│   │   │   ├── perception_interface.py    # Model A interface
│   │   │   └── reasoning_interface.py     # Model B interface
│   │   │
│   │   ├── model_a/                  # Perception Layer (OCR)
│   │   │   ├── __init__.py
│   │   │   ├── paddleocr_adapter.py       # PaddleOCR implementation
│   │   │   ├── image_preprocessor.py      # Image quality enhancement
│   │   │   └── tamper_detector.py         # Forgery detection
│   │   │
│   │   ├── model_b/                  # Reasoning Layer (Risk Assessment)
│   │   │   ├── __init__.py
│   │   │   ├── gpt4o_mini_adapter.py      # OpenAI GPT-4o mini for risk scoring
│   │   │   └── rapidfuzz_adapter.py       # Fuzzy matching for linkage
│   │   │
│   │   ├── model_c/                  # Self-Healing Layer (optional if implemented)
│   │   │   ├── __init__.py
│   │   │   └── claude_adapter.py          # Claude for fix generation
│   │   │
│   │   ├── engine.py                 # Eligibility orchestrator (coordinates A, B, linkage)
│   │   ├── linkage.py                # Probabilistic data linkage logic
│   │   └── normalization.py          # Schema normalization
│   │
│   ├── self_healing/                 # Model C self-healing system
│   │   ├── __init__.py
│   │   ├── orchestrator.py           # Self-healing workflow coordinator
│   │   ├── error_detector.py         # Error classification
│   │   ├── claude_fixer.py           # Fix proposal using Claude API
│   │   ├── fix_validator.py          # Test and validate fixes
│   │   ├── fix_applicator.py         # Apply validated fixes
│   │   ├── learning_loop.py          # Store outcomes for learning
│   │   └── decorators.py             # @self_healing decorator
│   │
│   ├── config/                       # Configuration and settings
│   │   ├── __init__.py
│   │   ├── settings.py               # Environment variables, config classes
│   │   └── logging_config.py         # Privacy-aware logging setup
│   │
│   ├── exceptions/                   # Custom exception classes
│   │   ├── __init__.py
│   │   ├── parser_exceptions.py      # OCR-related errors
│   │   ├── linkage_exceptions.py     # Linkage errors
│   │   └── self_healing_exceptions.py # Self-healing errors
│   │
│   └── utils/                        # Utility functions
│       ├── __init__.py
│       ├── hashing.py                # PII hashing for logs
│       └── validators.py             # Input validation helpers
│
├── models/                           # Model training & configs (optional)
│   ├── model_a_perception/
│   ├── model_b_reasoning/
│   └── model_c_healing/
│
├── schemas/                          # Data schemas & OpenAPI
│   ├── openapi.yaml                  # OpenAPI specification
│   └── domain_objects.json           # Domain object schemas
│
├── workflow/                         # n8n workflow definitions
│   ├── main_workflow.json            # Main eligibility workflow
│   └── README.md                     # Workflow documentation
│
├── scripts/                          # Utility scripts
│   ├── generate_synthetic_nics.py    # Generate synthetic NICS records
│   └── test_eligibility.py           # CLI testing script
│
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── conftest.py                   # Pytest fixtures
│   │
│   ├── unit/                         # Unit tests (70% coverage target)
│   │   ├── test_paddleocr_adapter.py
│   │   ├── test_gpt4o_mini_adapter.py
│   │   ├── test_linkage.py
│   │   └── test_self_healing.py
│   │
│   ├── integration/                  # Integration tests (25% coverage)
│   │   ├── test_eligibility_pipeline.py
│   │   └── test_api_endpoints.py
│   │
│   └── fixtures/                     # Test data
│       ├── sample_images/
│       └── mock_responses.json
│
├── data/                             # Data storage
│   ├── raw/                          # Raw data
│   │   ├── synthetic_cards/          # Synthetic driver license images
│   │   └── nics_data/
│   │       └── nics-firearm-background-checks.csv
│   │
│   ├── processed/                    # Processed data
│   │   └── synthetic_nics_records.json
│   │
│   ├── registry.db                   # SQLite database (audit logs)
│   └── self_healing.db               # Self-healing history database
│
├── logs/                             # Application logs
│   └── audit.log                     # Privacy-aware audit trail (JSON format)
│
├── docs/                             # Documentation
│   ├── architecture.md               # Architecture decisions & patterns
│   ├── dataset_eval.md               # Dataset analysis & limitations
│   └── api_examples.md               # API usage examples
│
├── .env.example                      # Environment variable template
├── .env                              # Local environment config (gitignored)
├── .gitignore                        # Git ignore rules
├── requirements.txt                  # Python dependencies
├── Dockerfile                        # Container definition
├── docker-compose.yml                # Multi-service orchestration (adapter + n8n)
├── Makefile                          # Development automation
├── CLAUDE.md                         # Development guidelines (this file)
├── QUICKSTART.md                     # Quick start guide
└── README.md                         # Project overview
```

### Key Design Principles

**1. SOLID Architecture**

- All models use abstract interfaces for swappability
- Single Responsibility: Model A (perception), Model B (reasoning), Model C (healing)
- Open/Closed: Can swap PaddleOCR for EasyOCR without changing core logic

**2. Probabilistic Everything**

- No exact matching—all decisions return confidence scores
- Manual review flagging for low-confidence decisions (0.7-0.9)
- Documented assumptions for every linkage decision

**3. Privacy by Design**

- No PII in logs (names, DOBs, addresses sanitized)
- Hashed applicant IDs for logging
- Encrypted audit trails in production

**4. Self-Healing**

- Model C detects errors, proposes fixes, validates, and learns
- Learning loop stores outcomes to improve future proposals
- Human-in-the-loop for low-confidence fixes

## 🔒 Security & Privacy

- **PII Hashing**: All applicant IDs hashed before logging
- **No PII in Logs**: Names, DOBs, addresses sanitized
- **Encrypted Storage**: Audit trails stored in encrypted SQLite (production)
- **API Rate Limiting**: 100 req/min default
- **CORS**: Configured origins only

## 📈 Monitoring

### Metrics Tracked

- **Model A**: OCR success rate, avg confidence, tamper detection rate
- **Model B**: Risk score distribution, manual review rate
- **Model C**: Self-healing trigger count, fix success rate
- **API**: Request latency (p50/p95/p99), error rate

### Logs

```bash
# View application logs
tail -f logs/audit.log

# View JSON-formatted logs
cat logs/audit.log | jq '.'
```

## 🛠️ Configuration

Key environment variables (`.env`):

```bash
# API Keys
OPENAI_API_KEY=sk-proj-your-key
ANTHROPIC_API_KEY=sk-ant-your-key

# Model Thresholds
MODEL_A_CONFIDENCE_THRESHOLD=0.8
MODEL_B_RISK_THRESHOLD=0.7
LINKAGE_CONFIDENCE_THRESHOLD=0.7

# Self-Healing
SELF_HEALING_ENABLED=true
AUTO_APPLY_FIXES=false  # CAUTION: Only true in dev!

# Data
USE_SYNTHETIC_NICS=true
SYNTHETIC_NICS_PATH=data/processed/synthetic_nics_records.json
```

## 📚 Documentation

- [CLAUDE.md](CLAUDE.md) - Comprehensive development guidelines
- [docs/dataset_eval.md](docs/dataset_eval.md) - Dataset analysis & limitations
- [docs/architecture.md](docs/architecture.md) - Architecture decisions
- [API Docs](http://localhost:8000/docs) - Interactive API documentation

---

## ❓ Troubleshooting

### Common Issues

#### Docker Issues

**Problem: `docker-compose up` fails with "address already in use"**

```bash
# Check what's using port 8000 or 5678
lsof -i :8000
lsof -i :5678

# Kill the process or change ports in .env
API_PORT=8001
N8N_PORT=5679
```

**Problem: Containers keep restarting**

```bash
# Check container logs for errors
docker-compose logs adapter
docker-compose logs n8n

# Common causes:
# 1. Missing .env file → Run: cp .env.example .env
# 2. Invalid API keys → Check OPENAI_API_KEY and ANTHROPIC_API_KEY in .env
# 3. Missing data directories → Run: mkdir -p data/raw data/processed logs
```

**Problem: "No such file or directory" when accessing data**

```bash
# Create required directories
mkdir -p data/raw/nics_data data/raw/synthetic_cards data/processed logs

# Verify volumes are mounted correctly
docker-compose config
```

**Problem: n8n workflows not persisting**

```bash
# Check if n8n volume exists
docker volume ls | grep n8n

# If missing, recreate:
docker-compose down
docker volume create gun-registry-adapter_n8n_data
docker-compose up -d
```

---

#### Local Development Issues

**Problem: `ModuleNotFoundError: No module named 'paddleocr'`**

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**Problem: PaddleOCR installation fails**

```bash
# On macOS with M1/M2 (Apple Silicon):
pip install paddlepaddle==2.5.1
pip install paddleocr

# On Linux:
python -m pip install paddlepaddle-gpu  # If you have CUDA
# OR
python -m pip install paddlepaddle  # CPU only

# Then install PaddleOCR
pip install paddleocr
```

**Problem: OpenAI API errors (401 Unauthorized)**

```bash
# Verify API key is correctly set
cat .env | grep OPENAI_API_KEY

# Test API key manually
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print(os.getenv('OPENAI_API_KEY'))
"

# Common fixes:
# 1. Ensure no extra spaces: OPENAI_API_KEY=sk-proj-...
# 2. Use quotes if key contains special characters: OPENAI_API_KEY="sk-proj-..."
# 3. Reload .env: export $(cat .env | xargs)
```

**Problem: Anthropic API errors (401 Unauthorized)**

```bash
# Same troubleshooting as OpenAI above, but check ANTHROPIC_API_KEY
cat .env | grep ANTHROPIC_API_KEY
```

**Problem: `uvicorn: command not found`**

```bash
# Virtual environment not activated
source venv/bin/activate

# Or use full path
./venv/bin/uvicorn adapter.main:app --reload
```

---

#### API Issues

**Problem: Health check fails (`/api/v1/health` returns 404)**

```bash
# Check if server is running
curl http://localhost:8000/api/v1/health

# If 404, verify route is defined in adapter/api/routes.py
# Check server logs for startup errors
docker-compose logs adapter | grep ERROR
```

**Problem: OCR extraction returns low confidence**

```bash
# Check image quality
# Images should be:
# - At least 600x400 pixels
# - Clear text (not blurry)
# - Good contrast
# - Not rotated

# Adjust confidence threshold in .env
MODEL_A_CONFIDENCE_THRESHOLD=0.6  # Lower threshold for testing
```

**Problem: API returns 500 error with "Database locked"**

```bash
# SQLite is locked by another process
# Stop all containers/processes
docker-compose down
pkill -f "uvicorn adapter.main:app"

# Remove lock files
rm -f data/*.db-wal data/*.db-shm

# Restart
docker-compose up -d
```

---

#### Data Issues

**Problem: "NICS data not found" error**

```bash
# Download NICS data
mkdir -p data/raw/nics_data
cd data/raw/nics_data

# Download from BuzzFeed News
curl -L https://raw.githubusercontent.com/BuzzFeedNews/nics-firearm-background-checks/master/data/nics-firearm-background-checks.csv -o nics-firearm-background-checks.csv

# Return to project root
cd ../../..

# Generate synthetic records
python scripts/generate_synthetic_nics.py
```

**Problem: No synthetic driver licenses found**

```bash
# Check if synthetic_cards directory exists
ls -la data/raw/synthetic_cards/

# If empty or missing, you need to obtain synthetic driver license images
# (These should be provided as part of the exercise data)
```

---

#### Testing Issues

**Problem: `pytest: command not found`**

```bash
# Activate virtual environment
source venv/bin/activate

# Install test dependencies
pip install pytest pytest-cov pytest-mock
```

**Problem: Tests fail with "No API key found"**

```bash
# Create .env file for tests
cp .env.example .env

# Or set environment variables directly
export OPENAI_API_KEY=sk-proj-test-key
export ANTHROPIC_API_KEY=sk-ant-test-key

# Or use mock mode
TEST_MODE=true pytest tests/
```

---

### Getting Help

1. **Check logs first:**
   ```bash
   # Docker
   docker-compose logs -f adapter

   # Local
   tail -f logs/audit.log
   ```

2. **Verify configuration:**
   ```bash
   make check-env    # Check .env is configured
   make check-data   # Check data files exist
   make health       # Check API health
   ```

3. **Review documentation:**
   - [CLAUDE.md](CLAUDE.md) - Development guidelines
   - [docs/architecture.md](docs/architecture.md) - Architecture details
   - API docs at <http://localhost:8000/docs>

4. **Common commands:**
   ```bash
   make help         # View all available commands
   make clean-all    # Complete cleanup and restart
   make docker-up    # Start fresh with Docker
   ```

---

## 🤝 Contributing

This is an engineering exercise demonstrating AI system design. Key learning objectives:

1. Multi-model AI architecture (perception + reasoning + self-healing)
2. Probabilistic data linkage (no exact matching)
3. SOLID design principles
4. Privacy-aware engineering
5. Production-ready patterns

## 📄 License

Educational project - see exercise requirements for usage terms.

## 🔗 References

- [FBI NICS Data](https://github.com/BuzzFeedNews/nics-firearm-background-checks/)
- [PaddleOCR Docs](https://github.com/PaddlePaddle/PaddleOCR)
- [OpenAI API](https://platform.openai.com/docs)
- [Anthropic Claude](https://docs.anthropic.com/)
- [n8n Workflow Automation](https://n8n.io/)

---

**Built with:** Python 3.11, FastAPI, PaddleOCR, OpenAI GPT-4o mini, Anthropic Claude, RapidFuzz, Docker
