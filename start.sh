#!/bin/bash

# ============================================================================
# Multi-Agent LLM System - Start Script
# ============================================================================

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🤖 Starting Multi-Agent LLM System"
echo "=================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found${NC}"
    echo "Running setup first..."
    ./setup.sh
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Check for .env
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo "Creating from template..."
    cp .env.example .env
    echo "Please edit .env and add your API keys, then run this script again."
    exit 1
fi

# Start the application
echo -e "${GREEN}✅ Starting Streamlit UI...${NC}"
echo ""
echo "Opening browser at http://localhost:8501"
echo "Press Ctrl+C to stop the server"
echo ""

streamlit run streamlit_app.py
