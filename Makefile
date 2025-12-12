# Gun Registry Adapter - Makefile
# Simple automation for build, run, test, and formatting

# ============================================================================
# Variables
# ============================================================================

PYTHON := python3.11
VENV := venv
BIN := $(VENV)/bin
PIP := $(BIN)/pip
PYTEST := $(BIN)/pytest
BLACK := $(BIN)/black
ISORT := $(BIN)/isort
RUFF := $(BIN)/ruff

# Source directories
SRC_DIR := adapter
TEST_DIR := tests
SCRIPTS_DIR := scripts

# Docker
DOCKER_COMPOSE := docker-compose
DOCKER_IMAGE := gun-registry-adapter
CONTAINER_NAME := gun_registry_adapter

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

# ============================================================================
# Help
# ============================================================================

.PHONY: help
help:  ## Show this help message
	@echo "$(GREEN)Gun Registry Adapter - Makefile Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Setup:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; /Setup:/ {found=1; next} /^[A-Z]/ {found=0} found {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Development:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; /Development:/ {found=1; next} /^[A-Z]/ {found=0} found {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Testing:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; /Testing:/ {found=1; next} /^[A-Z]/ {found=0} found {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Code Quality:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; /Code Quality:/ {found=1; next} /^[A-Z]/ {found=0} found {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Docker:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; /Docker:/ {found=1; next} /^[A-Z]/ {found=0} found {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Data:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; /Data:/ {found=1; next} /^[A-Z]/ {found=0} found {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Cleanup:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; /Cleanup:/ {found=1; next} /^[A-Z]/ {found=0} found {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# ============================================================================
# Setup
# ============================================================================

.PHONY: install
install: venv  ## Install all dependencies
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

.PHONY: venv
venv:  ## Create virtual environment
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(YELLOW)Creating virtual environment...$(NC)"; \
		$(PYTHON) -m venv $(VENV); \
		echo "$(GREEN)✓ Virtual environment created$(NC)"; \
	else \
		echo "$(GREEN)✓ Virtual environment already exists$(NC)"; \
	fi

.PHONY: setup
setup: venv install  ## Complete setup (venv + dependencies)
	@echo "$(YELLOW)Setting up environment...$(NC)"
	@if [ ! -f ".env" ]; then \
		cp .env.example .env; \
		echo "$(GREEN)✓ .env file created from template$(NC)"; \
		echo "$(YELLOW)⚠️  Edit .env and add your API keys!$(NC)"; \
	fi
	@mkdir -p data/raw/nics_data data/processed logs
	@echo "$(GREEN)✓ Setup complete!$(NC)"

# ============================================================================
# Development
# ============================================================================

.PHONY: run
run:  ## Run development server
	@echo "$(YELLOW)Starting development server...$(NC)"
	cd $(shell pwd) && PYTHONPATH=. $(BIN)/uvicorn adapter.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: dev
dev: run  ## Alias for 'make run'

.PHONY: shell
shell:  ## Open Python shell with venv activated
	@echo "$(YELLOW)Opening Python shell...$(NC)"
	$(BIN)/python

# ============================================================================
# Testing
# ============================================================================

.PHONY: test
test:  ## Run all tests
	@echo "$(YELLOW)Running tests...$(NC)"
	$(PYTEST) tests/ -v

.PHONY: test-unit
test-unit:  ## Run unit tests only
	@echo "$(YELLOW)Running unit tests...$(NC)"
	$(PYTEST) tests/unit/ -v

.PHONY: test-integration
test-integration:  ## Run integration tests only
	@echo "$(YELLOW)Running integration tests...$(NC)"
	$(PYTEST) tests/integration/ -v

.PHONY: test-cov
test-cov:  ## Run tests with coverage report
	@echo "$(YELLOW)Running tests with coverage...$(NC)"
	$(PYTEST) tests/ --cov=adapter --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✓ Coverage report generated: htmlcov/index.html$(NC)"

