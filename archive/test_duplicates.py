#!/usr/bin/env python3
"""
Test duplicate prevention in balance checking
"""

import json
import tempfile
from unified_wallet_scanner import UnifiedWalletScanner

def test_duplicate_prevention():
    """Test that duplicate addresses are properly handled"""
    
    print("🧪 Testing Duplicate Prevention in Balance Checking")
    print("="*55)
    
    # Create test data with intentional duplicates
    test_addresses = [
        {
            "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "chain": "bitcoin",
            "private_key": "test_key_1",
            "pattern_score": 10.0
        },
        {
            "address": "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",  
            "chain": "bitcoin",
            "private_key": "test_key_2",
            "pattern_score": 9.0
        },
        {
            "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",  # DUPLICATE
            "chain": "bitcoin", 
            "private_key": "test_key_1",
            "pattern_score": 8.0
        },
        {
            "address": "1JArS6jzE3AJ9sZ3aFij1BmTcpFGgN86hA",
            "chain": "bitcoin",
            "private_key": "test_key_3", 
            "pattern_score": 7.0
        },
        {
            "address": "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",  # DUPLICATE
            "chain": "bitcoin",
            "private_key": "test_key_2",
            "pattern_score": 6.0
        }
    ]
    
    # Count duplicates in test data
    addresses = [item['address'] for item in test_addresses]
    unique_addresses = set(addresses)
    
    print(f"📊 Test data:")
    print(f"   Total addresses: {len(addresses)}")
    print(f"   Unique addresses: {len(unique_addresses)}")
    print(f"   Duplicates: {len(addresses) - len(unique_addresses)}")
    print()
    
    # Test batch duplicate removal
    scanner = UnifiedWalletScanner()
    
    print("🔍 Testing batch duplicate removal...")
    batch_addresses = [addr['address'] for addr in test_addresses]
    print(f"   Input addresses: {len(batch_addresses)}")
    
    # Test the batch function's duplicate handling
    results = scanner.check_bitcoin_balance_batch(batch_addresses)
    print(f"   Results returned: {len(results)}")
    print()
    
    # Show results
    print("📋 Batch results:")
    for addr, balance in results.items():
        print(f"   {addr[:20]}... = {balance:.8f} BTC")
    
    print(f"\n✅ Duplicate prevention test completed!")
    print(f"📈 The system should handle duplicates gracefully without extra API calls")

if __name__ == "__main__":
    test_duplicate_prevention()
