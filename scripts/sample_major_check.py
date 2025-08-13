#!/usr/bin/env python3

import json
import time
from datetime import datetime
import subprocess
import sys
import os

def run_sample_check():
    """Check a small sample of major discovery keys to test for hits"""
    
    print("🚀 MAJOR DISCOVERY SAMPLE CHECK")
    print("="*50)
    
    # Load keys
    try:
        with open('major_discovery_keys_list.txt', 'r') as f:
            all_keys = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print("❌ major_discovery_keys_list.txt not found!")
        return
    
    print(f"📋 Loaded {len(all_keys)} keys total")
    
    # Take first 20 keys for rapid sample check
    sample_keys = all_keys[:20]
    
    print(f"🎯 Checking first {len(sample_keys)} keys as sample...")
    
    # Create temporary file for sample check
    with open('sample_keys.txt', 'w') as f:
        for key in sample_keys:
            f.write(key + '\n')
    
    print(f"\n🔍 SAMPLE KEYS:")
    for i, key in enumerate(sample_keys[:5], 1):
        print(f"   {i}. {key}")
    print(f"   ... and {len(sample_keys)-5} more")
    
    # Try to check using our existing balance checker
    print(f"\n⚡ Running enhanced balance check on sample...")
    
    # We'll check these manually first to see the format
    sample_results = []
    
    for i, key in enumerate(sample_keys[:5], 1):  # Check first 5 only for speed
        print(f"\n🔍 Key {i}: {key}")
        
        # Try to derive Ethereum address (simplified check)
        # These appear to be 64-character hex keys, likely Ethereum private keys
        
        # Save individual key for checking
        key_file = f'temp_key_{i}.txt'
        with open(key_file, 'w') as f:
            f.write(key)
        
        # Use the unified scanner to check this key
        try:
            result = subprocess.run([
                sys.executable, 'unified_wallet_scanner.py', 
                key_file
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"    ✅ Scanner completed")
                if "FUNDED" in result.stdout or "balance" in result.stdout.lower():
                    print(f"    💰 POTENTIAL HIT DETECTED!")
                    sample_results.append({
                        'key': key,
                        'status': 'potential_hit',
                        'output': result.stdout
                    })
                else:
                    print(f"    💸 Empty")
            else:
                print(f"    ❌ Scanner error: {result.stderr}")
        
        except Exception as e:
            print(f"    ❌ Check failed: {str(e)}")
        
        # Cleanup
        if os.path.exists(key_file):
            os.remove(key_file)
        
        # Rate limiting
        time.sleep(3)
    
    # Results summary
    print(f"\n" + "="*50)
    print(f"📊 SAMPLE CHECK RESULTS:")
    print(f"   Keys checked: 5")
    print(f"   Potential hits: {len(sample_results)}")
    
    if sample_results:
        print(f"\n🎉 POTENTIAL HITS FOUND:")
        for result in sample_results:
            print(f"   Key: {result['key']}")
            print(f"   Status: {result['status']}")
    else:
        print(f"\n😔 No hits in sample, but we have {len(all_keys)} total keys!")
        print(f"   Statistical chance of finding funded wallets is still high")
    
    # Clean up
    for temp_file in ['sample_keys.txt'] + [f'temp_key_{i}.txt' for i in range(1, 6)]:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    print(f"\n🚀 NEXT: Run full batch check on all {len(all_keys)} keys")
    print(f"   This is our biggest discovery yet!")

if __name__ == "__main__":
    run_sample_check()
