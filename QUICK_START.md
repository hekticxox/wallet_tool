# Quick Usage Guide

## 🚀 Get Started in 2 Minutes

### Step 1: Analyze Wallet Data
```bash
python wallet_analysis.py /path/to/browser/data
```

### Step 2: Check Balances (Smart & Safe)
```bash
python controlled_address_checker.py detected_wallet_data_summary.json 10
```

## 📊 What to Expect

**After Step 1:**
- Creates `detected_wallet_data_summary.json` with all findings
- Shows how many private keys and addresses were found
- Reports cover multiple blockchains (BTC, ETH, SOL)

**After Step 2:**
- Checks actual balances using multiple APIs
- Shows progress: `💸 0 BTC (blockstream)` or `💰 1.23 BTC (blockstream)`
- Saves any funded addresses with their private keys
- Never re-checks the same address twice

## 🎯 Pro Tips

1. **Start Small**: Use small numbers (5-10) for first run
2. **Let It Run**: Tool handles rate limits automatically
3. **Check History**: Tool remembers what it's already checked
4. **Secure Results**: Keep `detected_wallet_data_summary.json` safe

## 🔍 File Locations

**Common browser data locations:**
- **Windows**: `%LOCALAPPDATA%\Google\Chrome\User Data\Default\`
- **macOS**: `~/Library/Application Support/Google/Chrome/Default/`  
- **Linux**: `~/.config/google-chrome/Default/`

**Look for these directories:**
- `Local Extension Settings/`
- `IndexedDB/`
- `Local Storage/`

That's it! The tool does the heavy lifting. 🎉
