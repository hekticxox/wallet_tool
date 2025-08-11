#!/usr/bin/env python3
"""
Test Bitcoin batch balance checking with valid addresses only
"""

import json
import time
from unified_wallet_scanner import UnifiedWalletScanner

def test_bitcoin_batch_simple():
    """Test the Bitcoin batch balance checking with known valid addresses"""
    
    print("🧪 Testing Bitcoin Batch Balance Checking (Valid Addresses Only)")
    print("="*60)
    
    # Initialize scanner
    scanner = UnifiedWalletScanner()
    
    # Test addresses - all valid Bitcoin addresses
    test_addresses = [
        "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",  # Genesis block - has balance
        "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",   # Another known address with balance
        "1JArS6jzE3AJ9sZ3aFij1BmTcpFGgN86hA"    # Random address (might be empty)
    ]
    
    print(f"🔍 Testing batch check with {len(test_addresses)} valid addresses:")
    for i, addr in enumerate(test_addresses, 1):
        print(f"   {i}. {addr}")
    print()
    
    # Test batch function
    print("🌐 Running batch balance check...")
    start_time = time.time()
    
    try:
        results = scanner.check_bitcoin_balance_batch(test_addresses)
        elapsed = time.time() - start_time
        
        print(f"\n✅ Batch check completed in {elapsed:.2f} seconds")
        print("\n📊 Results:")
        
        total_balance = 0
        for address, balance in results.items():
            if balance > 0:
                print(f"💰 {address}: {balance:.8f} BTC")
                total_balance += balance
            else:
                print(f"❌ {address}: 0 BTC")
        
        print(f"\n📈 Total balance found: {total_balance:.8f} BTC")
        
        if total_balance > 0:
            print("🎉 Batch test successful - found funded addresses!")
        else:
            print("ℹ️  No funded addresses in test batch (this is expected)")
        
    except Exception as e:
        print(f"❌ Batch test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bitcoin_batch_simple()
