#!/bin/bash

echo "🚀 Wallet Recovery Tool Setup"
echo "============================="

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python version: $python_version"

if (( $(echo "$python_version 3.11" | awk '{print ($1 < $2)}') )); then
    echo "❌ Python 3.11+ required. Please upgrade Python."
    exit 1
fi

echo "✅ Python version check passed"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r configs/requirements.txt

# Copy configuration template if not exists
if [ ! -f ".env" ]; then
    echo "⚙️  Copying configuration template..."
    cp configs/.env.example .env
    echo "📝 Please edit .env file with your API keys and database settings"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p results logs data/keys data/analysis

# Test basic functionality
echo "🧪 Testing basic functionality..."
python main.py --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Basic functionality test passed"
else
    echo "❌ Basic functionality test failed"
    exit 1
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys: nano .env"
echo "2. (Optional) Set up PostgreSQL database: python main.py setup"
echo "3. Test extraction: python main.py extract /path/to/dataset --quick"
echo "4. Check balances: python main.py scan"
echo "5. Start monitoring: python main.py monitor"
echo ""
echo "For detailed instructions, see README.md"