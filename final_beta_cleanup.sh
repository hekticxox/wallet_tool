#!/bin/bash
#
# Final Beta Production Cleanup Script
# ====================================
# Remove redundant files and prepare the repository for beta production deployment.
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧹 Final Beta Production Cleanup${NC}"
echo "=================================="

# Remove duplicate/redundant result files
echo -e "${YELLOW}Cleaning up duplicate result files...${NC}"
rm -f massive_scan_results_*.json
rm -f fresh_brain_results_*.json
rm -f multi_chain_scan_results_*.json
rm -f simple_scan_results_*.json
rm -f *_results_*.json
rm -f *brain_wallets_*.txt
rm -f *brain_wallets_*.meta.json
echo -e "${GREEN}✅ Result files cleaned${NC}"

# Remove old Python cache
echo -e "${YELLOW}Cleaning Python cache...${NC}"
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
echo -e "${GREEN}✅ Python cache cleaned${NC}"

# Remove IDE files
echo -e "${YELLOW}Cleaning IDE files...${NC}"
rm -rf .vscode/settings.json 2>/dev/null || true
rm -f *.swp *.swo 2>/dev/null || true
echo -e "${GREEN}✅ IDE files cleaned${NC}"

# Remove redundant log files
echo -e "${YELLOW}Cleaning old log files...${NC}"
rm -f *.log 2>/dev/null || true
rm -f supreme_wallet_hunter.log 2>/dev/null || true
rm -f wallet_tool.log 2>/dev/null || true
echo -e "${GREEN}✅ Log files cleaned${NC}"

# Archive legacy setup scripts
echo -e "${YELLOW}Archiving legacy setup scripts...${NC}"
mkdir -p archive/legacy_setup
mv setup.sh archive/legacy_setup/ 2>/dev/null || true
mv setup_env.sh archive/legacy_setup/ 2>/dev/null || true
mv setup_postgresql_beta.sh archive/legacy_setup/ 2>/dev/null || true
mv setup_production_db.py archive/legacy_setup/ 2>/dev/null || true
echo -e "${GREEN}✅ Legacy setup scripts archived${NC}"

# Archive old cleanup scripts
echo -e "${YELLOW}Archiving old cleanup scripts...${NC}"
mkdir -p archive/legacy_cleanup
mv cleanup_repo.sh archive/legacy_cleanup/ 2>/dev/null || true
mv final_cleanup.sh archive/legacy_cleanup/ 2>/dev/null || true
mv aggressive_cleanup.py archive/legacy_cleanup/ 2>/dev/null || true
mv workspace_cleanup.py archive/legacy_cleanup/ 2>/dev/null || true
echo -e "${GREEN}✅ Legacy cleanup scripts archived${NC}"

# Archive redundant documentation
echo -e "${YELLOW}Archiving redundant documentation...${NC}"
mkdir -p archive/legacy_docs
mv BETA_TESTING_GUIDE.md archive/legacy_docs/ 2>/dev/null || true
mv CONSOLIDATION_*.md archive/legacy_docs/ 2>/dev/null || true
mv PRODUCTION_*.md archive/legacy_docs/ 2>/dev/null || true
mv FINAL_*.md archive/legacy_docs/ 2>/dev/null || true
mv NEXT_*.md archive/legacy_docs/ 2>/dev/null || true
mv REPOSITORY_*.md archive/legacy_docs/ 2>/dev/null || true
mv ORGANIZATION_*.md archive/legacy_docs/ 2>/dev/null || true
mv ENVIRONMENT_*.md archive/legacy_docs/ 2>/dev/null || true
echo -e "${GREEN}✅ Legacy documentation archived${NC}"

# Archive redundant status files
echo -e "${YELLOW}Archiving status files...${NC}"
mkdir -p archive/legacy_status
mv *STATUS*.md archive/legacy_status/ 2>/dev/null || true
mv *COMPLETE*.py archive/legacy_status/ 2>/dev/null || true
mv *COMPLETE*.md archive/legacy_status/ 2>/dev/null || true
mv production_status_report_*.json archive/legacy_status/ 2>/dev/null || true
echo -e "${GREEN}✅ Status files archived${NC}"