.PHONY: test-watch
test-watch:  ## Run tests in watch mode
	@echo "$(YELLOW)Running tests in watch mode...$(NC)"
	$(PYTEST) tests/ -v --looponfail

# ============================================================================
# Code Quality
# ============================================================================

.PHONY: format
format:  ## Format code with black and isort
	@echo "$(YELLOW)Formatting code...$(NC)"
	$(BLACK) $(SRC_DIR) $(TEST_DIR) $(SCRIPTS_DIR)
	$(ISORT) $(SRC_DIR) $(TEST_DIR) $(SCRIPTS_DIR)
	@echo "$(GREEN)✓ Code formatted$(NC)"

.PHONY: format-check
format-check:  ## Check code formatting without changes
	@echo "$(YELLOW)Checking code formatting...$(NC)"
	$(BLACK) --check $(SRC_DIR) $(TEST_DIR) $(SCRIPTS_DIR)
	$(ISORT) --check-only $(SRC_DIR) $(TEST_DIR) $(SCRIPTS_DIR)

.PHONY: lint
lint:  ## Run linter (ruff)
	@echo "$(YELLOW)Running linter...$(NC)"
	$(RUFF) check $(SRC_DIR) $(TEST_DIR) $(SCRIPTS_DIR)

.PHONY: lint-fix
lint-fix:  ## Run linter and auto-fix issues
	@echo "$(YELLOW)Running linter with auto-fix...$(NC)"
	$(RUFF) check --fix $(SRC_DIR) $(TEST_DIR) $(SCRIPTS_DIR)

.PHONY: type-check
type-check:  ## Run type checker (mypy)
	@echo "$(YELLOW)Running type checker...$(NC)"
	$(BIN)/mypy $(SRC_DIR)

.PHONY: check
check: format-check lint type-check  ## Run all code quality checks

.PHONY: fix
fix: format lint-fix  ## Auto-fix all code quality issues

# ============================================================================
# Docker
# ============================================================================

.PHONY: docker-build
docker-build:  ## Build Docker image
	@echo "$(YELLOW)Building Docker image...$(NC)"
	$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✓ Docker image built$(NC)"

.PHONY: docker-up
docker-up:  ## Start Docker containers
	@echo "$(YELLOW)Starting Docker containers...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✓ Containers started$(NC)"
	@echo "$(YELLOW)API: http://localhost:8000$(NC)"
	@echo "$(YELLOW)n8n: http://localhost:5678$(NC)"

.PHONY: docker-down
docker-down:  ## Stop Docker containers
	@echo "$(YELLOW)Stopping Docker containers...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✓ Containers stopped$(NC)"

.PHONY: docker-logs
docker-logs:  ## View Docker logs
	$(DOCKER_COMPOSE) logs -f

.PHONY: docker-restart
docker-restart: docker-down docker-up  ## Restart Docker containers

.PHONY: docker-clean
docker-clean:  ## Remove Docker containers and images
	@echo "$(YELLOW)Cleaning Docker resources...$(NC)"
	$(DOCKER_COMPOSE) down -v --rmi all
	@echo "$(GREEN)✓ Docker resources cleaned$(NC)"

# ============================================================================
# Data
# ============================================================================

.PHONY: generate-nics
generate-nics:  ## Generate synthetic NICS records
	@echo "$(YELLOW)Generating synthetic NICS records...$(NC)"
	$(BIN)/python scripts/generate_synthetic_nics.py
	@echo "$(GREEN)✓ Synthetic NICS records generated$(NC)"

