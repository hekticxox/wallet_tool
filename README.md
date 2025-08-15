# 🔐 Wallet Recovery Tools

Professional cryptocurrency wallet recovery and analysis tools designed for individual use. Clean, secure, and focused on protecting your privacy while providing powerful recovery capabilities.

## 🎯 GOAL

**Primary Objective**: Provide individual developers and researchers with professional-grade tools for cryptocurrency wallet recovery, key analysis, and blockchain investigation while maintaining complete privacy and security.

**Core Principles**:
- ✅ Individual-focused (not team-oriented)
- ✅ Privacy-first (no personal data in Git)
- ✅ Professional-grade tools and security
- ✅ Easy to use and customize
- ✅ Comprehensive blockchain support

## 🔄 WORKFLOW

### 1. **Initial Setup**
```bash
# Clone and setup
git clone https://github.com/hekticxox/wallet_tool.git
cd wallet_tool
./setup.sh
```

### 2. **Configuration**
```bash
# Copy and configure API settings
cp api_config.json.example api_config.json
# Edit with your API keys (kept private via .gitignore)
```

### 3. **Core Recovery Workflow**
```bash
# Activate environment
source venv/bin/activate

# Run security setup
python src/security/security_hardening.py

# Use core tools for recovery
python src/core/unified_wallet_scanner.py
python src/utils/status_dashboard.py
```

### 4. **Data Management**
- All results stored locally in `data/` (excluded from Git)
- Personal configurations kept private
- Secure cleanup tools available in `src/security/`

## 📁 Repository Structure

**✅ Included in Git (Core Tools)**:
```
├── README.md                    # This documentation
├── requirements.txt             # Dependencies
├── setup.sh                    # Easy setup script
├── api_config.json.example     # API configuration template
└── src/
    ├── core/                   # Core recovery tools
    ├── security/               # Security and audit tools
    └── utils/                  # Helper utilities
```

**❌ Excluded from Git (Personal Data)**:
```
├── data/                       # Your results and findings
├── logs/                       # Your activity logs  
├── api_config.json            # Your API keys
├── .env                       # Your environment variables
└── [all personal files]       # Your working data
```

## 🚀 Quick Start

### First Time Setup
```bash
# 1. Run setup
./setup.sh

# 2. Configure APIs
cp api_config.json.example api_config.json
# Edit api_config.json with your API keys

# 3. Test installation
python src/utils/api_test.py
```

### Daily Usage
```bash
# Activate environment
source venv/bin/activate

# Run your recovery workflow
python src/core/unified_wallet_scanner.py

# Check status
python src/utils/status_dashboard.py

# Security cleanup when done
python src/security/advanced_security_cleanup.py
```

## 🔧 Core Features

### 🔐 Security First
- **Privacy Protection**: All personal data excluded from Git
- **Secure Configuration**: API keys and sensitive data kept local
- **Security Tools**: Comprehensive cleanup and audit capabilities
- **Safe Practices**: Built-in security hardening and best practices

### 🎯 Recovery Capabilities  
- **Multi-Blockchain**: Bitcoin, Ethereum, and other cryptocurrencies
- **Advanced Analysis**: Professional-grade recovery algorithms
- **Flexible Tools**: Modular design for custom workflows
- **Individual Focus**: Designed for personal use, not team deployment

### ⚡ Professional Tools
- **Clean Architecture**: Well-organized, maintainable code
- **Easy Setup**: One-command installation and configuration
- **Status Monitoring**: Real-time dashboard and reporting
- **Repository Management**: Tools for keeping your workspace organized

## 🛡️ Security & Privacy

### What's Protected
- ✅ **Your API Keys** - Never committed to Git
- ✅ **Your Results** - All findings stay local
- ✅ **Your Configuration** - Personal settings excluded
- ✅ **Your Workflow** - Working files and logs private

### What's Shared
- ✅ **Core Tools** - Essential recovery utilities
- ✅ **Security Framework** - Audit and cleanup tools  
- ✅ **Setup Scripts** - Easy installation and configuration
- ✅ **Documentation** - Clear usage instructions

## 📚 Usage Examples

### Basic Recovery Session
```bash
# Start fresh session
source venv/bin/activate
python src/security/security_hardening.py

# Run recovery tools
python src/core/unified_wallet_scanner.py

# Monitor progress  
python src/utils/status_dashboard.py

# Secure cleanup
python src/security/advanced_security_cleanup.py
```

### Repository Management
```bash
# Organize your workspace
python src/utils/repository_organizer.py

# Clean up working files
python src/utils/simple_organizer.py
```

## ⚠️ Important Notes

- **Individual Use Only**: These tools are designed for personal cryptocurrency recovery projects
- **Keep Data Private**: Never commit your results, keys, or personal data to Git
- **API Keys**: Always use your own API keys and keep them secure
- **Legal Compliance**: Ensure you comply with local laws regarding cryptocurrency recovery
- **Backup Important Data**: Keep secure backups of important findings

## 🤝 Contributing

This repository focuses on **core tool development only**. Personal data, results, and individual workflows should never be shared or committed.

**What to Contribute**:
- ✅ Core tool improvements
- ✅ Security enhancements  
- ✅ Documentation updates
- ✅ Bug fixes in utilities

**What NOT to Contribute**:
- ❌ Personal results or findings
- ❌ API keys or configuration
- ❌ Working data or logs
- ❌ Individual recovery projects

## 📄 License

See LICENSE file for details. Use responsibly and in compliance with applicable laws.