#!/usr/bin/env python3

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_balance_checker import EnhancedBalanceChecker

def check_zelcore_extended_batch():
    """Check a larger batch of ZelCore keys (keys 21-100)"""
    
    print("🔍 Checking extended ZelCore key batch (keys 21-100)...")
    
    # Initialize balance checker
    checker = EnhancedBalanceChecker()
    
    try:
        # Load ZelCore keys
        with open('zelcore_extracted_keys.json', 'r') as f:
            keys_data = json.load(f)
        
        keys = list(keys_data)
        print(f"💰 Total ZelCore keys available: {len(keys)}")
        
        # Check keys 21-100 (next 80 keys)
        batch_keys = keys[20:100]  # Skip first 20 already checked
        print(f"🔍 Checking keys 21-100 ({len(batch_keys)} keys)...")
        
        results = []
        funded_found = False
        
        for i, key in enumerate(batch_keys, 21):
            print(f"\n🔍 Checking key {i}/{len(keys)}: {key[:16]}...{key[-16:]}")
            
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
                    'index': i,
                    'private_key': key,
                    'address': eth_address,
                    'eth_balance': eth_balance,
                    'balance_details': balance_result
                }
                
                if eth_balance > 0:
                    print(f"🎉 FUNDED WALLET FOUND! Balance: {eth_balance} ETH")
                    print(f"🔑 Private Key: {key}")
                    print(f"📍 Address: {eth_address}")
                    
                    # Save immediately to avoid losing it
                    with open(f'ZELCORE_FUNDED_WALLET_{i}.json', 'w') as f:
                        json.dump(result, f, indent=2)
                    
                    funded_found = True
                    results.append(result)
                    
                    # Also add to master funded list
                    try:
                        if os.path.exists('ALL_FUNDED_WALLETS.json'):
                            with open('ALL_FUNDED_WALLETS.json', 'r') as f:
                                all_funded = json.load(f)
                        else:
                            all_funded = []
                        
                        all_funded.append({
                            'source': 'zelcore_batch2',
                            'key_index': i,
                            **result
                        })
                        
                        with open('ALL_FUNDED_WALLETS.json', 'w') as f:
                            json.dump(all_funded, f, indent=2)
                        
                    except Exception as e:
                        print(f"   Warning: Could not update master list: {e}")
                
                else:
                    print(f"   Balance: {eth_balance} ETH (empty)")
                
            except Exception as e:
                print(f"   ❌ Error processing key {i}: {e}")
                continue
        
        # Save batch results
        with open('zelcore_extended_batch_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        funded_count = len([r for r in results if r['eth_balance'] > 0])
        
        if funded_count > 0:
            print(f"\n🎉 SUCCESS! Found {funded_count} funded wallets in extended batch!")
            for result in results:
                if result['eth_balance'] > 0:
                    print(f"💰 {result['eth_balance']} ETH - {result['address']}")
        else:
            print(f"\n💡 Extended batch complete - checked {len(batch_keys)} more keys")
            print("💡 No funded wallets found in keys 21-100")
            print("🔄 Could continue with more keys if needed")
    
        return results
        
    except Exception as e:
        print(f"❌ Error checking extended ZelCore batch: {e}")
        return []

if __name__ == "__main__":
    results = check_zelcore_extended_batch()
    
    funded = [r for r in results if r.get('eth_balance', 0) > 0]
    if funded:
        print(f"\n🎯 BREAKTHROUGH: {len(funded)} funded wallets discovered in ZelCore!")
    else:
        print(f"\n💡 Extended batch complete - {len(results)} keys processed")
