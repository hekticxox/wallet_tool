#!/usr/bin/env python3
"""
Extract and Test ZelCore Private Keys
Extracts potential private keys from ZelCore balances file and tests them
"""

import os
import sys
import binascii
import json
import time
from eth_keys import keys
from bit import PrivateKey

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
                potential_keys.append(chunk)
    
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

def validate_and_test_keys(keys_list, max_test=50):
    """Validate keys and test first batch for balances"""
    print(f"Validating and testing up to {max_test} keys...")
    
    valid_keys = []
    
    for i, key_hex in enumerate(keys_list[:max_test]):
        try:
            # Test as Bitcoin private key
            btc_key = PrivateKey(key_hex)
            btc_address = btc_key.address
            
            # Test as Ethereum private key
            eth_key = keys.PrivateKey(bytes.fromhex(key_hex))
            eth_address = eth_key.public_key.to_checksum_address()
            
            valid_keys.append({
                'private_key': key_hex,
                'bitcoin_address': btc_address,
                'ethereum_address': eth_address,
                'index': i
            })
            
            print(f"Valid key {i+1}: BTC: {btc_address}, ETH: {eth_address}")
            
        except Exception as e:
            print(f"Invalid key {i+1}: {key_hex[:16]}... - {str(e)}")
    
    print(f"Found {len(valid_keys)} valid keys out of {min(max_test, len(keys_list))} tested")
    return valid_keys

def main():
    zelcore_file = "/home/admin/Downloads/net599/[AR]39.4.38.112/Important Files/Profile/ZelCore/balances_SeedPhrase-1747047018275"
    output_file = "/home/admin/wallet_tool/zelcore_extracted_keys.json"
    
    # Extract keys
    keys_list = extract_zelcore_keys(zelcore_file, output_file)
    
    if not keys_list:
        print("No keys extracted")
        return
    
    print(f"\nFirst 10 extracted keys:")
    for i, key in enumerate(keys_list[:10]):
        print(f"{i+1}: {key}")
    
    # Validate and test a sample
    print(f"\nValidating sample of keys...")
    valid_keys = validate_and_test_keys(keys_list, max_test=20)
    
    # Save valid keys
    if valid_keys:
        valid_keys_file = "/home/admin/wallet_tool/zelcore_valid_keys.json"
        with open(valid_keys_file, 'w') as f:
            json.dump(valid_keys, f, indent=2)
        print(f"\nSaved {len(valid_keys)} valid keys to: {valid_keys_file}")
    
    print(f"\nTotal keys extracted: {len(keys_list)}")
    print(f"Keys file saved to: {output_file}")

if __name__ == "__main__":
    main()
