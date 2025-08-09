# 🔐 Wallet Recovery Toolkit

**Professional-grade cryptocurrency wallet recovery from browser data & LevelDB dumps**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/hekticxox/wallet_tool.git
cd wallet_tool

# Install dependencies
pip install -r requirements.txt

# Run wallet analysis on a directory
python wallet_analysis.py /path/to/browser/data

# Check balances for recovered addresses
python controlled_address_checker.py detected_wallet_data_summary.json 25
```

## 📋 What This Tool Does

This toolkit **recovers cryptocurrency wallets** from:
- 🌐 **Browser extension data** (MetaMask, Trust Wallet, etc.)
- 💾 **LevelDB databases** from Chrome/Edge profiles  
- 📁 **IndexedDB storage** with wallet information
- 🔑 **Raw private keys** and mnemonic phrases

**Supported Blockchains:**
- ₿ Bitcoin (BTC) - P2PKH, P2SH, Bech32 addresses
- Ξ Ethereum (ETH) - Standard addresses
- ◎ Solana (SOL) - Native addresses

## 🛠 Core Components

### 1. **Wallet Analysis** (`wallet_analysis.py`)
Main entry point that scans directories for wallet data:
```bash
python wallet_analysis.py /path/to/browser/profiles
```

### 2. **Balance Checker** (`controlled_address_checker.py`) ⭐ **RECOMMENDED**
Advanced balance checker with rate limiting and API fallbacks:
```bash
python controlled_address_checker.py detected_wallet_data_summary.json 25
```

**Features:**
- ✅ Only checks addresses you have private keys for
- ✅ Multiple API fallbacks (Etherscan, Alchemy, Blockstream, etc.)
- ✅ Smart rate limiting with randomized delays
- ✅ History tracking - never re-checks same addresses
- ✅ Shows exact balance amounts and API sources
- ✅ Secure output with private keys for funded addresses

### 3. **Core Modules**
- `detectors.py` - Pattern matching for wallet data
- `derivation.py` - Address derivation from private keys  
- `reports.py` - Output formatting and file generation
- `cli.py` - Command-line interface utilities

## 📊 Real-World Performance

**Tested on 148GB dataset with 500+ browser profiles:**
- ✅ **361 private keys** recovered
- ✅ **1,083 addresses** derived (361 × 3 blockchains)
- ✅ **Zero rate limiting** with multi-API system
- ✅ **Persistent progress** with history tracking

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Internet connection for balance checking APIs

### Install Dependencies
```bash
pip install requests plyvel cryptography base58 bech32
```

### Optional: API Keys (Higher Rate Limits)
Copy `api_config.json.example` to `api_config.json` and add your API keys:
```json
{
  "etherscan_api_key": "your-etherscan-key",
  "blockcypher_token": "your-blockcypher-token"
}
```

## 💡 Usage Examples

### Basic Wallet Recovery
```bash
# Scan Chrome profile directory
python wallet_analysis.py ~/.config/google-chrome/Default/

# Scan multiple browser profiles  
python wallet_analysis.py /path/to/browser/data/

# Scan LevelDB dump
python wallet_analysis.py /path/to/leveldb/dump/
```

### Balance Checking (Recommended Workflow)
```bash
# Check small batch first (test run)
python controlled_address_checker.py detected_wallet_data_summary.json 5

# Check larger batches
python controlled_address_checker.py detected_wallet_data_summary.json 25

# Check all addresses (will take time but resumes automatically)
python controlled_address_checker.py detected_wallet_data_summary.json 1000

# Reset checking history if needed
python controlled_address_checker.py --reset-history
```

## 📁 Output Files

### Analysis Results
- `detected_wallet_data_summary.json` - Complete findings with private keys
- `filtered_wallet_entries.json` - Organized wallet data

### Balance Check Results  
- `FUNDED_CONTROLLED_ADDRESSES_*.json` - **FUNDED WALLETS FOUND** 🎉
- `checked_addresses_history.json` - Tracking file (do not delete)

### Generated Reports
- Human-readable summaries of discoveries
- Organized by blockchain and wallet type

## 🔍 Understanding the Data Structure

**Why equal numbers per blockchain?**
Each private key generates addresses for all supported blockchains:

```
Private Key: abc123...def789
├── Bitcoin: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa  
├── Ethereum: 0x742F35CC6cf7B9D9ADf6A3E1C6A7C8F9E4D2E1B0
└── Solana: 5G1N8KzP9QvJ2H4F3R6E8D7C9B5A1X2Y4M7T6S8W
```

**This means:**
- 361 private keys = 361 ETH + 361 BTC + 361 SOL addresses
- **Maximum coverage** - same key might have funds on different blockchains
- **Efficient checking** - only addresses you can actually access

## ⚡ Advanced Features

### API Redundancy
Multiple free APIs with automatic failover:
- **Ethereum**: Etherscan → Alchemy → Blockchair → CloudFlare  
- **Bitcoin**: Blockstream → BlockCypher → Blockchain.info → Blockchair
- **Solana**: Official RPC → Ankr → GetBlock → Quicknode

### Smart Rate Limiting
- Randomized delays (2-4s ETH, 2-4s BTC, 1-2s SOL)
- Exponential backoff on rate limits
- Automatic API switching on failures

### Progress Persistence
- Never re-checks the same address twice
- Resume checking after interruption
- Clear progress tracking

## 🛡 Security & Legal Notes

⚠️ **Important Considerations:**
- **Keep results secure** - contains private keys and sensitive data
- **Legal compliance** - ensure you have rights to analyze the data
- **Responsible use** - only use on data you own or have permission to analyze
- **Backup critical files** - especially `detected_wallet_data_summary.json`

## 🐛 Troubleshooting

### Common Issues

**"No wallet data found"**
- Ensure browser extensions were installed and used
- Check different browser profile directories
- Try with actual user data, not fresh installs

**Rate limiting errors**
- Tool automatically handles this with multiple APIs
- Reduce batch size: use lower numbers (5-10 instead of 25)
- Wait and try again - APIs reset limits over time

**"ImportError" or missing dependencies**
```bash
pip install --upgrade requests plyvel cryptography base58 bech32
```

### Getting Help
- Check the output messages - they're detailed and helpful
- Start with small test batches before large runs
- Review generated log files for specific error details

## 📈 Performance Tips

### For Large Datasets
1. **Start small**: Test with 5-10 addresses first
2. **Use history**: Let the tool track progress automatically  
3. **Run overnight**: Large datasets take time but resume automatically
4. **Monitor APIs**: Different APIs have different limits and speeds

### For Best Results
1. **Target browser extension data** - highest success rate
2. **Check multiple browser profiles** - users often have multiple wallets
3. **Focus on controlled addresses** - only check what you can access

## 🔄 Version History

- **v2.0** - Multi-API system, persistent history, improved rate limiting
- **v1.5** - Added Solana support, better error handling
- **v1.0** - Initial release with Bitcoin and Ethereum support

---

## 🏆 Success Metrics

✅ **Scalable**: Handles 100GB+ datasets  
✅ **Reliable**: Multi-API fallbacks prevent failures  
✅ **Efficient**: Never duplicates work with history tracking  
✅ **Secure**: Private keys only shown for funded addresses  
✅ **Professional**: Clean output and comprehensive logging  

**Built for serious wallet recovery operations.** 💼

---

*This tool is for legitimate wallet recovery purposes only. Always ensure legal compliance and data ownership.*
