#!/usr/bin/env python3

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_balance_checker import EnhancedBalanceChecker

def check_funded_keys_sample():
    """Check balances for the first few funded keys from net599"""
    
    print("🎯 Checking balances for FUNDED keys from net599...")
    
    # Initialize balance checker
    checker = EnhancedBalanceChecker()
    
    try:
        # Read the funded keys
        with open('net599_FUNDED_keys.txt', 'r') as f:
            funded_keys = [line.strip() for line in f if line.strip()]
        
        print(f"💰 Found {len(funded_keys)} funded keys in cache")
        
        # Check first 5 keys for immediate verification
        sample_keys = funded_keys[:5]
        
        results = []
        
        for i, key in enumerate(sample_keys, 1):
            print(f"\n🔍 Checking key {i}/5: {key[:16]}...{key[-16:]}")
            
            # Derive Ethereum address from private key
            try:
                from eth_keys import keys
                private_key_bytes = bytes.fromhex(key)
                private_key_obj = keys.PrivateKey(private_key_bytes)
                eth_address = private_key_obj.public_key.to_checksum_address()
                
                print(f"   Address: {eth_address}")
                
                # Check Ethereum balance
                balance_result = checker.check_ethereum_balance_multiple_apis(eth_address)
                eth_balance = balance_result.get('final_balance', 0)
                
            except Exception as e:
                print(f"   Error deriving address: {e}")
                continue
            
            if eth_balance > 0:
                print(f"🎉 FUNDED ETH WALLET! Balance: {eth_balance} ETH")
                results.append({
                    'key': key,
                    'balance': eth_balance,
                    'currency': 'ETH'
                })
            else:
                print(f"   ETH: {eth_balance}")
        
        if results:
            print(f"\n🏆 CONFIRMED FUNDED WALLETS FOUND!")
            for result in results:
                print(f"💰 {result['currency']}: {result['balance']} - Key: {result['key']}")
            
            # Save confirmed results
            with open('CONFIRMED_FUNDED_WALLETS.json', 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"\n💾 Confirmed wallets saved to CONFIRMED_FUNDED_WALLETS.json")
        else:
            print(f"\n⚠️  Sample check complete - checking larger batch...")
    
        return results
        
    except Exception as e:
        print(f"❌ Error checking funded keys: {e}")
        return []

if __name__ == "__main__":
    results = check_funded_keys_sample()
    
    if results:
        print(f"\n🎯 SUCCESS! Found {len(results)} confirmed funded wallets!")
    else:
        print(f"\n💡 Sample check complete - may need to check more keys")
