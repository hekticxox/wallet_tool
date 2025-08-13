#!/usr/bin/env python3

import json
import time
import os
from datetime import datetime
from enhanced_balance_checker import check_balance, load_api_config

def batch_check_extracted_keys():
    """Batch check all extracted keys from net602 and net605"""
    
    print("🚀 BATCH CHECKING EXTRACTED KEYS FROM NET602 AND NET605")
    print("="*70)
    
    # Load API configuration
    api_config = load_api_config()
    if not api_config:
        print("❌ API configuration not found!")
        return
    
    funded_wallets = []
    total_checked = 0
    batch_size = 50
    
    # Load keys from both datasets
    all_keys = []
    sources = []
    
    # Load net602 keys
    try:
        with open('net602_direct_keys.json', 'r') as f:
            net602_data = json.load(f)
            net602_keys = net602_data['private_keys'][:500]  # First 500 keys
            all_keys.extend(net602_keys)
            sources.extend(['net602'] * len(net602_keys))
            print(f"✅ Loaded {len(net602_keys)} keys from NET602")
    except FileNotFoundError:
        print("⚠️  net602_direct_keys.json not found")
    
    # Load net605 keys 
    try:
        with open('net605_direct_keys.json', 'r') as f:
            net605_data = json.load(f)
            net605_keys = net605_data['private_keys'][:500]  # First 500 keys
            all_keys.extend(net605_keys)
            sources.extend(['net605'] * len(net605_keys))
            print(f"✅ Loaded {len(net605_keys)} keys from NET605")
    except FileNotFoundError:
        print("⚠️  net605_direct_keys.json not found")
    
    if not all_keys:
        print("❌ No keys loaded!")
        return
    
    print(f"\n🎯 CHECKING {len(all_keys)} PRIVATE KEYS...")
    print(f"⏱️  Estimated time: {len(all_keys) * 2 / 60:.1f} minutes")
    
    start_time = time.time()
    
    # Process keys in batches
    for i in range(0, len(all_keys), batch_size):
        batch_keys = all_keys[i:i+batch_size]
        batch_sources = sources[i:i+batch_size]
        
        print(f"\n📦 Batch {i//batch_size + 1}: Checking keys {i+1}-{min(i+batch_size, len(all_keys))}")
        
        for j, private_key in enumerate(batch_keys):
            try:
                key_index = i + j + 1
                source = batch_sources[j]
                
                # Check balance (supports both Bitcoin and Ethereum)
                balance_info = check_balance(private_key, api_config)
                
                if balance_info and balance_info.get('total_balance_usd', 0) > 0:
                    print(f"💰 FUNDED WALLET #{key_index} ({source})!")
                    print(f"    Key: {private_key}")
                    print(f"    Balance: ${balance_info['total_balance_usd']:.8f}")
                    for chain, data in balance_info.items():
                        if isinstance(data, dict) and data.get('balance', 0) > 0:
                            print(f"    {chain}: {data['balance']} {data.get('symbol', '')}")
                    
                    funded_wallets.append({
                        'key_index': key_index,
                        'private_key': private_key,
                        'source': source,
                        'balance_info': balance_info,
                        'discovery_time': datetime.now().isoformat()
                    })
                else:
                    # Show progress every 50 keys
                    if key_index % 50 == 0:
                        elapsed = time.time() - start_time
                        rate = key_index / elapsed
                        print(f"    Progress: {key_index}/{len(all_keys)} ({key_index/len(all_keys)*100:.1f}%) - {rate:.1f} keys/sec")
                
                total_checked += 1
                
                # Rate limiting
                time.sleep(1.5)  # Slower rate for stability
                
            except Exception as e:
                print(f"    Error checking key {key_index}: {str(e)}")
                continue
        
        # Save progress after each batch
        if funded_wallets:
            progress_file = f'funded_keys_batch_{i//batch_size + 1}.json'
            with open(progress_file, 'w') as f:
                json.dump(funded_wallets, f, indent=2)
    
    elapsed_time = time.time() - start_time
    
    print(f"\n📊 BATCH CHECK COMPLETE!")
    print(f"   ⏱️  Time taken: {elapsed_time/60:.1f} minutes")
    print(f"   🔍 Keys checked: {total_checked}")
    print(f"   💰 Funded wallets found: {len(funded_wallets)}")
    
    if funded_wallets:
        # Save final results
        final_results = {
            'check_date': datetime.now().isoformat(),
            'total_keys_checked': total_checked,
            'funded_wallets_count': len(funded_wallets),
            'sources': ['net602', 'net605'],
            'funded_wallets': funded_wallets
        }
        
        with open('MAJOR_DISCOVERY_net602_net605.json', 'w') as f:
            json.dump(final_results, f, indent=2)
        
        print(f"\n🎉 FUNDED WALLETS DISCOVERED:")
        for wallet in funded_wallets:
            print(f"   #{wallet['key_index']} ({wallet['source']}): ${wallet['balance_info']['total_balance_usd']:.8f}")
        
        print(f"\n💾 Results saved: MAJOR_DISCOVERY_net602_net605.json")
        print("🚨 SECURE THESE PRIVATE KEYS IMMEDIATELY!")
    else:
        print("\n😔 No funded wallets found in this batch")
        print("   Continuing systematic search...")

if __name__ == "__main__":
    batch_check_extracted_keys()
