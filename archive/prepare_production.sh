#!/bin/bash
# Clean repository for production release

echo "🧹 Cleaning repository for production..."
echo "======================================="

# Remove sensitive data files
echo "🗑️  Removing sensitive data files..."
rm -f detected_wallet_data_summary.json
rm -f filtered_wallet_entries.json  
rm -f checked_addresses_history.json
rm -f balance_checker.log
rm -f auto_recovery.log
rm -f FUNDED_ADDRESSES.txt
rm -f api_config.json

# Remove development/debugging files
echo "🗑️  Removing development files..."
rm -f README_new.md
rm -f WORKFLOW.md
rm -f QUICK_START.md
rm -f wallet_analysis.py  # Keep only the clean version
rm -f controlled_address_checker.py  # Keep only continuous version
rm -f safe_data_analyzer.py
rm -rf __pycache__/

# Remove virtual environment (user should create their own)
echo "🗑️  Removing virtual environment..."
rm -rf venv/

# Remove IDE settings  
rm -rf .vscode/

# Clean git if it exists
if [ -d ".git" ]; then
    echo "🔄 Cleaning git history..."
    # Add all files to staging
    git add -A
    
    # Check if there are changes to commit
    if ! git diff --staged --quiet; then
        echo "📝 Committing production-ready version..."
        git commit -m "Production ready: Cleaned sensitive data and debugging files

- Removed all personal wallet data files
- Removed development/debugging files  
- Updated .gitignore for security
- Added clean production scripts
- Ready for public repository"
    else
        echo "ℹ️  No changes to commit"
    fi
fi

# Rename files for production
if [ -f "wallet_analysis_clean.py" ]; then
    echo "🔄 Setting up production files..."
    mv wallet_analysis_clean.py wallet_analysis.py
fi

if [ -f "README_PRODUCTION.md" ]; then
    mv README_PRODUCTION.md README.md
fi

# Create final directory structure info
echo ""
echo "📁 Production files ready:"
echo "=========================="
ls -la | grep -E "\.(py|sh|md|txt|json\.example)$|^-.*requirements"

echo ""
echo "✅ Repository cleaned for production!"
echo ""
echo "📋 Next steps:"
echo "   1. Review files above"
echo "   2. Test with: ./setup.sh"
echo "   3. Push to GitHub: git push origin main"
echo "   4. Tag release: git tag v1.0.0"
echo ""
echo "⚠️  Make sure .gitignore prevents accidental data commits!"
