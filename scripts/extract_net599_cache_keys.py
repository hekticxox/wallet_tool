#!/usr/bin/env python3

import json
import re
from collections import defaultdict

def extract_keys_from_cache():
    """Extract private keys from the API cache file"""
    
    print("🔍 Extracting private keys from net599 cache file...")
    
    try:
        # Read the cache file
        with open('/home/admin/Downloads/net599/.api_checked_cache.json', 'r') as f:
            cache_data = json.load(f)
        
        private_keys = set()
        
        # Extract all keys from the cache
        for key, value in cache_data.items():
            # Look for 64-character hex strings (Ethereum private keys)
            if re.match(r'^[a-fA-F0-9]{64}$', key):
                # Validate it's not all zeros or ones
                if (not all(c == '0' for c in key) and
                    not all(c == 'f' for c in key.lower()) and
                    not all(c == '1' for c in key) and
                    key.count('0') < 50):  # Not mostly zeros
                    
                    private_keys.add(key.lower())
        
        print(f"✅ Found {len(private_keys)} unique private keys in cache")
        
        if private_keys:
            # Save keys
            with open('net599_cache_keys.txt', 'w') as f:
                for key in sorted(private_keys):
                    f.write(f"{key}\n")
            
            print(f"💾 Keys saved to net599_cache_keys.txt")
            
            # Show first 10 keys
            print("\nFirst 10 private keys from cache:")
            for i, key in enumerate(sorted(private_keys)[:10], 1):
                print(f"{i:2d}. {key}")
            
            # Check if any have been marked as having balances (value = True)
            funded_keys = []
            for key, has_balance in cache_data.items():
                if (re.match(r'^[a-fA-F0-9]{64}$', key) and 
                    has_balance is True and
                    key.lower() in private_keys):
                    funded_keys.append(key.lower())
            
            if funded_keys:
                print(f"\n🎉 JACKPOT! Found {len(funded_keys)} keys marked as FUNDED in cache:")
                for i, key in enumerate(funded_keys, 1):
                    print(f"💰 {i}. {key}")
                
                with open('net599_FUNDED_keys.txt', 'w') as f:
                    for key in funded_keys:
                        f.write(f"{key}\n")
                print(f"💾 FUNDED keys saved to net599_FUNDED_keys.txt")
            else:
                print("\n💡 No keys marked as funded in cache (all show False or True for 'checked' status)")
        
        return list(private_keys)
        
    except Exception as e:
        print(f"❌ Error extracting from cache: {e}")
        return []

if __name__ == "__main__":
    keys = extract_keys_from_cache()
    
    if keys:
        print(f"\n🎯 SUCCESS: Extracted {len(keys)} private keys from net599 cache!")
        print("🚀 Ready to check balances!")
    else:
        print("\n❌ No private keys found in cache")
