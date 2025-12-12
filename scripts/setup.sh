#!/bin/bash
# Gun Registry Adapter - Quick Setup Script

set -e  # Exit on error

echo "=========================================================================="
echo "Gun Registry Adapter - Setup Script"
echo "=========================================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo -e "\n${YELLOW}Checking Python version...${NC}"
if command -v python3.11 &> /dev/null; then
    echo -e "${GREEN}✓ Python 3.11 found${NC}"
    PYTHON=python3.11
elif command -v python3 &> /dev/null; then
    VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [ "$VERSION" == "3.11" ]; then
        echo -e "${GREEN}✓ Python 3.11 found${NC}"
        PYTHON=python3
    else
        echo -e "${RED}✗ Python 3.11 required, found $VERSION${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Python 3.11 not found${NC}"
    exit 1
fi

# Create virtual environment
echo -e "\n${YELLOW}Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    $PYTHON -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "\n${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Upgrade pip
echo -e "\n${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓ pip upgraded${NC}"

# Install dependencies
echo -e "\n${YELLOW}Installing dependencies...${NC}"
echo "This may take a few minutes (PaddleOCR is large)..."
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create .env file if it doesn't exist
echo -e "\n${YELLOW}Setting up environment configuration...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created from template${NC}"
    echo -e "${YELLOW}⚠️  IMPORTANT: Edit .env and add your API keys:${NC}"
    echo "   - OPENAI_API_KEY"
    echo "   - ANTHROPIC_API_KEY"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Create necessary directories
echo -e "\n${YELLOW}Creating data directories...${NC}"
mkdir -p data/raw/nics_data data/processed logs
echo -e "${GREEN}✓ Directories created${NC}"

# Check for NICS data
echo -e "\n${YELLOW}Checking for NICS data...${NC}"
if [ -f "data/raw/nics_data/nics-firearm-background-checks.csv" ]; then
    echo -e "${GREEN}✓ NICS data found${NC}"

    # Offer to generate synthetic records
    read -p "Generate synthetic NICS records? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "\n${YELLOW}Generating synthetic NICS records...${NC}"
        python scripts/generate_synthetic_nics.py
        echo -e "${GREEN}✓ Synthetic NICS records generated${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  NICS data not found${NC}"
    echo "Download from: https://github.com/BuzzFeedNews/nics-firearm-background-checks/"
    echo "Place in: data/raw/nics_data/nics-firearm-background-checks.csv"
    echo "Then run: python scripts/generate_synthetic_nics.py"
fi

# Check for Docker
echo -e "\n${YELLOW}Checking Docker installation...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker found${NC}"

    if command -v docker-compose &> /dev/null; then
        echo -e "${GREEN}✓ Docker Compose found${NC}"
    else
        echo -e "${YELLOW}⚠️  Docker Compose not found (optional)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Docker not found (optional for deployment)${NC}"
fi

# Summary
echo -e "\n=========================================================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env and add your API keys:"
echo "   - OPENAI_API_KEY=sk-proj-your-key-here"
echo "   - ANTHROPIC_API_KEY=sk-ant-your-key-here"
echo ""
echo "2. Run the development server:"
echo "   python adapter/main.py"
echo ""
echo "3. Or use Docker:"
echo "   docker-compose up -d"
echo ""
echo "4. Access the API:"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - n8n: http://localhost:5678 (Docker only)"
echo ""
echo "5. Run tests:"
echo "   pytest"
echo ""
echo "=========================================================================="
