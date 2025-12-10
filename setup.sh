#!/bin/bash

# ============================================================================
# Multi-Agent LLM System - Setup Script
# ============================================================================

set -e  # Exit on error

echo "🤖 Multi-Agent LLM System - Setup"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "📋 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
    echo -e "${RED}❌ Python 3.11+ is required. Found: $PYTHON_VERSION${NC}"
    echo "Please install Python 3.11 or higher."
    exit 1
fi

echo -e "${GREEN}✅ Python $PYTHON_VERSION detected${NC}"
echo ""

# Create virtual environment
echo "🔨 Creating virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
    read -p "Do you want to recreate it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
    fi
else
    python3 -m venv venv
fi
echo -e "${GREEN}✅ Virtual environment created${NC}"
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip
echo -e "${GREEN}✅ pip upgraded${NC}"
echo ""

# Install requirements
echo "📦 Installing requirements..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Requirements installed${NC}"
else
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi
echo ""

# Create directories
echo "📁 Creating directories..."
mkdir -p workspace
mkdir -p logs
mkdir -p cache
mkdir -p data
echo -e "${GREEN}✅ Directories created${NC}"
echo ""

# Setup environment file
echo "⚙️  Setting up environment configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env from template${NC}"
        echo -e "${YELLOW}⚠️  Please edit .env and add your API keys${NC}"
    else
        echo -e "${RED}❌ .env.example not found${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  .env already exists${NC}"
fi
echo ""

# Check for API keys
echo "🔑 Checking API keys..."
if [ -f ".env" ]; then
    source .env
    
    if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" == "sk-your-openai-api-key-here" ]; then
        echo -e "${RED}❌ OpenAI API key not configured${NC}"
        echo "Please add your OpenAI API key to .env file"
    else
        echo -e "${GREEN}✅ OpenAI API key configured${NC}"
    fi
    
    if [ -z "$SERPAPI_API_KEY" ] || [ "$SERPAPI_API_KEY" == "your-serpapi-key-here" ]; then
        echo -e "${YELLOW}⚠️  SerpAPI key not configured (optional)${NC}"
    else
        echo -e "${GREEN}✅ SerpAPI key configured${NC}"
    fi
fi
echo ""

# Run tests (optional)
echo "🧪 Running tests..."
read -p "Do you want to run tests? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -d "tests" ]; then
        pytest tests/ -v
        echo -e "${GREEN}✅ Tests completed${NC}"
    else
        echo -e "${YELLOW}⚠️  No tests directory found${NC}"
    fi
fi
echo ""

# Final instructions
echo "============================================"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Run the system:"
echo "   - CLI: python main_system.py 'your task here'"
echo "   - Web UI: streamlit run streamlit_app.py"
echo ""
echo "To activate the environment later, run:"
echo "   source venv/bin/activate"
echo ""
echo "Happy building! 🚀"