.PHONY: check-data
check-data:  ## Check if required data files exist
	@echo "$(YELLOW)Checking data files...$(NC)"
	@if [ -f "data/raw/nics_data/nics-firearm-background-checks.csv" ]; then \
		echo "$(GREEN)✓ NICS aggregate data found$(NC)"; \
	else \
		echo "$(RED)✗ NICS aggregate data not found$(NC)"; \
		echo "  Download from: https://github.com/BuzzFeedNews/nics-firearm-background-checks/"; \
	fi
	@if [ -f "data/processed/synthetic_nics_records.json" ]; then \
		echo "$(GREEN)✓ Synthetic NICS records found$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Synthetic NICS records not found$(NC)"; \
		echo "  Run: make generate-nics"; \
	fi
	@if [ -d "data/raw/synthetic_cards" ]; then \
		COUNT=$$(ls -1 data/raw/synthetic_cards/*.png 2>/dev/null | wc -l); \
		echo "$(GREEN)✓ Found $$COUNT synthetic driver license images$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Synthetic driver license images not found$(NC)"; \
	fi

# ============================================================================
# Cleanup
# ============================================================================

.PHONY: clean
clean:  ## Remove Python cache files
	@echo "$(YELLOW)Cleaning Python cache files...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	@echo "$(GREEN)✓ Python cache cleaned$(NC)"

.PHONY: clean-logs
clean-logs:  ## Remove log files
	@echo "$(YELLOW)Cleaning log files...$(NC)"
	rm -rf logs/*.log
	@echo "$(GREEN)✓ Logs cleaned$(NC)"

.PHONY: clean-data
clean-data:  ## Remove generated data files
	@echo "$(YELLOW)Cleaning generated data...$(NC)"
	rm -rf data/processed/*.json
	@echo "$(GREEN)✓ Generated data cleaned$(NC)"

.PHONY: clean-all
clean-all: clean clean-logs docker-clean  ## Remove all generated files and Docker resources
	@echo "$(YELLOW)Removing virtual environment...$(NC)"
	rm -rf $(VENV)
	@echo "$(GREEN)✓ Complete cleanup finished$(NC)"

# ============================================================================
# Utilities
# ============================================================================

.PHONY: check-env
check-env:  ## Check if .env file is configured
	@echo "$(YELLOW)Checking environment configuration...$(NC)"
	@if [ ! -f ".env" ]; then \
		echo "$(RED)✗ .env file not found$(NC)"; \
		echo "  Run: cp .env.example .env"; \
		exit 1; \
	fi
	@if grep -q "sk-proj-your-openai-api-key-here" .env 2>/dev/null; then \
		echo "$(RED)✗ OPENAI_API_KEY not configured$(NC)"; \
		exit 1; \
	fi
	@if grep -q "sk-ant-your-anthropic-api-key-here" .env 2>/dev/null; then \
		echo "$(RED)✗ ANTHROPIC_API_KEY not configured$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ Environment configured$(NC)"

.PHONY: health
health:  ## Check API health endpoint
	@echo "$(YELLOW)Checking API health...$(NC)"
	@curl -s http://localhost:8000/api/v1/health | $(BIN)/python -m json.tool || \
		echo "$(RED)✗ API not responding (is the server running?)$(NC)"

.PHONY: docs
docs:  ## Open API documentation in browser
	@echo "$(YELLOW)Opening API documentation...$(NC)"
	@open http://localhost:8000/docs 2>/dev/null || \
		xdg-open http://localhost:8000/docs 2>/dev/null || \
		echo "$(YELLOW)API Docs: http://localhost:8000/docs$(NC)"

.PHONY: tree
tree:  ## Show project structure
	@echo "$(YELLOW)Project Structure:$(NC)"
	@tree -L 3 -I 'venv|__pycache__|*.pyc|*.egg-info|.git|node_modules|htmlcov' .

# ============================================================================
# Quick Commands
# ============================================================================

.PHONY: all
all: setup generate-nics  ## Complete setup and data generation

.PHONY: start
start: run  ## Start development server (alias for run)

.PHONY: restart
restart:  ## Kill existing server and restart
	@pkill -f "uvicorn adapter.main:app" 2>/dev/null || true
	@sleep 1
	@make run

# Default target
.DEFAULT_GOAL := help
