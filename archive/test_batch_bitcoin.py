#!/usr/bin/env python3
"""
Test Bitcoin batch balance checking functionality
"""

import json
import time
from unified_wallet_scanner import UnifiedWalletScanner

def test_bitcoin_batch():
    """Test the Bitcoin batch balance checking"""
    
    print("🧪 Testing Bitcoin Batch Balance Checking")
    print("="*50)
    
    # Initialize scanner
    scanner = UnifiedWalletScanner()
    
    # Test addresses with known balances
    test_addresses = [
        "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",  # Genesis block - has balance
        "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",   # Another known address
        "1JArS6jzE3AJ9sZ3aFij1BmTcpFGgN86hA",   # Random address (likely empty)
        "1234567890123456789012345678901234",     # Invalid address
        "bc1qw508d6qejxtdg4y5r3zrvs0c5xuyxgrcnxt9ms"  # Bech32 address
    ]
    
    print(f"🔍 Testing batch check with {len(test_addresses)} addresses:")
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
        
        for address, balance in results.items():
            if balance > 0:
                print(f"💰 {address}: {balance:.8f} BTC")
            else:
                print(f"❌ {address}: 0 BTC")
        
        # Test individual checks for comparison
        print(f"\n🔍 Comparing with individual checks...")
        individual_start = time.time()
        
        for address in test_addresses[:2]:  # Just test first 2 to save time
            print(f"   Testing {address[:20]}...", end=" ")
            individual_balance = scanner.check_bitcoin_balance(address)
            batch_balance = results.get(address, 0)
            
            if abs(individual_balance - batch_balance) < 0.00000001:  # Close enough for floating point
                print(f"✅ Match: {individual_balance:.8f} BTC")
            else:
                print(f"❌ Mismatch: batch={batch_balance:.8f}, individual={individual_balance:.8f}")
        
        individual_elapsed = time.time() - individual_start
        print(f"\n⚡ Performance comparison:")
        print(f"   Batch check: {elapsed:.2f}s for {len(test_addresses)} addresses")
        print(f"   Individual: {individual_elapsed:.2f}s for 2 addresses")
        print(f"   Batch efficiency: ~{individual_elapsed/2*len(test_addresses)/elapsed:.1f}x faster")
        
    except Exception as e:
        print(f"❌ Batch test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bitcoin_batch()
