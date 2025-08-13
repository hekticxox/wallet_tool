#!/usr/bin/env python3

import re
import json
from collections import defaultdict

def extract_private_keys_from_scan():
    """Extract private keys from net599 scan results"""
    
    private_keys = set()
    addresses = set()
    key_sources = defaultdict(list)
    
    print("🔍 Extracting private keys from net599 scan results...")
    
    try:
        with open('net599_scan_results.txt', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Look for Ethereum private keys (64 hex characters)
            eth_key_pattern = r'\b([a-fA-F0-9]{64})\b'
            eth_matches = re.findall(eth_key_pattern, content)
            
            # Look for Bitcoin WIF private keys
            wif_pattern = r'\b([5KL][1-9A-HJ-NP-Za-km-z]{50,51})\b'
            wif_matches = re.findall(wif_pattern, content)
            
            # Look for compressed WIF keys
            compressed_wif_pattern = r'\b([KL][1-9A-HJ-NP-Za-km-z]{51})\b'
            compressed_wif_matches = re.findall(compressed_wif_pattern, content)
            
            # Combine all private keys
            all_keys = []
            
            # Filter Ethereum keys (must be exactly 64 hex chars, not all zeros/ones)
            for key in eth_matches:
                if (len(key) == 64 and 
                    not all(c == '0' for c in key) and 
                    not all(c == 'f' for c in key.lower()) and
                    not all(c == '1' for c in key)):
                    all_keys.append(key.lower())
                    key_sources['ethereum'].append(key.lower())
            
            # Add WIF keys
            for key in wif_matches + compressed_wif_matches:
                all_keys.append(key)
                key_sources['bitcoin'].append(key)
            
            private_keys.update(all_keys)
        
        print(f"✅ Found {len(private_keys)} unique private keys")
        print(f"   - Ethereum keys: {len(key_sources['ethereum'])}")
        print(f"   - Bitcoin WIF keys: {len(key_sources['bitcoin'])}")
        
        # Save unique private keys
        unique_keys = list(private_keys)
        
        with open('net599_private_keys.txt', 'w') as f:
            for key in unique_keys:
                f.write(f"{key}\n")
        
        print(f"💾 Private keys saved to net599_private_keys.txt")
        
        # Show first 10 keys
        print("\nFirst 10 private keys found:")
        for i, key in enumerate(unique_keys[:10], 1):
            key_type = "ETH" if len(key) == 64 and key.isalnum() else "BTC"
            print(f"{i:2d}. {key} ({key_type})")
            
        return unique_keys
        
    except Exception as e:
        print(f"❌ Error extracting keys: {e}")
        return []

if __name__ == "__main__":
    keys = extract_private_keys_from_scan()
    
    if keys:
        print(f"\n🎯 SUCCESS: Found {len(keys)} private keys from net599!")
        print("💡 Next: Check balances for these keys")
    else:
        print("\n❌ No private keys extracted from net599")
