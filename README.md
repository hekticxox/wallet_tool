# 🔍 Crypto Wallet Recovery Tool

A comprehensive Python tool for extracting and analyzing cryptocurrency private keys, seed phrases, and wallet addresses from LevelDB database files (commonly found in browser storage, wallet applications, etc.).

## ⚡ Features

- **LevelDB Analysis**: Recursively scans directories for LevelDB databases and extracts readable data
- **Multi-Chain Support**: Bitcoin, Ethereum, and Solana address generation and validation
- **Seed Phrase Detection**: Automatically identifies and validates BIP39 mnemonic phrases
- **Private Key Extraction**: Finds both hex-format private keys and WIF-encoded Bitcoin keys
- **Balance Checking**: Automated balance verification across multiple blockchain networks
- **Continuous Operation**: Background processing with monitoring and auto-recovery
- **Cross-Chain Mapping**: Links private keys to their corresponding addresses across chains

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/wallet-recovery-tool.git
   cd wallet-recovery-tool
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Basic Usage

1. **Extract wallet data from LevelDB**
   ```bash
   python wallet_analysis.py
   ```
   - Enter the path to your LevelDB directory when prompted
   - The tool will scan all subdirectories recursively
   - Results saved to `detected_wallet_data_summary.json`

2. **Check balances (optional)**
   ```bash
   python continuous_checker.py
   ```
   - Automatically checks balances for all detected addresses
   - Runs continuously until all addresses are verified
   - Funded addresses logged to `FUNDED_ADDRESSES.txt`

## 📁 Output Files

- `detected_wallet_data_summary.json`: Complete analysis results
- `filtered_wallet_entries.json`: Raw LevelDB data
- `checked_addresses_history.json`: Balance checking progress
- `FUNDED_ADDRESSES.txt`: Found addresses with balances
- `balance_checker.log`: Processing logs

## 🛠️ Management Scripts

- `./monitor_checker.sh`: Check balance checker status
- `./restart_checker.sh`: Restart balance checker
- `./auto_recovery.sh`: Auto-restart crashed processes (for cron)

## 🔧 Configuration

The tool works out-of-the-box with default API endpoints:

- **Bitcoin**: blockstream.info API
- **Ethereum**: etherscan.io API (rate limited)
- **Solana**: Official RPC endpoint

## 📊 Performance

- **Processing Rate**: ~1,333 addresses/hour (API rate limited)
- **Memory Usage**: ~300-400MB typical
- **Storage**: Minimal (results are JSON files)

## ⚠️ Important Notes

### Security & Privacy
- **Never commit wallet data files** - they contain sensitive private keys
- **Use on isolated systems** for maximum security
- **Backup your findings** before running balance checks
- **This tool is for recovery purposes only** - respect legal boundaries

### Legal Disclaimer
- Only use on wallet data you own or have explicit permission to analyze
- Cryptocurrency recovery tools should be used responsibly
- Users are responsible for complying with local laws and regulations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter issues:

1. Check the [Issues](https://github.com/yourusername/wallet-recovery-tool/issues) page
2. Review the logs in `balance_checker.log`
3. Ensure your LevelDB directory is accessible
4. Verify all dependencies are installed correctly

## 🙏 Acknowledgments

- Built with [bip_utils](https://github.com/ebellocchia/bip_utils) for cryptographic functions
- Uses [plyvel](https://github.com/wbolster/plyvel) for LevelDB access
- Ethereum support via [eth_keys](https://github.com/ethereum/eth-keys)
- Solana integration with [solders](https://github.com/kevinheavey/solders)

---

**⭐ If this tool helped you recover your wallet, please star the repository!**
