#!/bin/bash
# 🎯 Advanced Wallet Recovery System - Setup Script
# Professional-grade cryptocurrency wallet recovery platform

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║              🎯 WALLET RECOVERY SYSTEM SETUP                     ║"
echo "║                Professional Installation                         ║"
echo "╚══════════════════════════════════════════════════════════════════╝"

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python version
print_status "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    MAJOR_VERSION=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    MINOR_VERSION=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$MAJOR_VERSION" -eq 3 ] && [ "$MINOR_VERSION" -ge 8 ]; then
        print_success "Python $PYTHON_VERSION detected ✅"
        PYTHON_CMD=python3
    else
        print_error "Python 3.8+ required. Found: $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 not found. Please install Python 3.8+ first."
    exit 1
fi

# Create virtual environment
print_status "Creating virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    print_success "Virtual environment created ✅"
else
    print_warning "Virtual environment already exists, skipping..."
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate || {
    print_error "Failed to activate virtual environment"
    exit 1
}
print_success "Virtual environment activated ✅"

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
print_success "Pip upgraded ✅"

# Install requirements
print_status "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt > /dev/null 2>&1
    print_success "Dependencies installed ✅"
else
    print_warning "requirements.txt not found, installing core packages..."
    pip install requests eth-keys eth-utils bip-utils web3 bit debugpy plyvel > /dev/null 2>&1
    print_success "Core packages installed ✅"
fi

# Create configuration files
print_status "Setting up configuration files..."

# API config
if [ ! -f "configs/api_config.json" ]; then
    if [ -f "configs/api_config.json.example" ]; then
        cp configs/api_config.json.example configs/api_config.json
        print_success "API config template created ✅"
        print_warning "Please edit configs/api_config.json with your API keys"
    fi
fi

# Environment file
if [ ! -f ".env" ]; then
    cat > .env << EOF
# Wallet Recovery System Environment
WALLET_RECOVERY_MODE=production
DEBUG_LEVEL=info
MAX_PARALLEL_CHECKS=10
ENTROPY_THRESHOLD=0.85
API_DELAY_MS=100
MAX_RETRIES=3
TIMEOUT_SECONDS=30
EOF
    print_success "Environment file created ✅"
fi

# Create directories if they don't exist
print_status "Creating directory structure..."
mkdir -p data/keys data/addresses data/scans data/balances
mkdir -p reports/jackpots reports/campaigns reports/audits
mkdir -p logs
print_success "Directory structure ready ✅"

# Set permissions
print_status "Setting file permissions..."
chmod +x setup.sh 2>/dev/null || true
chmod 644 .env 2>/dev/null || true
chmod 600 configs/api_config.json 2>/dev/null || true
print_success "Permissions configured ✅"

# Run system check
print_status "Running system health check..."
if python system_auditor.py > /dev/null 2>&1; then
    print_success "System health check passed ✅"
else
    print_warning "System health check had issues, but setup completed"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                 🎉 SETUP COMPLETED SUCCESSFULLY                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 NEXT STEPS:"
echo "   1. Edit configs/api_config.json with your API keys"
echo "   2. Run: source venv/bin/activate"
echo "   3. Test: python system_auditor.py"
echo "   4. Start hunting: python scripts/hunters/laser_focus_hunter.py"
echo ""
echo "📚 DOCUMENTATION:"
echo "   • README.md - Complete usage guide"
echo "   • docs/ - Technical documentation"
echo "   • reports/ - System reports and discoveries"
echo ""
echo "🎯 SYSTEM STATUS: READY FOR WALLET RECOVERY OPERATIONS"
echo ""
