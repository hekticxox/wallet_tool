# 🎯 Wallet Recovery Tool - Fresh Start Guide

A clean, objective approach to cryptocurrency wallet recovery using data-driven analysis.

## 🚀 Quick Start

1. **Setup (one time only):**
   ```bash
   ./fresh_start.sh
   ```

2. **Three-step workflow:**
   ```bash
   # Step 1: Extract all data (no assumptions, no balance checks)
   python3 unified_wallet_scanner.py --extract-only /path/to/wallet/directory
   
   # Step 2: Find top 100 most promising addresses using objective analysis
   python3 top_wallet_finder.py extracted_addresses_all.json
   
   # Step 3: Check balances for only the top 100 addresses
   python3 unified_wallet_scanner.py --check-balances top_100_wallets.json
   ```

## 📊 How It Works

### Step 1: Data Extraction
- Scans LevelDB databases for private keys
- Generates Bitcoin and Ethereum addresses from each private key
- Saves all data without any filtering or assumptions
- **No balance checking** - just pure data extraction

### Step 2: Objective Analysis  
- Analyzes wallet types (MetaMask, Trust, Coinbase, etc.)
- Evaluates private key entropy (randomness = legitimacy)
- Considers geographic patterns based on crypto adoption
- Scores addresses using **data-driven metrics only**
- Selects top 100 most promising addresses

### Step 3: Targeted Balance Checking
- Checks only the 100 most promising addresses
- Uses multiple APIs (Etherscan, Blockstream, etc.)
- Saves any funded addresses immediately
- Provides detailed reporting

## 🎯 Scoring System (Objective)

Addresses are scored based on:

- **Wallet Type**: MetaMask (9.0), Coinbase (8.0), Trust (7.0), etc.
- **Chain Type**: Bitcoin P2PKH (8.0), Ethereum (7.0), Bitcoin P2SH (6.0)
- **Geographic**: High crypto adoption countries (+3.0)
- **Entropy**: Private key randomness (up to +5.0)
- **Profile Type**: Power users with multiple profiles (+2.0)

## 📋 Requirements

- Python 3.8+
- Dependencies: `requests`, `plyvel`, `bip-utils`, `eth-keys`, `eth-utils`
- API keys: Etherscan (for Ethereum balance checking)

## ⚙️ Configuration

Edit `api_config.json`:
```json
{
  "etherscan_api_key": "your_etherscan_api_key",
  "bitcoin_apis": ["https://blockstream.info/api"],
  "rate_limits": {
    "etherscan": 5,
    "bitcoin": 10
  }
}
```

## 🔍 Sample Output

```
🎯 TOP WALLET FINDER - OBJECTIVE ANALYSIS
==================================================
📊 Loaded 50,000 extracted addresses

🔗 Chain Distribution:
   ETHEREUM    : 25,000 addresses (50.0%)
   BITCOIN     : 25,000 addresses (50.0%)

📱 Source Analysis (Top 5):
   MetaMask_Chrome_Default  : 15,000 addresses (30.0%)
   Trust_Wallet            :  8,000 addresses (16.0%)
   Coinbase_Wallet         :  5,000 addresses (10.0%)

🏆 Top 100 addresses selected and saved to top_100_wallets.json
```

## 🚨 Key Differences from Previous Versions

- ✅ **No hardcoded patterns** - everything is data-driven
- ✅ **No assumptions** about dataset origin or status
- ✅ **Focused approach** - only check top 100 most promising
- ✅ **Objective scoring** based on legitimate usage patterns
- ✅ **Clear separation** between extraction and balance checking

## 📁 Files Created

- `extracted_addresses_all.json` - All extracted addresses and private keys
- `top_100_wallets.json` - The 100 most promising addresses to check
- `address_tracking.db` - SQLite database for duplicate prevention
- `unified_scanner_final_report.json` - Detailed results and statistics

## 🤝 Usage

This tool is designed for legitimate wallet recovery. Always ensure you have proper authorization to scan any directories or check any addresses.

Tell me which directory you want to analyze and we'll run through the complete workflow!
