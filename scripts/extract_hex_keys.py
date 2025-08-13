#!/usr/bin/env python3

import json
import re
import os

def extract_hex_private_keys(filename):
    """Extract hex private keys from scan results"""
    
    print(f"🔍 EXTRACTING HEX PRIVATE KEYS FROM {filename}...")
    
    private_keys = set()
    addresses = set()
    
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Pattern 1: Full hex keys (64 characters)
        hex_pattern = r'\b[a-fA-F0-9]{64}\b'
        hex_matches = re.findall(hex_pattern, content)
        
        for hex_key in hex_matches:
            # Validate it looks like a private key (not all zeros, not sequential)
            if hex_key != '0' * 64 and not all(c == hex_key[0] for c in hex_key):
                private_keys.add(hex_key.lower())
        
        # Pattern 2: Truncated keys in format "start...end"
        truncated_pattern = r'🔑 PRIVATE KEY: ([a-fA-F0-9]{8})\.\.\.([a-fA-F0-9]{8})'
        truncated_matches = re.findall(truncated_pattern, content)
        
        # For truncated keys, we need to find the full key in context
        for start, end in truncated_matches:
            # Look for the full key around this truncated reference
            context_pattern = rf'\b{re.escape(start)}[a-fA-F0-9]{{48}}{re.escape(end)}\b'
            context_matches = re.findall(context_pattern, content, re.IGNORECASE)
            for full_key in context_matches:
                private_keys.add(full_key.lower())
        
        # Pattern 3: WIF format keys (Bitcoin)
        wif_pattern = r'\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b'
        wif_matches = re.findall(wif_pattern, content)
        for wif_key in wif_matches:
            private_keys.add(wif_key)
        
        # Pattern 4: Ethereum private keys (0x prefix or not)
        eth_pattern = r'\b(?:0x)?[a-fA-F0-9]{64}\b'
        eth_matches = re.findall(eth_pattern, content)
        for eth_key in eth_matches:
            if len(eth_key) == 64 or (len(eth_key) == 66 and eth_key.startswith('0x')):
                clean_key = eth_key.replace('0x', '').lower()
                if clean_key != '0' * 64:
                    private_keys.add(clean_key)
        
        # Extract addresses too
        address_patterns = [
            r'\b1[A-Za-z0-9]{25,34}\b',  # Bitcoin Legacy
            r'\b3[A-Za-z0-9]{25,34}\b',  # Bitcoin SegWit
            r'\bbc1[a-z0-9]{39,59}\b',   # Bitcoin Bech32
            r'\b0x[a-fA-F0-9]{40}\b',    # Ethereum
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, content)
            for address in matches:
                addresses.add(address)
    
    except FileNotFoundError:
        print(f"❌ {filename} not found")
        return [], []
    
    valid_keys = list(private_keys)
    valid_addresses = list(addresses)
    
    print(f"✅ Found {len(valid_keys)} unique private keys")
    print(f"✅ Found {len(valid_addresses)} unique addresses")
    
    return valid_keys, valid_addresses

def main():
    print("🚀 EXTRACTING PRIVATE KEYS FROM NET602 AND NET605")
    print("="*60)
    
    # Extract from net602
    keys_602, addr_602 = extract_hex_private_keys('net602_scan_results.txt')
    
    # Extract from net605
    keys_605, addr_605 = extract_hex_private_keys('net605_scan_results.txt')
    
    # Save net602 data
    if keys_602:
        keys_data_602 = {
            "source": "net602",
            "extraction_date": "2025-08-12",
            "total_keys_found": len(keys_602),
            "total_addresses_found": len(addr_602),
            "private_keys": keys_602[:500],  # First 500 for initial check
            "addresses": addr_602[:100]
        }
        
        with open('net602_extracted_keys.json', 'w') as f:
            json.dump(keys_data_602, f, indent=2)
        
        print(f"\n📋 NET602 - FIRST 10 PRIVATE KEYS:")
        for i, key in enumerate(keys_602[:10], 1):
            print(f"{i:2d}. {key}")
    
    # Save net605 data
    if keys_605:
        keys_data_605 = {
            "source": "net605",
            "extraction_date": "2025-08-12",
            "total_keys_found": len(keys_605),
            "total_addresses_found": len(addr_605),
            "private_keys": keys_605[:500],  # First 500 for initial check
            "addresses": addr_605[:100]
        }
        
        with open('net605_extracted_keys.json', 'w') as f:
            json.dump(keys_data_605, f, indent=2)
        
        print(f"\n📋 NET605 - FIRST 10 PRIVATE KEYS:")
        for i, key in enumerate(keys_605[:10], 1):
            print(f"{i:2d}. {key}")
    
    total_keys = len(keys_602) + len(keys_605)
    total_addresses = len(addr_602) + len(addr_605)
    
    print(f"\n📊 EXTRACTION SUMMARY:")
    print(f"   NET602: {len(keys_602)} keys, {len(addr_602)} addresses")
    print(f"   NET605: {len(keys_605)} keys, {len(addr_605)} addresses")
    print(f"   TOTAL: {total_keys} keys, {total_addresses} addresses")
    
    if total_keys > 0:
        print("\n✅ Ready for batch balance checking!")
    else:
        print("\n❌ No private keys extracted - check scan results format")

if __name__ == "__main__":
    main()
