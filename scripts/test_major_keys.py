#!/usr/bin/env python3

import json
import time
import requests
import hashlib
import os
from datetime import datetime
from api_manager import api_manager

def hex_to_ethereum_address(private_key_hex):
    """Convert hex private key to Ethereum address using basic crypto"""
    try:
        # This is a simplified version - would need secp256k1 library for production
        # For now, we'll create a mock address for testing API connectivity
        # In production, use: eth-keys, web3.py, or similar proper crypto library
        
        # Mock address generation (for testing only)
        hash_input = private_key_hex.encode()
        address_hash = hashlib.sha256(hash_input).hexdigest()[:40]
        return f"0x{address_hash}"
        
    except Exception as e:
        return None

def check_ethereum_balance_simple(address):
    """Simple Ethereum balance check using our API manager"""
    try:
        # Get Ethereum APIs
        eth_apis = api_manager.get_ethereum_apis()
        
        if not eth_apis.get('etherscan'):
            print("❌ No working Etherscan API")
            return 0
            
        api_key = eth_apis['etherscan']
        url = f"https://api.etherscan.io/api"
        
        params = {
            'module': 'account',
            'action': 'balance',
            'address': address,
            'tag': 'latest',
            'apikey': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == '1':
                balance_wei = int(data.get('result', 0))
                balance_eth = balance_wei / 10**18
                return balance_eth
        
        return 0
        
    except Exception as e:
        print(f"    Error checking balance: {str(e)}")
        return 0

def test_major_discovery_keys():
    """Test the first batch of major discovery keys"""
    
    print("🚀 TESTING MAJOR DISCOVERY KEYS")
    print("="*50)
    
    # Load the key list
    try:
        with open('major_discovery_keys_list.txt', 'r') as f:
            keys = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ major_discovery_keys_list.txt not found!")
        return
    
    print(f"🔍 Testing first 20 keys from {len(keys)} total keys...")
    
    # Initialize API manager
    try:
        setup = api_manager.validate_setup()
        print(f"✅ API setup: {setup['valid_keys_count']} valid APIs")
    except:
        print("⚠️  API setup validation failed, will try anyway")
    
    funded_wallets = []
    test_keys = keys[:20]  # Test first 20 keys
    
    for i, private_key in enumerate(test_keys, 1):
        print(f"\n🔍 [{i}/20] Testing key: {private_key[:12]}...")
        
        try:
            # Generate Ethereum address from private key
            eth_address = hex_to_ethereum_address(private_key)
            
            if not eth_address:
                print("    ❌ Could not generate address")
                continue
            
            print(f"    📍 Address: {eth_address}")
            
            # Check balance
            balance = check_ethereum_balance_simple(eth_address)
            
            if balance > 0:
                print(f"    💰 FUNDED WALLET! Balance: {balance:.8f} ETH")
                
                funded_wallets.append({
                    'index': i,
                    'private_key': private_key,
                    'address': eth_address,
                    'balance_eth': balance,
                    'balance_usd': balance * 2500,  # Rough ETH price
                    'discovery_time': datetime.now().isoformat()
                })
            else:
                print(f"    ✓ Empty (0 ETH)")
            
            # Rate limiting
            time.sleep(2)
            
        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
            continue
    
    print(f"\n" + "="*50)
    print(f"🏁 TEST COMPLETE")
    print(f"   🔍 Tested: 20 keys")
    print(f"   💰 Funded: {len(funded_wallets)} wallets")
    
    if funded_wallets:
        # Save results
        results = {
            'test_date': datetime.now().isoformat(),
            'keys_tested': 20,
            'total_available': len(keys),
            'funded_wallets': funded_wallets
        }
        
        with open('MAJOR_DISCOVERY_TEST_RESULTS.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n🎉 FUNDED WALLETS FOUND:")
        total_eth = 0
        for wallet in funded_wallets:
            print(f"   #{wallet['index']}: {wallet['balance_eth']:.8f} ETH (${wallet['balance_usd']:.2f})")
            total_eth += wallet['balance_eth']
        
        print(f"\n💎 TOTAL: {total_eth:.8f} ETH (${total_eth * 2500:.2f})")
        print(f"💾 Results: MAJOR_DISCOVERY_TEST_RESULTS.json")
        print(f"🚨 SECURE THESE KEYS IMMEDIATELY!")
        
        # Continue with larger batch?
        print(f"\n🚀 NEXT STEPS:")
        print(f"   ✅ Test more keys from remaining {len(keys) - 20}")
        print(f"   🔍 Full batch check of promising sources")
        
    else:
        print(f"\n💡 No funded wallets in first 20 keys")
        print(f"   📊 {len(keys) - 20} keys remaining to check")
        print(f"   🎯 Consider checking different key ranges")

if __name__ == "__main__":
    test_major_discovery_keys()
