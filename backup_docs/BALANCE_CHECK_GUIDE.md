# Rate-Limit Safe Balance Checking Guide

## Quick Start - Smart Balance Checker

For immediate use without rate limit issues:

```bash
python smart_balance_checker.py
```

This will:
- ✅ Check 15 random addresses from each blockchain
- ✅ Use rate-limit friendly APIs (Blockchair, Blockstream)
- ✅ Add smart delays (1.5-3 seconds between calls)
- ✅ Show progress in real-time
- ✅ Save any funded addresses found

### Custom Options

```bash
# Check specific file
python smart_balance_checker.py your_wallet_file.json

# Check more addresses (be careful with sample size)
python smart_balance_checker.py detected_wallet_data_summary.json 25
```

## Advanced Balance Checker

For comprehensive checking with advanced features:

```bash
python advanced_balance_checker.py detected_wallet_data_summary.json --max-addresses 50
```

Features:
- 🔄 Multiple API fallbacks
- 💾 Intelligent caching (won't re-check same addresses)
- 📦 Batch processing with delays
- 🔄 Resume capability
- 📊 Detailed progress tracking

## Rate Limiting Strategy

### What Makes These Safe:

1. **API Selection**: Uses free APIs with generous rate limits
   - Blockchair: No API key required, high limits
   - Blockstream: Reliable Bitcoin API
   - Solana RPC: Direct blockchain access

2. **Smart Delays**:
   - Ethereum: 1.5-2.5 seconds between calls
   - Bitcoin: 2-3 seconds between calls  
   - Solana: 1-1.5 seconds between calls
   - Random jitter to avoid patterns

3. **Caching**: Never checks the same address twice

4. **Small Batches**: Processes in small groups with breaks

5. **Error Handling**: Gracefully handles rate limits and retries

## Getting API Keys (Optional but Recommended)

For even better rate limits, get free API keys:

### Etherscan (Ethereum)
1. Go to https://etherscan.io/apis
2. Create free account
3. Get API key (100,000 calls/day)
4. Edit `advanced_balance_checker.py` and add your key

### Blockchair (Multi-chain)
1. Go to https://blockchair.com/api
2. Free tier: 1,440 requests/day
3. Premium: Much higher limits

### Alchemy (Ethereum)
1. Go to https://www.alchemy.com/
2. Free tier: 300M compute units/month
3. Very reliable for Ethereum

## Expected Performance

### Smart Checker (Conservative):
- ~15 addresses per blockchain
- ~3-5 minutes total runtime
- Very low risk of rate limiting
- Good for quick scans

### Advanced Checker:
- Up to 100 addresses per blockchain  
- ~15-30 minutes total runtime
- Caching makes repeat runs very fast
- Better for comprehensive analysis

## Tips for Success

1. **Start Small**: Use smart checker first to test
2. **Be Patient**: Delays are necessary to avoid rate limits
3. **Check Different Times**: APIs may have lower load at certain hours
4. **Monitor Progress**: Both scripts show real-time progress
5. **Save Results**: All findings are automatically saved

## If You Get Rate Limited

If you still hit rate limits:
1. Stop the script (Ctrl+C)
2. Wait 1 hour
3. Run again (cached results won't be re-checked)
4. Consider getting API keys
5. Use smaller sample sizes

## Sample Output

```
🔍 Smart Balance Checker - Rate Limit Safe
==================================================
✅ Loaded wallet data from detected_wallet_data_summary.json

🔸 Checking 15 Ethereum addresses...
    1/15 ETH 0x1234abcd... 💸 0 ETH
    2/15 ETH 0x5678efgh... 💰 0.001234 ETH
    ...

💰 FUNDED ADDRESSES FOUND: 1
💾 Results saved to: funded_wallets_1691234567.json
```
