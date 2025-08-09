# 🔐 Wallet Recovery Tool

A clean, professional Python toolkit for recovering cryptocurrency wallets from browser storage dumps and LevelDB files.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/hekticxox/wallet_tool.git
cd wallet_tool

# Set up Python environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run wallet analysis
python wallet_analysis.py

# Check balances for found addresses
python controlled_address_checker.py
```

## 📋 What This Tool Does

This toolkit **recovers cryptocurrency wallets** from:
- 🌐 **Browser extension data** (MetaMask, Trust Wallet, etc.)
- 💾 **LevelDB databases** from Chrome/Edge profiles  
- 📁 **Browser storage** with wallet information
- 🔑 **Private keys** and mnemonic phrases

**Supported Blockchains:**
- ₿ **Bitcoin** (BTC) - P2PKH addresses
- Ξ **Ethereum** (ETH) - Standard addresses  
- ◎ **Solana** (SOL) - Native addresses

## 🗂 Repository Structure

```
wallet_tool/
├── wallet_analysis.py              # Main wallet extraction script
├── controlled_address_checker.py   # Balance checker for controlled addresses  
├── requirements.txt                # Python dependencies
├── README.md                       # Documentation
├── WORKFLOW.md                     # Step-by-step workflow guide
├── LICENSE                         # MIT License
├── .gitignore                      # Git ignore rules
└── .vscode/                        # VS Code configuration
```

## 🛠 Core Scripts

### 1. Wallet Analysis (`wallet_analysis.py`)
Extracts wallet data from browser directories:
- Scans LevelDB files for private keys and mnemonics
- Generates addresses for Bitcoin, Ethereum, and Solana
- Cross-validates that keys generate expected addresses  
- Outputs comprehensive JSON summaries

### 2. Controlled Address Checker (`controlled_address_checker.py`)
Checks balances only for addresses with known private keys:
- Rate-limited API calls to respect service limits
- Multiple blockchain support with API fallbacks
- Tracks checking history to avoid duplicates
- Shows private keys for any funded addresses found

## 📊 Example Output

```
Detected private keys: 122,581
Detected Ethereum addresses: 134,909
Detected Bitcoin addresses: 122,591
Detected Solana addresses: 122,581

✅ Balance checking: 1,083 addresses checked
💰 Found funded addresses with private keys available
```

## ⚡ Key Features

- **🎯 Targeted**: Only checks addresses you can actually control
- **🚀 Fast**: Smart caching and rate limiting  
- **🔒 Secure**: Works offline, keys never leave your machine
- **📈 Scalable**: Handles datasets with 100K+ addresses
- **🔄 Resumable**: All progress automatically saved
- **🛡️ Professional**: Clean code, comprehensive error handling

## 📖 Documentation

- **[WORKFLOW.md](WORKFLOW.md)** - Complete step-by-step workflow
- **[LICENSE](LICENSE)** - MIT License details

## ⚠️ Legal Disclaimer

This tool is for **recovering your own wallets** only. Use responsibly and in compliance with local laws.

## 🤝 Contributing

Issues and pull requests welcome! Please ensure code follows the existing style and includes appropriate tests.

---

**Made with ❤️ for the crypto recovery community**
