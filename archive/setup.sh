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

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        echo "Make sure python3-venv is installed: apt install python3-venv"
        exit 1
    fi
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Check if we're in the venv
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

echo "✅ Virtual environment active: $(basename $VIRTUAL_ENV)"

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
    cp api_config.json.example api_config.json
    echo "   📄 Created api_config.json from template"
    echo "   ✏️  You can customize API settings if needed"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Quick Start:"
echo "   source venv/bin/activate          # Activate virtual environment"
echo "   python3 wallet_analysis.py       # Main analysis"
echo "   python3 continuous_checker.py    # Balance checking"  
echo "   ./monitor_checker.sh             # Monitor progress"
echo ""
echo "📚 For detailed instructions, see README.md"
echo ""

# Show current directory contents
echo "📁 Ready to use:"
ls -la *.py *.sh README.md requirements.txt api_config.json* 2>/dev/null | head -10
