# Test Scripts

This directory contains various test and validation scripts for the wallet recovery system.

## Available Tests

### API Testing
- `test_all_apis.py` - Comprehensive API functionality testing
- `test_api_setup.py` - API configuration validation
- `test_bitcoin_apis.py` - Bitcoin-specific API testing

### Balance Testing
- `test_batch_simple.py` - Simple batch balance checking
- `test_batch_bitcoin.py` - Bitcoin batch operations
- `test_single_address.py` - Single address validation

### Key Testing
- `test_major_keys.py` - High-priority key validation
- `test_recovery_key.py` - Recovery key functionality
- `test_duplicates.py` - Duplicate detection testing

## Usage

Run individual tests:
```bash
python tests/test_api_setup.py
python tests/test_single_address.py
```

## Test Results Summary

These tests have validated:
- ✅ API connectivity and functionality
- ✅ Balance checking accuracy
- ✅ Key format validation
- ✅ Recovery mechanism testing

## Notes

- Tests are designed for validation and debugging
- Use with caution on live data
- Some tests require API keys configuration
