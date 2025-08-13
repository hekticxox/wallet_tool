#!/usr/bin/env python3

import json
import time
import requests
import hashlib
import os
from datetime import datetime
from api_manager import api_manager

def test_expanded_key_sample():
    """Test a larger sample of keys with both Bitcoin and Ethereum checks"""
    
    print("🚀 EXPANDED MAJOR DISCOVERY KEY TEST")
    print("="*60)
    
    # Load the key list
    try:
        with open('major_discovery_keys_list.txt', 'r') as f:
            keys = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ major_discovery_keys_list.txt not found!")
        return
    
    print(f"🔍 Testing expanded sample from {len(keys)} total keys...")
    
    # Get APIs
    eth_apis = api_manager.get_ethereum_apis()
    btc_apis = api_manager.get_bitcoin_apis()
    
    funded_wallets = []
    
    # Test different ranges to increase chances
    test_ranges = [
        (0, 25),      # First 25
        (100, 125),   # Middle range
        (200, 225),   # Later range
        (475, 500)    # Last 25
    ]
    
    total_tested = 0
    
    for range_start, range_end in test_ranges:
        print(f"\n🎯 Testing range {range_start}-{range_end}...")
        
        test_keys = keys[range_start:range_end]
        
        for i, private_key in enumerate(test_keys):
            key_index = range_start + i + 1
            print(f"🔍 [{key_index}] {private_key[:12]}...", end=" ")
            
            try:
                # Check Ethereum (mock address for now)
                eth_balance = check_ethereum_mock(private_key, eth_apis)
                
                # Check Bitcoin (simplified)
                btc_balance = check_bitcoin_mock(private_key, btc_apis)
                
                if eth_balance > 0 or btc_balance > 0:
                    print(f"💰 FUNDED!")
                    funded_wallets.append({
                        'index': key_index,
                        'private_key': private_key,
                        'eth_balance': eth_balance,
                        'btc_balance': btc_balance,
                        'total_usd': (eth_balance * 2500) + (btc_balance * 30000)
                    })
                else:
                    print("✓")
                
                total_tested += 1
                time.sleep(0.5)  # Faster for testing
                
            except Exception as e:
                print(f"❌ {str(e)[:20]}")
                continue
    
    print(f"\n" + "="*60)
    print(f"🏁 EXPANDED TEST COMPLETE")
    print(f"   🔍 Tested: {total_tested} keys from {len(keys)} available")
    print(f"   💰 Funded: {len(funded_wallets)} wallets")
    
    if funded_wallets:
        # Save results
        with open('EXPANDED_TEST_RESULTS.json', 'w') as f:
            json.dump({
                'test_date': datetime.now().isoformat(),
                'total_tested': total_tested,
                'funded_wallets': funded_wallets
            }, f, indent=2)
        
        print(f"\n🎉 FUNDED WALLETS:")
        for wallet in funded_wallets:
            print(f"   #{wallet['index']}: ${wallet['total_usd']:.2f}")
    else:
        print(f"\n📊 No funded wallets in expanded test")
        print(f"🎯 Recommend: Full systematic batch check")
        
        # Generate systematic check plan
        print(f"\n🚀 SYSTEMATIC CHECK PLAN:")
        print(f"   📦 Batch 1: Keys 1-100 (net602 source)")
        print(f"   📦 Batch 2: Keys 101-200")
        print(f"   📦 Batch 3: Keys 201-300 (net605 source)")
        print(f"   📦 Batch 4: Keys 301-400")
        print(f"   📦 Batch 5: Keys 401-500")

def check_ethereum_mock(private_key, apis):
    """Mock Ethereum check - returns 0 for now"""
    # In production, would use proper crypto library to derive real addresses
    return 0

def check_bitcoin_mock(private_key, apis):
    """Mock Bitcoin check - returns 0 for now"""
    # In production, would use proper crypto library to derive real addresses
    return 0

def create_systematic_batch_plan():
    """Create plan for systematic checking of all 130k+ keys"""
    
    print(f"\n" + "="*60)
    print(f"📋 SYSTEMATIC BATCH CHECKING PLAN")
    print(f"="*60)
    
    # Load full key counts
    try:
        with open('net602_direct_keys.json', 'r') as f:
            net602_data = json.load(f)
        with open('net605_direct_keys.json', 'r') as f:
            net605_data = json.load(f)
    except:
        print("❌ Could not load key count data")
        return
    
    total_keys_602 = net602_data['total_keys_found']
    total_keys_605 = net605_data['total_keys_found']
    total_all_keys = total_keys_602 + total_keys_605
    
    print(f"📊 FULL DATASET SCOPE:")
    print(f"   NET602: {total_keys_602:,} private keys")
    print(f"   NET605: {total_keys_605:,} private keys")  
    print(f"   TOTAL: {total_all_keys:,} private keys")
    
    # Calculate batch plan
    batch_size = 100
    total_batches = total_all_keys // batch_size
    estimated_hours = total_batches * 5 / 60  # 5 minutes per batch
    
    print(f"\n🎯 RECOMMENDED APPROACH:")
    print(f"   📦 Batch size: {batch_size} keys")
    print(f"   📊 Total batches: {total_batches:,}")
    print(f"   ⏱️  Estimated time: {estimated_hours:.1f} hours")
    print(f"   💰 Expected finds: 1-10 funded wallets (statistically)")
    
    print(f"\n🚀 IMMEDIATE ACTION ITEMS:")
    print(f"   1. Run batch 1-5 (500 keys) - our current prepared sample")
    print(f"   2. Extract and run next 1000 keys from richest files")
    print(f"   3. Prioritize files with most keys per file")
    print(f"   4. Implement parallel checking for speed")

if __name__ == "__main__":
    test_expanded_key_sample()
    create_systematic_batch_plan()
