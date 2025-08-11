#!/bin/bash

# Fresh Start Setup for Wallet Tool
# This script sets up the wallet recovery tool from the beginning with clean, objective approach

echo "🚀 WALLET TOOL - FRESH START SETUP"
echo "=================================="
echo "Setting up clean, objective wallet recovery tool"
echo

# Create fresh directories
echo "📁 Creating clean workspace..."
rm -f address_tracking.db unified_scanner.log *.json 2>/dev/null || true

# Ensure all dependencies are installed
echo "📦 Installing Python dependencies..."
pip3 install --quiet plyvel requests bip-utils eth-keys eth-utils 2>/dev/null || {
    echo "⚠️  Some dependencies may not install - checking what's available..."
    pip3 install --quiet requests 2>/dev/null || echo "requests installation failed"
}

# Make scripts executable  
chmod +x unified_wallet_scanner.py
chmod +x top_wallet_finder.py

echo "✅ Setup complete!"
echo
echo "🎯 WORKFLOW - FROM EXTRACTION TO TOP 100:"
echo "=========================================="
echo
echo "Step 1: Extract all private keys and addresses (no balance checks)"
echo "   python3 unified_wallet_scanner.py --extract-only /path/to/your/directory"
echo
echo "Step 2: Analyze data and find top 100 most promising addresses"
echo "   python3 top_wallet_finder.py extracted_addresses_all.json"
echo
echo "Step 3: Check balances for only the top 100 addresses"
echo "   python3 unified_wallet_scanner.py --check-balances top_100_wallets.json"
echo
echo "🔍 Key Features:"
echo "- Completely objective analysis (no hardcoded assumptions)"
echo "- Data-driven prioritization based on wallet usage patterns"
echo "- Entropy analysis for private key legitimacy"
echo "- Geographic and wallet type analysis"
echo "- Focus on top 100 most promising addresses only"
echo
echo "📊 Ready to start! What directory do you want to analyze?"