# Archive WX directory if exists
echo -e "${YELLOW}Archiving WX directory...${NC}"
if [ -d "WX51A40D1621" ]; then
    mv WX51A40D1621 archive/ 2>/dev/null || true
    echo -e "${GREEN}✅ WX directory archived${NC}"
else
    echo -e "${YELLOW}⚠️  No WX directory found${NC}"
fi

# Archive net607 directory if exists
echo -e "${YELLOW}Archiving net607 directory...${NC}"
if [ -d "net607" ]; then
    mv net607 archive/ 2>/dev/null || true
    echo -e "${GREEN}✅ net607 directory archived${NC}"
else
    echo -e "${YELLOW}⚠️  No net607 directory found${NC}"
fi

# Clean up empty directories
echo -e "${YELLOW}Removing empty directories...${NC}"
find . -type d -empty -delete 2>/dev/null || true
echo -e "${GREEN}✅ Empty directories removed${NC}"

# Update git ignore for production
echo -e "${YELLOW}Ensuring .gitignore is production-ready...${NC}"
if grep -q "PRODUCTION SECURITY" .gitignore; then
    echo -e "${GREEN}✅ .gitignore already production-ready${NC}"
else
    echo -e "${YELLOW}⚠️  .gitignore needs updating${NC}"
fi

# Set final permissions
echo -e "${YELLOW}Setting production permissions...${NC}"
chmod +x main.py 2>/dev/null || true
chmod +x deploy_production.sh 2>/dev/null || true
chmod -R +r src/ 2>/dev/null || true
echo -e "${GREEN}✅ Production permissions set${NC}"

# Create final directory structure summary
echo -e "${YELLOW}Creating directory summary...${NC}"
cat > DIRECTORY_STRUCTURE.md << 'EOF'
# Production Directory Structure

## Active Production Files
```
wallet_tool/
├── main.py                    # 🎯 Main entry point
├── deploy_production.sh       # 🚀 Production deployment
├── requirements-production.txt # 📦 Dependencies
├── .env.production.template   # ⚙️ Config template
├── README_PRODUCTION.md       # 📖 Production documentation
├── .gitignore                # 🔒 Security exclusions
│
├── src/                      # 📂 Source code
│   ├── core/                # 🏛️ Core modules
│   │   └── config.py       # Configuration management
│   └── scanners/           # 🔍 Scanning modules
│       ├── brain_wallet_scanner.py
│       └── balance_checker.py
│
├── data/                    # 💾 Working data (secure)
├── results/                 # 📈 Scan results (secure)  
├── logs/                    # 📋 Application logs
├── backup/                  # 💾 Backups
└── archive/                 # 📦 Legacy code
    ├── legacy_scanners/     # Old scanner files
    ├── legacy_setup/        # Old setup scripts
    ├── legacy_cleanup/      # Old cleanup scripts
    ├── legacy_docs/         # Old documentation
    └── legacy_status/       # Old status files
```

## Archived Files
- 🗃️ 180+ legacy scanner files moved to archive/
- 🗃️ Duplicate documentation consolidated  
- 🗃️ Old setup and cleanup scripts archived
- 🗃️ Status and temporary files cleaned

## Security Features
- 🔒 .env file excluded from git
- 🔒 All data/ and results/ secured
- 🔒 Private keys never committed
- 🔒 API keys in environment only
EOF

echo -e "${GREEN}✅ Directory structure documented${NC}"

# Final file count
echo -e "${BLUE}📊 Final cleanup statistics:${NC}"
echo "Production files in root: $(find . -maxdepth 1 -type f | wc -l)"
echo "Files in src/: $(find src/ -type f | wc -l 2>/dev/null || echo "0")"
echo "Archived files: $(find archive/ -type f | wc -l 2>/dev/null || echo "0")"

echo ""
echo -e "${GREEN}🎉 BETA PRODUCTION CLEANUP COMPLETE!${NC}"
echo "======================================"
echo ""
echo -e "${BLUE}✅ Repository is now beta production ready!${NC}"
echo ""
echo "Next steps:"
echo "1. Run: ./deploy_production.sh"
echo "2. Configure .env file"
echo "3. Test: python main.py status"
echo "4. Deploy: python main.py brain-scan fast"
