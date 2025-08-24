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
