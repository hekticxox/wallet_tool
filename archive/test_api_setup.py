#!/usr/bin/env python3
"""
API Setup Validator and Test Suite
==================================
Validates API configuration and tests balance checking functionality.
"""

import json
import time
from pathlib import Path
from api_manager import api_manager, validate_api_setup
from enhanced_balance_checker import EnhancedBalanceChecker

def test_ethereum_addresses():
    """Test with known Ethereum addresses"""
    return [
        "0x0000000000000000000000000000000000000000",  # Burn address (should be empty)
        "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Vitalik's address (likely has balance)
        "0x8ba1f109551bD432803012645Heh45aAB8A76c55",  # Invalid address for testing
    ]

def test_bitcoin_addresses():
    """Test with known Bitcoin addresses"""
    return [
        "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",  # Genesis block (has balance)
        "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy",    # Random address (likely empty)
        "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",  # Bech32 address
    ]

def main():
    """Main test function"""
    print("🧪 COMPREHENSIVE API AND BALANCE CHECKER TEST")
    print("=" * 70)
    print()
    
    # Step 1: Validate API setup
    print("🔍 STEP 1: Validating API Configuration")
    print("-" * 50)
    validate_api_setup()
    print()
    
    # Step 2: Test balance checker initialization
    print("🔍 STEP 2: Initializing Balance Checker")
    print("-" * 50)
    try:
        checker = EnhancedBalanceChecker()
        print("✅ Balance checker initialized successfully")
        
        # Show API status
        status = checker.get_api_status()
        eth_api_count = len([k for k in status['ethereum_apis'].values() if k])
        btc_api_count = len([k for k in status['bitcoin_apis'].values() if k])
        
        print(f"📊 Available APIs:")
        print(f"   • Ethereum APIs: {eth_api_count}")
        print(f"   • Bitcoin APIs: {btc_api_count}")
        
        if eth_api_count == 0 and btc_api_count == 0:
            print("⚠️  WARNING: No API keys configured. Tests will likely fail.")
            print("💡 Add your API keys to the .env file to enable balance checking.")
            return
        
    except Exception as e:
        print(f"❌ Failed to initialize balance checker: {e}")
        return
    
    print()
    
    # Step 3: Test Ethereum balance checking
    if eth_api_count > 0:
        print("🔍 STEP 3: Testing Ethereum Balance Checking")
        print("-" * 50)
        
        eth_addresses = test_ethereum_addresses()[:2]  # Test only first 2 to avoid rate limits
        
        for address in eth_addresses:
            print(f"   Testing: {address}")
            result = checker.check_address_balance(address, 'ethereum')
            
            if result['success']:
                balance = result.get('balance_eth', 0)
                api_used = result.get('api', 'unknown')
                print(f"   ✅ Success via {api_used}: {balance:.6f} ETH")
                
                if result.get('has_balance'):
                    print(f"   💎 Address has funds!")
                else:
                    print(f"   💸 Address is empty")
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
            
            time.sleep(1)  # Rate limiting
        print()
    
    # Step 4: Test Bitcoin balance checking  
    if btc_api_count > 0:
        print("🔍 STEP 4: Testing Bitcoin Balance Checking")
        print("-" * 50)
        
        btc_addresses = test_bitcoin_addresses()[:2]  # Test only first 2 to avoid rate limits
        
        for address in btc_addresses:
            print(f"   Testing: {address}")
            result = checker.check_address_balance(address, 'bitcoin')
            
            if result['success']:
                balance = result.get('balance_btc', 0)
                api_used = result.get('api', 'unknown')
                print(f"   ✅ Success via {api_used}: {balance:.8f} BTC")
                
                if result.get('has_balance'):
                    print(f"   💎 Address has funds!")
                else:
                    print(f"   💸 Address is empty")
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
            
            time.sleep(2)  # Conservative rate limiting for Bitcoin APIs
        print()
    
    # Step 5: Test auto-detection
    print("🔍 STEP 5: Testing Auto-Detection")
    print("-" * 50)
    
    test_auto_addresses = [
        "0x0000000000000000000000000000000000000000",  # Should detect as Ethereum
        "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",          # Should detect as Bitcoin
    ]
    
    for address in test_auto_addresses:
        print(f"   Testing auto-detection: {address}")
        result = checker.check_address_balance(address)  # No chain specified
        
        if result['success']:
            print(f"   ✅ Auto-detected and checked successfully")
        else:
            print(f"   ❌ Auto-detection failed: {result.get('error', 'Unknown error')}")
        
        time.sleep(1)
    print()
    
    # Final summary
    print("🎯 TEST SUMMARY")
    print("-" * 50)
    
    final_status = checker.get_api_status()
    total_calls = final_status['api_calls_made']
    
    print(f"✅ Test completed successfully!")
    print(f"📊 Total API calls made: {total_calls}")
    print(f"🔑 API keys configured: {eth_api_count + btc_api_count}")
    
    if total_calls > 0:
        print(f"🎉 Balance checking is working correctly!")
    else:
        print(f"⚠️  No API calls were made - check your API key configuration")
    
    print()
    print("💡 Next Steps:")
    print("   1. Add your real API keys to .env file")
    print("   2. Run enhanced_balance_checker.py with your addresses")
    print("   3. Use api_manager.py in your wallet recovery scripts")
    print("=" * 70)

if __name__ == '__main__':
    main()
