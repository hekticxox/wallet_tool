#!/bin/bash
# Production Setup Script for Crypto Wallet Recovery Tool

echo "🔧 Crypto Wallet Recovery Tool - Setup"
echo "======================================"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PYTHON_VERSION detected"

# Check if we're already in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment already active: $(basename $VIRTUAL_ENV)"
else
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo "📦 Creating virtual environment..."
        python3 -m venv venv
        
        if [ $? -ne 0 ]; then
            echo "❌ Failed to create virtual environment"
            exit 1
        fi
    fi
    
    echo "🔄 Activating virtual environment..."
    source venv/bin/activate
fi

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install requirements
echo "📥 Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    echo "Please check requirements.txt and try again"
    exit 1
fi

# Make scripts executable
echo "🔧 Setting up management scripts..."
chmod +x monitor_checker.sh
chmod +x restart_checker.sh  
chmod +x auto_recovery.sh

# Create example API config
if [ ! -f "api_config.json" ]; then
    echo "📝 Creating API configuration template..."
    cat > api_config.json << EOF
{
  "etherscan_api_key": "YourApiKeyToken",
  "rate_limits": {
    "ethereum": 5,
    "bitcoin": 1,
    "solana": 2
  },
  "timeouts": {
    "ethereum": 15,
    "bitcoin": 15,
    "solana": 10
  }
}
EOF
    echo "   📄 Created api_config.json (optional configuration)"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Quick Start:"
echo "   1. python3 wallet_analysis_clean.py    # Main analysis"
echo "   2. python3 continuous_checker.py       # Balance checking"
echo "   3. ./monitor_checker.sh                # Monitor progress"
echo ""
echo "📚 For detailed instructions, see README.md"
echo ""

# Show current directory contents
echo "📁 Project files:"
ls -la *.py *.sh *.md requirements.txt 2>/dev/null | grep -v "^d"
