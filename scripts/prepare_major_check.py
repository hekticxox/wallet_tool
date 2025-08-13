#!/usr/bin/env python3

import json
import os
import subprocess
import sys

def run_batch_checks():
    """Run batch checks on the newly extracted keys"""
    
    print("🚀 RUNNING BATCH BALANCE CHECKS ON MAJOR DISCOVERY")
    print("="*60)
    
    # Check if we have the extracted key files
    key_files = ['net602_direct_keys.json', 'net605_direct_keys.json']
    
    for key_file in key_files:
        if os.path.exists(key_file):
            with open(key_file, 'r') as f:
                data = json.load(f)
            
            print(f"\n📁 {key_file}:")
            print(f"   Total keys: {data['total_keys_found']}")
            print(f"   Keys in file: {len(data['private_keys'])}")
            print(f"   Source: {data['source']}")
        else:
            print(f"❌ {key_file} not found")
    
    # Create a combined key file for batch checking
    print(f"\n🔗 CREATING COMBINED KEY FILE...")
    
    all_keys = []
    
    # Load NET602 keys (first 250)
    try:
        with open('net602_direct_keys.json', 'r') as f:
            net602_data = json.load(f)
            net602_keys = net602_data['private_keys'][:250]
            for key in net602_keys:
                all_keys.append({
                    'private_key': key,
                    'source': 'net602',
                    'format': 'hex'
                })
    except:
        pass
    
    # Load NET605 keys (first 250) 
    try:
        with open('net605_direct_keys.json', 'r') as f:
            net605_data = json.load(f)
            net605_keys = net605_data['private_keys'][:250]
            for key in net605_keys:
                all_keys.append({
                    'private_key': key,
                    'source': 'net605',
                    'format': 'hex'
                })
    except:
        pass
    
    if not all_keys:
        print("❌ No keys to check!")
        return
    
    # Save combined keys
    combined_data = {
        'extraction_date': '2025-08-12',
        'sources': ['net602', 'net605'],
        'total_keys': len(all_keys),
        'keys': all_keys
    }
    
    with open('combined_major_discovery_keys.json', 'w') as f:
        json.dump(combined_data, f, indent=2)
    
    print(f"✅ Created combined file with {len(all_keys)} keys")
    
    # Create a simple list for the batch checker
    simple_keys = [item['private_key'] for item in all_keys]
    
    with open('major_discovery_keys_list.txt', 'w') as f:
        for key in simple_keys:
            f.write(key + '\n')
    
    print(f"✅ Created key list: major_discovery_keys_list.txt")
    print(f"\n🎯 READY TO CHECK {len(simple_keys)} KEYS!")
    print(f"   Use: python batch_balance_checker.py with the generated keys")
    
    return len(simple_keys)

if __name__ == "__main__":
    count = run_batch_checks()
    if count:
        print(f"\n🚀 NEXT: Run balance checks on {count} high-priority keys!")
        print("   This is our biggest potential discovery yet!")
