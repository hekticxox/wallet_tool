#!/usr/bin/env python3
"""Quick test with just a few addresses to verify the scanner works"""

import sys
import os
import json
import time
import sqlite3
import hashlib
import threading
import logging
import requests
from datetime import datetime, timedelta
from collections import defaultdict

# Add the current directory to the path to import our scanner
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock the missing imports for this test
class MockBip44:
    pass

class MockEthKeys:
    pass

# Import our scanner class
from unified_wallet_scanner import UnifiedWalletScanner

def create_test_addresses():
    """Create a small test file with known addresses"""
    test_addresses = [
        {
            "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "chain": "bitcoin",
            "source": "genesis_block",
            "private_key": "unknown",
            "pattern_score": 10.0
        },
        {
            "address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            "chain": "ethereum", 
            "source": "vitalik_wallet",
            "private_key": "unknown",
            "pattern_score": 15.0
        },
        {
            "address": "1JG5oFpGnj9TQ3v8BqKGCNLEJNK7iEqBr3CwTvie",
            "chain": "bitcoin",
            "source": "test_wallet",
            "private_key": "unknown",
            "pattern_score": 8.0
        }
    ]
    
    with open('test_addresses.json', 'w') as f:
        json.dump(test_addresses, f, indent=2)
    
    print(f"📝 Created test file with {len(test_addresses)} addresses")
    return test_addresses

def test_scanner():
    """Test the scanner with our small set of addresses"""
    
    print("🧪 Starting scanner test with known addresses...")
    
    # Create test data
    test_addresses = create_test_addresses()
    
    # Initialize scanner
    try:
        scanner = UnifiedWalletScanner()
        print("✅ Scanner initialized successfully")
        
        # Test balance checking for each address
        funded_found = 0
        
        for i, addr_data in enumerate(test_addresses, 1):
            address = addr_data['address']
            chain = addr_data['chain']
            source = addr_data['source']
            
            print(f"\n🔍 [{i}/{len(test_addresses)}] Testing {chain} address from {source}")
            print(f"    Address: {address}")
            print(f"    Expected: Should have balance")
            
            # Check balance
            balance = 0
            try:
                print(f"    Checking balance: ", end="", flush=True)
                
                if chain.lower() == 'bitcoin':
                    balance = scanner.check_bitcoin_balance(address)
                elif chain.lower() == 'ethereum':
                    balance = scanner.check_ethereum_balance(address)
                
                if balance > 0:
                    print(f" 💰 SUCCESS! Balance: {balance}")
                    funded_found += 1
                else:
                    print(f" ❌ No balance found")
                    
            except Exception as e:
                print(f" ⚠️ Error: {e}")
        
        print(f"\n📊 Test Results:")
        print(f"    Total addresses tested: {len(test_addresses)}")
        print(f"    Addresses with balance found: {funded_found}")
        print(f"    Success rate: {100 * funded_found / len(test_addresses):.1f}%")
        
        if funded_found == len(test_addresses):
            print("🎉 All tests passed! Scanner is working correctly.")
            return True
        else:
            print("⚠️ Some tests failed. Check API configurations.")
            return False
            
    except Exception as e:
        print(f"❌ Scanner test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_scanner()
    
    if success:
        print("\n✅ Scanner ready to use with real data!")
        print("🚀 Run: python3 unified_wallet_scanner.py --check-balances")
    else:
        print("\n❌ Scanner needs fixes before using with real data")
        
    # Cleanup
    if os.path.exists('test_addresses.json'):
        os.remove('test_addresses.json')
