#!/usr/bin/env python3
"""
Extract and Test ZelCore Private Keys (Simple Version)
Extracts potential private keys from ZelCore balances file
"""

import os
import sys
import json
import hashlib
import re

def extract_zelcore_keys(file_path, output_file):
    """Extract potential private keys from ZelCore file"""
    print(f"Extracting keys from: {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read().strip()
    
    # Convert hex to bytes and back to ensure clean hex
    try:
        hex_data = bytes.fromhex(content)
        clean_hex = hex_data.hex()
    except ValueError:
        print("Invalid hex data")
        return []
    
    # Extract all 64-character hex strings
    potential_keys = []
    hex_str = clean_hex.lower()
    
    for i in range(0, len(hex_str), 64):
        chunk = hex_str[i:i+64]
        if len(chunk) == 64:
            # Check if it's a valid private key (not all zeros, not all fs)
            if not all(c == '0' for c in chunk) and not all(c == 'f' for c in chunk):
                # Additional validation: should be a valid hex number
                try:
                    int(chunk, 16)
                    potential_keys.append(chunk)
                except ValueError:
                    continue
    
    # Remove duplicates while preserving order
    unique_keys = []
    seen = set()
    for key in potential_keys:
        if key not in seen:
            unique_keys.append(key)
            seen.add(key)
    
    print(f"Extracted {len(unique_keys)} unique potential private keys")
    
    # Save to file
    with open(output_file, 'w') as f:
        json.dump(unique_keys, f, indent=2)
    
    return unique_keys

def analyze_keys(keys_list):
    """Analyze extracted keys for patterns"""
    print(f"\nAnalyzing {len(keys_list)} keys...")
    
    # Check for patterns
    patterns = {}
    
    for key in keys_list:
        # Check first few characters for patterns
        prefix = key[:8]
        if prefix not in patterns:
            patterns[prefix] = 0
        patterns[prefix] += 1
    
    # Show most common prefixes
    sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
    print("\nMost common 8-character prefixes:")
    for prefix, count in sorted_patterns[:10]:
        print(f"  {prefix}: {count} keys")
    
    # Check for sequential patterns
    sequential = 0
    for i in range(1, min(50, len(keys_list))):
        key1 = int(keys_list[i-1], 16)
        key2 = int(keys_list[i], 16)
        if abs(key2 - key1) == 1:
            sequential += 1
    
    print(f"\nSequential keys found: {sequential}")
    
    # Validate keys are in valid range for secp256k1
    secp256k1_n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
    valid_range = 0
    
    for key in keys_list[:100]:  # Check first 100
        key_int = int(key, 16)
        if 1 <= key_int < secp256k1_n:
            valid_range += 1
    
    print(f"Keys in valid secp256k1 range (first 100): {valid_range}/100")

def create_balance_check_file(keys_list, output_file, max_keys=100):
    """Create a file with keys for balance checking"""
    print(f"\nCreating balance check file with up to {max_keys} keys...")
    
    # Take a diverse sample
    sample_keys = []
    if len(keys_list) <= max_keys:
        sample_keys = keys_list
    else:
        # Take keys from different positions
        step = len(keys_list) // max_keys
        for i in range(0, len(keys_list), step):
            if len(sample_keys) < max_keys:
                sample_keys.append(keys_list[i])
    
    # Create addresses for balance checking
    balance_check_data = []
    for i, key in enumerate(sample_keys):
        balance_check_data.append({
            'index': i,
            'private_key': key,
            'note': f'ZelCore extracted key {i+1}'
        })
    
    with open(output_file, 'w') as f:
        json.dump(balance_check_data, f, indent=2)
    
    print(f"Created balance check file: {output_file}")
    print(f"Contains {len(sample_keys)} keys ready for balance checking")
    
    return balance_check_data

def main():
    zelcore_file = "/home/admin/Downloads/net599/[AR]39.4.38.112/Important Files/Profile/ZelCore/balances_SeedPhrase-1747047018275"
    output_file = "/home/admin/wallet_tool/zelcore_extracted_keys.json"
    balance_check_file = "/home/admin/wallet_tool/zelcore_balance_check.json"
    
    # Extract keys
    keys_list = extract_zelcore_keys(zelcore_file, output_file)
    
    if not keys_list:
        print("No keys extracted")
        return
    
    print(f"\nFirst 10 extracted keys:")
    for i, key in enumerate(keys_list[:10]):
        print(f"{i+1}: {key}")
    
    # Analyze keys
    analyze_keys(keys_list)
    
    # Create balance check file
    balance_check_data = create_balance_check_file(keys_list, balance_check_file, max_keys=50)
    
    print(f"\n" + "="*60)
    print("ZELCORE EXTRACTION COMPLETE")
    print("="*60)
    print(f"Total keys extracted: {len(keys_list)}")
    print(f"All keys saved to: {output_file}")
    print(f"Balance check file: {balance_check_file}")
    print("\nNext steps:")
    print("1. Run batch balance checker on the balance check file")
    print("2. If any funded keys found, investigate further")

if __name__ == "__main__":
    main()
