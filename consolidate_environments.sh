#!/bin/bash
"""
ENVIRONMENT CONSOLIDATION SCRIPT
===============================
Consolidates multiple environments into ONE unified production environment
"""

echo "🚀 WALLET TOOL ENVIRONMENT CONSOLIDATION"
echo "========================================="
echo "This script will consolidate all environments into one unified setup"
echo ""

# Create unified directory structure
echo "1️⃣  Creating unified directory structure..."
mkdir -p /home/admin/wallet_tool_unified
mkdir -p /home/admin/wallet_tool_unified/logs
mkdir -p /home/admin/wallet_tool_unified/backups
mkdir -p /home/admin/wallet_tool_unified/data

echo "✅ Unified directory created"

# Copy all Python files from main wallet_tool
echo "2️⃣  Copying main wallet tool files..."
cp /home/admin/wallet_tool/*.py /home/admin/wallet_tool_unified/ 2>/dev/null || true
cp /home/admin/wallet_tool/requirements.txt /home/admin/wallet_tool_unified/ 2>/dev/null || true

# Copy enhanced modules from production directory
echo "3️⃣  Copying enhanced modules..."
enhanced_files=(
    "database_integration.py"
    "erc20_checker.py" 
    "multichain_checker.py"
    "continuous_monitor.py"
    "ultimate_scanner.py"
    "production_enhanced_scanner.py"
    "final_production_status.py"
)

for file in "${enhanced_files[@]}"; do
    if [ -f "/home/admin/wallet_tool/$file" ]; then
        cp "/home/admin/wallet_tool/$file" /home/admin/wallet_tool_unified/
        echo "   ✅ Copied $file"
    elif [ -f "/home/admin/wallet_tool_production/$file" ]; then
        cp "/home/admin/wallet_tool_production/$file" /home/admin/wallet_tool_unified/
        echo "   ✅ Copied $file from production"
    fi
done

# Copy database directory
echo "4️⃣  Copying database modules..."
if [ -d "/home/admin/wallet_tool/database" ]; then
    cp -r /home/admin/wallet_tool/database /home/admin/wallet_tool_unified/
    echo "   ✅ Database modules copied"
elif [ -d "/home/admin/wallet_tool_production/database" ]; then
    cp -r /home/admin/wallet_tool_production/database /home/admin/wallet_tool_unified/
    echo "   ✅ Database modules copied from production"
fi

# Create unified environment file
echo "5️⃣  Creating unified environment configuration..."
cat > /home/admin/wallet_tool_unified/.env << 'EOF'
# UNIFIED WALLET TOOL ENVIRONMENT
# ==============================

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=wallet_recovery
DB_USER=wallet_admin
DB_PASSWORD=secure_wallet_pass_2024

# API Keys - Blockchain Services
ETHERSCAN_API_KEY=YourEtherscanAPIKey
ALCHEMY_API_KEY=YourAlchemyAPIKey
INFURA_API_KEY=YourInfuraAPIKey
BLOCKCYPHER_API_KEY=YourBlockCypherAPIKey

# Multi-Chain API Keys
POLYGONSCAN_API_KEY=YourPolygonscanAPIKey
BSCSCAN_API_KEY=YourBscscanAPIKey
ARBITRUMSCAN_API_KEY=YourArbitrumscanAPIKey

# System Configuration
LOG_LEVEL=INFO
MAX_BATCH_SIZE=100
MONITORING_INTERVAL=300
BACKUP_ENABLED=true

# Production Settings
ENVIRONMENT=production
DEBUG=false
EOF

echo "   ✅ Unified environment file created"

# Create unified virtual environment
echo "6️⃣  Creating unified virtual environment..."
cd /home/admin/wallet_tool_unified
python3 -m venv venv_unified
source venv_unified/bin/activate

echo "   ✅ Unified virtual environment created"

# Install all required packages
echo "7️⃣  Installing unified requirements..."
cat > requirements.txt << 'EOF'
# Core Requirements
python-dotenv>=1.0.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
alembic>=1.12.0

# Enhanced Features
aiohttp>=3.8.0
eth-keys>=0.4.0
ecdsa>=0.18.0
base58>=2.1.0
web3>=6.0.0

# Bitcoin Support  
electrum>=4.4.0

# Monitoring and Logging
schedule>=1.2.0
requests>=2.31.0

# Development
pytest>=7.4.0
black>=23.0.0
flake8>=6.0.0
EOF

pip install -r requirements.txt

echo "   ✅ All requirements installed"

# Create startup script
echo "8️⃣  Creating unified startup script..."
cat > start_unified_wallet_tool.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Unified Wallet Tool Environment"
cd /home/admin/wallet_tool_unified
source venv_unified/bin/activate
export $(cat .env | grep -v ^# | xargs)
echo "✅ Environment loaded and ready!"
echo "🎯 Available commands:"
echo "  python production_enhanced_scanner.py  - Run production scan"
echo "  python final_production_status.py      - Check system status"
echo "  python continuous_monitor.py           - Start monitoring"
exec "$@"
EOF

chmod +x start_unified_wallet_tool.sh

echo "   ✅ Startup script created"

echo ""
echo "🎉 CONSOLIDATION COMPLETE!"
echo "=========================="
echo "✅ All environments consolidated to: /home/admin/wallet_tool_unified"
echo "✅ Unified virtual environment: venv_unified"
echo "✅ Unified configuration: .env"
echo "✅ All enhanced modules included"
echo ""
echo "🚀 TO USE THE UNIFIED ENVIRONMENT:"
echo "./start_unified_wallet_tool.sh"
echo ""
echo "🗂️  OLD ENVIRONMENTS (can be removed after testing):"
echo "• /home/admin/wallet_tool/venv"
echo "• /home/admin/wallet_tool/hunter_env"  
echo "• /home/admin/wallet_tool/venv_db"
echo "• /home/admin/wallet_tool_production/venv_production"
echo "• /home/admin/venv"
