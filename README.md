# Gun Registry Adapter - AI-Powered Eligibility Assessment System

A multi-model AI system for firearm eligibility assessment with a three-tier architecture.

## 🎯 Overview

Three-model architecture for processing driver license images and assessing eligibility:

- **Model A (Perception)**: PaddleOCR for license OCR extraction
- **Model B (Reasoning)**: GPT-4o mini for risk assessment + RapidFuzz for fuzzy matching
- **Model C (Self-Healing)**: Placeholder for autonomous error detection (planned)

## 🏗️ Architecture

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
│ │  Eligibility Engine                                         │ │
│ └───┬─────────────┬───────────────────┬─────────────────────┘ │
│     │             │                   │                         │
│ ┌───▼──────┐  ┌───▼───────────┐  ┌───▼───────────────────┐    │
│ │ Model A  │  │   Linkage     │  │      Model B          │    │
│ │PaddleOCR │  │ Probabilistic │  │  GPT-4o mini +        │    │
│ │          │  │   Matching    │  │   RapidFuzz           │    │
│ └──────────┘  └───────────────┘  └───────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### n8n Workflow

![n8n Workflow](docs/n8n.png)

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API key
- Anthropic API key (for future Model C)

### Setup with Docker

```bash
# 1. Clone and configure
git clone <repository-url>
cd gun-registry-adapter
cp .env.example .env

# 2. Edit .env and add your API keys
nano .env  # Add OPENAI_API_KEY and ANTHROPIC_API_KEY

# 3. Start services
docker-compose up -d

# 4. Verify
docker-compose ps
curl http://localhost:8000/api/v1/health
```

### Local Development

```bash
# 1. Setup virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
nano .env  # Add your API keys

# 4. Run server
make run
# OR
uvicorn adapter.main:app --reload
```

Access services:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **n8n**: http://localhost:5678 (admin/changeme)

## 📂 Project Structure

```
gun-registry-adapter/
├── adapter/                      # Core application
│   ├── main.py                   # FastAPI entry point
│   ├── api/
│   │   └── routes.py             # API endpoints
│   ├── core/
│   │   ├── engine.py             # Eligibility engine
│   │   ├── linkage.py            # Probabilistic linkage
│   │   ├── interfaces/           # Abstract interfaces
│   │   ├── model_a/              # PaddleOCR adapter
│   │   ├── model_b/              # GPT-4o + RapidFuzz
│   │   └── model_c/              # Self-healing (placeholder)
│   ├── config/                   # Settings & logging
│   ├── exceptions/               # Custom exceptions
│   ├── prompts/                  # LLM prompts
│   ├── self_healing/             # Model C (placeholder)
│   └── utils/                    # Privacy utilities
│
├── data/
│   ├── raw/                      # Raw data files
│   └── processed/                # Synthetic NICS records
│
├── docs/
│   ├── architecture.md           # Architecture decisions
│   └── n8n.png                   # Workflow visualization
│
├── models/                       # Model configs
├── scripts/                      # Utility scripts
│   ├── generate_synthetic_nics.py
│   └── test_api.py
│
├── tests/
│   ├── unit/                     # Unit tests
│   └── integration/              # Integration tests
│
├── workflow/                     # n8n workflow JSON
├── .env.example                  # Environment template
├── docker-compose.yml            # Docker services
├── Dockerfile                    # Container definition
├── Makefile                      # Development commands
└── requirements.txt              # Python dependencies
```

## 🛠️ Makefile Commands

```bash
# Setup
make setup          # Complete setup (venv + dependencies)
make check-env      # Verify .env configuration

# Development
make run            # Start development server
make shell          # Python shell

# Docker
make docker-up      # Start containers
make docker-down    # Stop containers
make docker-logs    # View logs

# Testing
make test           # Run all tests
make test-cov       # Run tests with coverage

# Code Quality
make format         # Format code
make lint           # Run linter

# Data
make generate-nics  # Generate synthetic NICS records

# Cleanup
make clean          # Remove cache files
make clean-all      # Complete cleanup

# Help
make help           # View all commands
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

**Response:**
```json
{
  "applicant_id": "test-12345",
  "decision": "APPROVED",
  "confidence": 0.92,
  "extracted_data": {
    "name": "John Doe",
    "dob": "1985-03-15",
    "state": "FL"
  },
  "risk_assessment": {
    "risk_score": 0.12,
    "confidence": 0.95
  }
}
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=adapter --cov-report=html

# Run specific tests
pytest tests/unit/
pytest tests/integration/
```

## 🔒 Security & Privacy

- **PII Hashing**: Applicant IDs are hashed in logs
- **No PII in Logs**: Names, DOBs, addresses sanitized
- **Environment Variables**: API keys stored in `.env` (never commit)

## ❓ Troubleshooting

### Docker Issues

**Containers keep restarting:**
```bash
docker-compose logs adapter
# Check for missing .env or invalid API keys
```

**Port already in use:**
```bash
# Change ports in .env
API_PORT=8001
N8N_PORT=5679
```

### API Issues

**Import errors:**
```bash
# Activate virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

**OpenAI API errors:**
```bash
# Verify API key in .env
cat .env | grep OPENAI_API_KEY
```

### Getting Help

```bash
# Check logs
docker-compose logs -f adapter
tail -f logs/audit.log

# Verify setup
make check-env
make health
```

## 📚 Documentation

- [Architecture Decisions](docs/architecture.md)
- [API Docs](http://localhost:8000/docs) (when running)
- [Makefile Help](Makefile) - Run `make help`

## 🔗 References

- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- [OpenAI API](https://platform.openai.com/docs)
- [Anthropic Claude](https://docs.anthropic.com/)
- [n8n Automation](https://n8n.io/)

---

**Built with:** Python 3.11, FastAPI, PaddleOCR, OpenAI GPT-4o mini, RapidFuzz, Docker
