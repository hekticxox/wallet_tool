# 🚀 Wallet Recovery Tool - Beta Production Ready

**Professional-grade cryptocurrency private key recovery and balance scanning toolkit**

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Production Ready](https://img.shields.io/badge/status-beta--production-green.svg)](https://github.com)
[![Security](https://img.shields.io/badge/security-production--grade-green.svg)](https://github.com)

## 🎯 Quick Start (Beta Production)

### 1. **One-Command Deployment**
```bash
# Deploy for production use
./deploy_production.sh
```

### 2. **Configure Environment**
```bash
# Copy and edit configuration
cp .env.production.template .env
nano .env  # Add your API keys and settings
```

### 3. **Start Scanning**
```bash
# Activate production environment
source venv_production/bin/activate

# Quick brain wallet scan
python main.py brain-scan fast

# Massive comprehensive scan  
python main.py brain-scan massive

# Check balances from file
python main.py balance-check keys.txt

# System status
python main.py status
```

## 🏗️ Production Architecture

### **Unified Entry Point**
All operations use the single `main.py` entry point:

```bash
python main.py <command> [options]
```

### **Core Commands**

| Command | Description | Example |
|---------|-------------|---------|
| `brain-scan` | Brain wallet scanning | `python main.py brain-scan fast` |
| `balance-check` | Check balances from file | `python main.py balance-check keys.txt` |
| `config` | Configuration management | `python main.py config --summary` |
| `setup` | Environment setup | `python main.py setup` |
| `status` | System status check | `python main.py status` |

### **Scanning Modes**

| Mode | Description | Speed | Coverage |
|------|-------------|-------|----------|
| `fast` | Quick patterns (1K keys) | ⚡⚡⚡ | Recent/current patterns |
| `massive` | Large-scale (100K+ keys) | ⚡⚡ | Comprehensive coverage |
| `research` | Academic research patterns | ⚡⚡ | Research-based targeting |
| `realistic` | Current patterns, no honeypots | ⚡⚡ | Modern, viable patterns |

## 📁 Production Directory Structure

```
wallet_tool/                    # 🏠 Project root
├── main.py                    # 🎯 Single entry point (START HERE!)
├── deploy_production.sh       # 🚀 One-command deployment
├── requirements-production.txt # 📦 Production dependencies
├── .env.production.template   # ⚙️ Configuration template
├── .env                      # 🔐 Your configuration (create from template)
│
├── src/                      # 📂 Source code (production organized)
│   ├── core/                 # 🏛️ Core system
│   │   └── config.py        # Configuration management
│   ├── scanners/            # 🔍 Scanning modules
│   │   ├── brain_wallet_scanner.py  # Unified brain wallet scanner
│   │   └── balance_checker.py       # Multi-API balance checker
│   ├── extractors/          # ⛏️ Key extraction (legacy)
│   ├── utils/               # 🛠️ Utilities
│   └── reports/             # 📊 Reporting
│
├── data/                    # 💾 Private keys & extracted data (secure)
├── results/                 # 📈 Scan results & found wallets (secure)
├── logs/                    # 📋 Application logs
├── backup/                  # 💾 Backup files
└── archive/                 # 📦 Legacy code (180+ files organized)
    └── legacy_scanners/     # Old scanner implementations
```

## ✨ Production Features

### **🔐 Security First**
- Environment-based configuration (.env)
- No hardcoded API keys or secrets
- Secure file permissions (600 for .env)
- Private key encryption support
- Audit logs and secure deletion

### **⚡ High Performance**
- Multi-threaded scanning (configurable)
- API rate limiting and fallback
- Efficient memory usage
- Progress tracking and resumable scans
- Batch processing optimizations

### **🛡️ Production Ready**
- Comprehensive error handling
- API timeout and retry logic
- Configuration validation
- Health checks and monitoring
- Clean shutdown handling

### **📊 Monitoring & Reporting**
- Real-time progress tracking
- Detailed scan statistics
- JSON result outputs
- Structured logging
- Performance metrics

## 🔧 Configuration

### **Environment Variables (.env)**

```bash
# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Scanner Settings
SCANNER_MAX_THREADS=10
SCANNER_API_TIMEOUT=5
SCANNER_RATE_LIMIT_BUFFER=0.2

# Bitcoin APIs
BLOCKSTREAM_ENABLED=true
BLOCKCYPHER_ENABLED=true
BLOCKCYPHER_API_KEY=your_api_key_here

# Security
ENCRYPT_PRIVATE_KEYS=true
LOG_PRIVATE_KEYS=false
BACKUP_RESULTS=true
```

### **API Configuration**
The tool supports multiple Bitcoin APIs with automatic fallback:

- **Blockstream** (primary, no key required)
- **BlockCypher** (recommended with API key)
- **Blockchain.info** (backup)

## 🎯 Usage Examples

### **Brain Wallet Scanning**

```bash
# Quick scan (recommended for testing)
python main.py brain-scan fast

# Comprehensive scan (production)
python main.py brain-scan massive

# Research-based patterns
python main.py brain-scan research

# Current patterns only (no honeypots)
python main.py brain-scan realistic
```

### **Balance Checking**

```bash
# Check private keys from file
python main.py balance-check private_keys.txt

# Check Bitcoin addresses from file
python main.py balance-check addresses.txt

# With custom output file
python main.py balance-check keys.txt --output results.json
```

### **Configuration Management**

```bash
# Show configuration summary
python main.py config --summary

# Validate API keys
python main.py config --validate

# Check system status
python main.py status
```

## 📊 Expected Results

### **Scan Statistics**
Typical performance metrics:
- **Fast mode**: 1,024 patterns in ~60 seconds
- **Massive mode**: 100,000+ patterns in ~2 hours  
- **API rate**: 10-20 keys/second (depending on APIs)
- **Success rate**: >99% API reliability with fallback

### **Found Wallets**
When funded wallets are discovered:
```json
{
  "pattern": "bitcoin2025",
  "private_key": "a1b2c3...",
  "address": "1A1zP1eP...", 
  "balance_btc": 0.00123456,
  "found_at": "2025-08-24T10:30:00Z"
}
```

## 🔒 Security & Legal

### **Security Best Practices**
- ✅ All sensitive data stored locally only
- ✅ No cloud storage or external transmission
- ✅ Environment-based configuration
- ✅ Secure file permissions
- ✅ Optional private key encryption
- ✅ Audit logging

### **Legal Compliance**
- ⚖️ Only scan keys you own or have permission to scan
- ⚖️ Respect API terms of service
- ⚖️ Follow local cryptocurrency regulations
- ⚖️ Use responsibly and ethically

## 🚀 Deployment Checklist

### **Pre-Deployment**
- [ ] Python 3.8+ installed
- [ ] Git repository cloned
- [ ] API keys obtained (BlockCypher recommended)

### **Deployment**
- [ ] Run `./deploy_production.sh`
- [ ] Configure `.env` file with your settings
- [ ] Test with `python main.py status`
- [ ] Run small test: `python main.py brain-scan fast`

### **Production Use**
- [ ] Monitor `logs/` directory
- [ ] Check `results/` for found wallets  
- [ ] Backup important findings
- [ ] Monitor API usage and limits

## 🆘 Troubleshooting

### **Common Issues**

**Import Errors**
```bash
# Install bitcoin library
pip install bitcoin

# Activate production environment
source venv_production/bin/activate
```

**API Rate Limits**
```bash
# Check configuration
python main.py config --validate

# Increase rate limit buffer in .env
SCANNER_RATE_LIMIT_BUFFER=0.5
```

**Permission Errors**
```bash
# Fix .env permissions
chmod 600 .env

# Fix directory permissions  
chmod 755 data results logs backup
```

## 📞 Support & Updates

### **Beta Testing**
This is a beta production release. Please:
- Test thoroughly before large-scale use
- Report issues and feedback
- Monitor for updates and improvements
- Keep backups of important results

### **Version History**
- **v1.0-beta**: Initial production consolidation
- **v1.1-beta**: Unified entry point and configuration
- **v1.2-beta**: Enhanced security and monitoring

---

## 🎉 Ready for Beta Production!

The wallet recovery tool has been completely consolidated and optimized for production use. All duplicate code has been removed, security has been enhanced, and the system is ready for reliable, large-scale cryptocurrency wallet recovery operations.

**Start your first scan:**
```bash
source venv_production/bin/activate
python main.py brain-scan fast
```

Good hunting! 🎯
