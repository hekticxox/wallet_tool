#!/usr/bin/env python3

import json
import re

def extract_unchecked_keys():
    """Extract private keys marked as False (unchecked) in cache"""
    
    print("🔍 Extracting UNCHECKED private keys from net599 cache...")
    
    try:
        # Read the cache file
        with open('/home/admin/Downloads/net599/.api_checked_cache.json', 'r') as f:
            cache_data = json.load(f)
        
        unchecked_keys = []
        checked_empty_keys = []
        
        # Extract keys based on their status
        for key, status in cache_data.items():
            # Look for 64-character hex strings (Ethereum private keys)
            if re.match(r'^[a-fA-F0-9]{64}$', key):
                # Validate it's not all zeros or ones
                if (not all(c == '0' for c in key) and
                    not all(c == 'f' for c in key.lower()) and
                    not all(c == '1' for c in key) and
                    key.count('0') < 50):  # Not mostly zeros
                    
                    if status is False:
                        unchecked_keys.append(key.lower())
                    elif status is True:
                        checked_empty_keys.append(key.lower())
        
        print(f"✅ Found {len(unchecked_keys)} UNCHECKED private keys")
        print(f"📊 Found {len(checked_empty_keys)} checked empty keys")
        
        if unchecked_keys:
            # Save unchecked keys (these might have funds!)
            with open('net599_UNCHECKED_keys.txt', 'w') as f:
                for key in unchecked_keys:
                    f.write(f"{key}\n")
            
            print(f"💾 Unchecked keys saved to net599_UNCHECKED_keys.txt")
            
            # Show first 10 unchecked keys
            print("\nFirst 10 UNCHECKED keys (high priority):")
            for i, key in enumerate(unchecked_keys[:10], 1):
                print(f"{i:2d}. {key}")
        
        # Also save checked empty for reference
        if checked_empty_keys:
            with open('net599_checked_empty_keys.txt', 'w') as f:
                for key in checked_empty_keys:
                    f.write(f"{key}\n")
            print(f"📝 Checked empty keys saved to net599_checked_empty_keys.txt")
        
        return unchecked_keys
        
    except Exception as e:
        print(f"❌ Error extracting unchecked keys: {e}")
        return []

if __name__ == "__main__":
    unchecked = extract_unchecked_keys()
    
    if unchecked:
        print(f"\n🎯 Found {len(unchecked)} UNCHECKED keys - these are HIGH PRIORITY!")
        print("💡 These keys have never been checked and might contain funds!")
    else:
        print(f"\n❌ No unchecked keys found")
