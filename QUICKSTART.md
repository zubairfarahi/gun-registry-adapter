# Gun Registry Adapter - Quick Start Guide

Get up and running in 5 minutes! 🚀

## Prerequisites Checklist

- [ ] Python 3.11 installed
- [ ] OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- [ ] Anthropic API key ([Get one here](https://console.anthropic.com/settings/keys))
- [ ] (Optional) Docker & Docker Compose

## 🚀 Fast Track Setup

### Option 1: Using Makefile (Recommended)

```bash
# 1. Complete setup in one command
make setup

# 2. Add your API keys to .env
nano .env  # or use your favorite editor
# Set:
#   OPENAI_API_KEY=sk-proj-your-actual-key
#   ANTHROPIC_API_KEY=sk-ant-your-actual-key

# 3. Download NICS data and generate synthetic records
# Download from: https://github.com/BuzzFeedNews/nics-firearm-background-checks/
# Place in: data/raw/nics_data/nics-firearm-background-checks.csv
make generate-nics

# 4. Start the server
make run
```

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add your API keys

# 4. Generate data
python scripts/generate_synthetic_nics.py

# 5. Run server
python adapter/main.py
```

### Option 3: Using Docker

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env and add your API keys

# 2. Generate synthetic data (before Docker)
python scripts/generate_synthetic_nics.py

# 3. Start everything
make docker-up
# or: docker-compose up -d
```

## 📡 Testing the API

Once the server is running, try these commands:

### 1. Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### 2. Interactive API Docs
Open in browser: http://localhost:8000/docs

### 3. Sample Eligibility Check

First, encode a test image:
```bash
# Encode an image to base64
base64 data/raw/synthetic_cards/00509_driver_license_front_texas_011898.png > test_image.txt
```

Then make the API call:
```bash
curl -X POST http://localhost:8000/api/v1/eligibility \
  -H "Content-Type: application/json" \
  -d "{
    \"applicant_id\": \"test-12345\",
    \"id_image_base64\": \"$(cat test_image.txt)\"
  }" | python -m json.tool
```

Expected response:
```json
{
  "applicant_id": "test-12345",
  "decision": "APPROVED" or "DENIED" or "MANUAL_REVIEW",
  "confidence": 0.92,
  "extracted_data": {
    "name": "...",
    "dob": "YYYY-MM-DD",
    "state": "TX",
    ...
  },
  "risk_assessment": {...},
  "linkage_result": {...}
}
```

## 🧪 Running Tests

```bash
# All tests
make test

# With coverage
make test-cov

# Unit tests only
make test-unit
```

## 🔧 Common Makefile Commands

```bash
make help              # Show all available commands
make setup             # Complete setup
make run               # Start development server
make test              # Run tests
make test-cov          # Run tests with coverage
make format            # Format code (black + isort)
make lint              # Run linter
make check             # Run all quality checks
make docker-up         # Start with Docker
make docker-logs       # View Docker logs
make generate-nics     # Generate synthetic NICS records
make clean             # Clean cache files
```

## 📊 Verifying Installation

Run this checklist:

```bash
# 1. Check Python version
python --version  # Should be 3.11+

# 2. Check virtual environment
which python  # Should point to venv/bin/python

# 3. Check dependencies
pip list | grep -E "fastapi|paddleocr|openai|anthropic|rapidfuzz"

# 4. Check environment
make check-env  # Verifies API keys are set

# 5. Check data files
make check-data  # Verifies data files exist

# 6. Check API health
make health  # Tests if server is running
```

## 🎯 Next Steps

1. **Explore API Docs**: http://localhost:8000/docs
2. **View n8n Workflow**: http://localhost:5678 (if using Docker)
3. **Read Architecture**: See [CLAUDE.md](CLAUDE.md) for detailed architecture
4. **Run Tests**: `make test-cov` to see code coverage
5. **Try Different Images**: Test with various driver license images

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'paddleocr'"

**Solution:**
```bash
source venv/bin/activate  # Make sure venv is activated
pip install -r requirements.txt
```

### Issue: "OpenAI API Error: Invalid API key"

**Solution:**
```bash
# Check your .env file
cat .env | grep OPENAI_API_KEY
# Make sure it's a valid key starting with "sk-proj-"
```

### Issue: "No NICS records available for matching"

**Solution:**
```bash
# Generate synthetic NICS records
make generate-nics
# Or manually:
python scripts/generate_synthetic_nics.py
```

### Issue: "Port 8000 already in use"

**Solution:**
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9
# Or change port in .env:
# API_PORT=8001
```

### Issue: Docker container won't start

**Solution:**
```bash
# Check Docker logs
make docker-logs

# Rebuild from scratch
make docker-clean
make docker-build
make docker-up
```

## 📝 Configuration Quick Reference

Key `.env` variables:

```bash
# API Keys (REQUIRED)
OPENAI_API_KEY=sk-proj-your-key
ANTHROPIC_API_KEY=sk-ant-your-key

# Model Thresholds
MODEL_A_CONFIDENCE_THRESHOLD=0.8      # OCR confidence
MODEL_B_RISK_THRESHOLD=0.7            # Risk score
LINKAGE_CONFIDENCE_THRESHOLD=0.7      # Linkage match

# Data Paths
USE_SYNTHETIC_NICS=true
SYNTHETIC_NICS_PATH=data/processed/synthetic_nics_records.json

# Self-Healing (Model C)
SELF_HEALING_ENABLED=true
AUTO_APPLY_FIXES=false  # NEVER true in production!

# Logging
LOG_LEVEL=INFO
LOG_PII=false  # NEVER true in production!
```

## 🎓 Learning Resources

- **API Documentation**: http://localhost:8000/docs (when running)
- **Architecture Guide**: [CLAUDE.md](CLAUDE.md)
- **Dataset Analysis**: [docs/dataset_eval.md](docs/dataset_eval.md)
- **Implementation Guides**: `.claude/commands/` directory
- **Full README**: [README.md](README.md)

## 💡 Pro Tips

1. **Use Makefile**: All common tasks have simple `make` commands
2. **Check Coverage**: Run `make test-cov` and open `htmlcov/index.html`
3. **Format on Save**: Configure your IDE to run `make format` on save
4. **Docker for Demos**: Use `make docker-up` for complete demo environment
5. **Watch Mode**: Use `make test-watch` during development

## 🚢 Production Checklist

Before deploying to production:

- [ ] Set `AUTO_APPLY_FIXES=false` in `.env`
- [ ] Set `LOG_PII=false` in `.env`
- [ ] Set `DEBUG=false` in `.env`
- [ ] Configure real database (not SQLite)
- [ ] Enable encryption (`ENABLE_ENCRYPTION=true`)
- [ ] Set up monitoring (Prometheus, Sentry)
- [ ] Review CORS origins
- [ ] Set strong `SECRET_KEY`
- [ ] Configure backup strategy
- [ ] Set up log rotation
- [ ] Enable rate limiting
- [ ] Run security audit: `make check`

---

**Need Help?** Check the [README.md](README.md) or [CLAUDE.md](CLAUDE.md) for detailed information.

**Ready to build?** Run `make setup && make run` and you're good to go! 🎉
