#!/usr/bin/env python3

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_balance_checker import EnhancedBalanceChecker

def check_zelcore_keys_batch():
    """Check balances for ZelCore extracted keys"""
    
    print("🔍 Checking ZelCore extracted keys for balances...")
    
    # Initialize balance checker
    checker = EnhancedBalanceChecker()
    
    try:
        # Load ZelCore keys
        with open('zelcore_extracted_keys.json', 'r') as f:
            keys_data = json.load(f)
        
        keys = list(keys_data)
        print(f"💰 Loaded {len(keys)} ZelCore keys for balance checking")
        
        # Check first batch of 20 keys for quick test
        batch_size = 20
        sample_keys = keys[:batch_size]
        
        results = []
        
        for i, key in enumerate(sample_keys, 1):
            print(f"\n🔍 Checking key {i}/{len(sample_keys)}: {key[:16]}...{key[-16:]}")
            
            try:
                # Derive Ethereum address from private key
                from eth_keys import keys as eth_keys
                private_key_bytes = bytes.fromhex(key)
                private_key_obj = eth_keys.PrivateKey(private_key_bytes)
                eth_address = private_key_obj.public_key.to_checksum_address()
                
                print(f"   Address: {eth_address}")
                
                # Check Ethereum balance
                balance_result = checker.check_ethereum_balance_multiple_apis(eth_address)
                eth_balance = balance_result.get('final_balance', 0)
                
                result = {
                    'private_key': key,
                    'address': eth_address,
                    'eth_balance': eth_balance,
                    'balance_details': balance_result
                }
                
                if eth_balance > 0:
                    print(f"🎉 FUNDED WALLET! Balance: {eth_balance} ETH")
                    print(f"🔑 Private Key: {key}")
                    print(f"📍 Address: {eth_address}")
                    
                    # Save immediately to avoid losing it
                    with open('ZELCORE_FUNDED_WALLET.json', 'w') as f:
                        json.dump(result, f, indent=2)
                    
                    results.append(result)
                else:
                    print(f"   Balance: {eth_balance} ETH (empty)")
                
            except Exception as e:
                print(f"   ❌ Error processing key: {e}")
                continue
        
        # Save all results
        with open('zelcore_balance_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        funded_count = len([r for r in results if r['eth_balance'] > 0])
        
        if funded_count > 0:
            print(f"\n🎉 SUCCESS! Found {funded_count} funded wallets!")
            for result in results:
                if result['eth_balance'] > 0:
                    print(f"💰 {result['eth_balance']} ETH - {result['address']}")
        else:
            print(f"\n💡 Checked {len(results)} keys - no funded wallets in this batch")
            print("💡 Consider checking more keys if needed")
    
        return results
        
    except Exception as e:
        print(f"❌ Error checking ZelCore keys: {e}")
        return []

if __name__ == "__main__":
    results = check_zelcore_keys_batch()
    
    funded = [r for r in results if r.get('eth_balance', 0) > 0]
    if funded:
        print(f"\n🎯 FINAL RESULT: {len(funded)} funded wallets discovered!")
    else:
        print(f"\n💡 Batch check complete - {len(results)} keys checked")
