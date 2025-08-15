#!/bin/bash
# Wallet Recovery Tools - Setup Script

echo "🔐 Setting up Wallet Recovery Tools..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p data/{results,reports,configs}
mkdir -p logs

echo "✅ Setup complete!"
echo "📖 See README.md for usage instructions"
echo "⚠️  Remember: Keep your API keys secure and never commit personal data!"