# API Configuration Guide

## 🔑 Secure API Key Management

This wallet recovery tool now uses a secure `.env` file system for managing API keys. This prevents accidental commits of sensitive data and provides a standardized way to manage multiple blockchain APIs.

## 📋 Quick Setup

1. **Copy the example file:**
   ```bash
   cp .env .env.backup  # Backup if you already have one
   ```

2. **Edit the `.env` file with your API keys:**
   ```bash
   nano .env
   ```

3. **Get free API keys from these providers:**
   - **Etherscan.io** - Ethereum blockchain data
   - **BlockCypher.com** - Bitcoin and multi-chain APIs  
   - **Infura.io** - Ethereum infrastructure
   - **Alchemy.com** - Multi-chain Web3 APIs

4. **Test your configuration:**
   ```bash
   python test_api_setup.py
   ```

## 🔧 Supported APIs

### Ethereum APIs
- **Etherscan** - Most reliable, 5 calls/second free
- **Alchemy** - High performance, generous free tier
- **Infura** - Ethereum infrastructure, 100k calls/day free
- **Moralis** - Web3 APIs with good free limits

### Bitcoin APIs  
- **BlockCypher** - Comprehensive Bitcoin API
- **Blockstream** - No API key required, rate limited
- **Blockchain.info** - Classic Bitcoin explorer API

### Multi-Chain APIs
- **Covalent** - Unified API for multiple chains
- **Ankr** - Multi-chain RPC services  
- **Moralis** - Cross-chain Web3 APIs

## 📝 Environment Variables

The `.env` file supports these variables:

```bash
# Ethereum APIs
ETHERSCAN_API_KEY=your_etherscan_key_here
INFURA_PROJECT_ID=your_infura_project_id_here
ALCHEMY_API_KEY=your_alchemy_key_here

# Bitcoin APIs  
BLOCKCYPHER_API_TOKEN=your_blockcypher_token_here
BLOCKSTREAM_API_KEY=optional_blockstream_key
BLOCKCHAIN_INFO_API_KEY=your_blockchain_info_key

# Multi-chain APIs
MORALIS_API_KEY=your_moralis_key_here
COVALENT_API_KEY=your_covalent_key_here
ANKR_API_KEY=your_ankr_key_here

# Rate Limiting
DEFAULT_RATE_LIMIT=5
PREMIUM_RATE_LIMIT=10
API_TIMEOUT=30

# RPC URLs (optional overrides)
ETHEREUM_RPC_URL=https://mainnet.infura.io/v3/
BITCOIN_RPC_URL=https://api.blockcypher.com/v1/btc/main
```

## 🚀 Usage Examples

### Basic Balance Checking
```python
from enhanced_balance_checker import EnhancedBalanceChecker

checker = EnhancedBalanceChecker()

# Check single address (auto-detects blockchain)
result = checker.check_address_balance("0x...")
if result['success'] and result['has_balance']:
    print(f"Found {result['balance_eth']} ETH!")

# Check multiple addresses
addresses = ["0x...", "1....", "bc1..."]
results = checker.check_multiple_addresses(addresses)
```

### Using API Manager Directly
```python
from api_manager import api_manager

# Get specific API key
etherscan_key = api_manager.get_api_key('etherscan')

# Get all Ethereum APIs
eth_apis = api_manager.get_ethereum_apis()

# Validate configuration
status = api_manager.validate_setup()
```

### Integration with Existing Scripts
```python
# Replace old API loading code:
# with open('api_config.json') as f:
#     config = json.load(f)

# With new secure loading:
from api_manager import get_ethereum_api_key
api_key = get_ethereum_api_key()
```

## 🛡️ Security Features

- **Never commits sensitive data** - `.env` is in `.gitignore`
- **Multiple API fallbacks** - Automatically tries backup APIs
- **Rate limiting protection** - Prevents API abuse
- **Input validation** - Validates API keys and responses
- **Error handling** - Graceful degradation when APIs fail

## ⚡ Performance Optimization

- **Automatic API selection** - Uses fastest available API
- **Intelligent rate limiting** - Respects each API's limits
- **Connection pooling** - Reuses HTTP connections
- **Response caching** - Caches recent API responses
- **Batch processing** - Groups requests when possible

## 🧪 Testing & Validation

Run the test suite to validate your setup:

```bash
# Test API configuration
python test_api_setup.py

# Test individual components
python api_manager.py
python enhanced_balance_checker.py
```

The test suite will:
- ✅ Validate `.env` file exists and is readable
- ✅ Check API keys are properly formatted
- ✅ Test connectivity to each configured API
- ✅ Verify rate limiting is working
- ✅ Test auto-detection features

## 🔄 Migration from Old System

If you're upgrading from the old `api_config.json` system:

1. **Backup your old configuration:**
   ```bash
   cp api_config.json api_config.json.backup
   ```

2. **Extract your API keys:**
   - Copy API keys from `api_config.json`
   - Add them to `.env` file using new variable names

3. **Update your scripts:**
   - Replace `json.load()` API loading
   - Use `api_manager` imports instead

4. **Test the migration:**
   ```bash
   python test_api_setup.py
   ```

## 📈 Rate Limits & Best Practices

### Free Tier Limits
- **Etherscan**: 5 calls/second, 100,000/day
- **Infura**: 10 calls/second, 100,000/day  
- **Alchemy**: 300 calls/second, 300M/month
- **BlockCypher**: 3 calls/second, 200/hour

### Best Practices
- **Use multiple APIs** for redundancy
- **Implement exponential backoff** for failures
- **Cache responses** to reduce API calls
- **Batch requests** when APIs support it
- **Monitor usage** to avoid hitting limits

## 🆘 Troubleshooting

### Common Issues

**"No API key found" error:**
- Check `.env` file exists in correct directory
- Verify variable names match exactly
- Ensure no spaces around `=` in `.env`

**"Rate limited" error:**
- Wait before retrying
- Check if you've exceeded daily limits
- Use multiple API keys for higher limits

**"Invalid API key" error:**
- Verify API key is correct and active
- Check if API key has required permissions
- Some APIs require whitelisted IPs

**"Connection timeout" error:**
- Check internet connectivity
- Try different API endpoint
- Increase timeout in `.env` file

### Debug Mode

Enable detailed logging:
```bash
export ENABLE_DEBUG_MODE=true
python your_script.py
```

### Support

For issues with specific APIs:
- **Etherscan**: https://docs.etherscan.io/
- **Alchemy**: https://docs.alchemy.com/
- **Infura**: https://docs.infura.io/
- **BlockCypher**: https://www.blockcypher.com/dev/

## 🔒 Security Considerations

- **Never share** your `.env` file
- **Use separate keys** for development/production
- **Rotate keys regularly** if they're compromised
- **Monitor usage** for unexpected activity
- **Use least privilege** - only request needed permissions

## 📊 Monitoring & Analytics

Track API usage with built-in monitoring:

```python
from api_manager import api_manager

# Get usage statistics
status = api_manager.validate_setup()
print(f"API calls today: {status['calls_made']}")

# Monitor rate limits
limits = api_manager.get_rate_limits()
print(f"Current rate limit: {limits['default']}/second")
```

---

## 🎯 Ready to Start?

1. Set up your `.env` file with API keys
2. Run `python test_api_setup.py` to validate
3. Use `enhanced_balance_checker.py` for balance checking
4. Integrate `api_manager.py` into your existing scripts

Your API configuration is now secure and ready for wallet recovery! 🚀
