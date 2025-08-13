#!/usr/bin/env python3

import json
import re
import os

def extract_net602_keys():
    """Extract private keys from net602 scan results"""
    
    print("🔍 EXTRACTING NET602 PRIVATE KEYS...")
    
    private_keys = set()
    current_key = None
    
    # Read scan results
    try:
        with open('net602_scan_results.txt', 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Look for private key indicators
                if "PRIVATE KEY FOUND" in line:
                    # Extract from line like "🔑 PRIVATE KEY FOUND: L1234..."
                    key_match = re.search(r'PRIVATE KEY FOUND:\s*([A-Za-z0-9]{51,52})', line)
                    if key_match:
                        private_keys.add(key_match.group(1))
                        current_key = key_match.group(1)
                
                # Look for numbered private keys
                elif re.match(r'^\d+\.\s+([A-Za-z0-9]{51,52})', line):
                    key_match = re.match(r'^\d+\.\s+([A-Za-z0-9]{51,52})', line)
                    if key_match:
                        private_keys.add(key_match.group(1))
                        current_key = key_match.group(1)
                
                # Look for standalone keys (51-52 chars, alphanumeric)
                elif len(line) >= 51 and len(line) <= 52 and line.isalnum():
                    if line.startswith(('L', 'K', '5')):  # Common Bitcoin private key prefixes
                        private_keys.add(line)
                        current_key = line
                
                # Context-based extraction
                elif current_key and ("Ethereum" in line or "Bitcoin" in line):
                    continue
                else:
                    current_key = None
    
    except FileNotFoundError:
        print("❌ net602_scan_results.txt not found")
        return []
    
    # Convert to list and validate
    valid_keys = []
    for key in private_keys:
        if len(key) >= 51 and len(key) <= 52 and key.isalnum():
            valid_keys.append(key)
    
    print(f"✅ Found {len(valid_keys)} unique private keys in net602")
    
    # Save keys
    keys_data = {
        "source": "net602",
        "extraction_date": "2025-08-12",
        "total_keys_found": len(valid_keys),
        "private_keys": valid_keys[:1000]  # Limit for initial check
    }
    
    with open('net602_extracted_keys.json', 'w') as f:
        json.dump(keys_data, f, indent=2)
    
    # Show sample
    print("\n📋 FIRST 10 KEYS:")
    for i, key in enumerate(valid_keys[:10], 1):
        print(f"{i:2d}. {key}")
    
    if len(valid_keys) > 10:
        print(f"    ... and {len(valid_keys) - 10} more")
    
    print(f"\n💾 Saved to: net602_extracted_keys.json")
    return valid_keys

def extract_net605_keys():
    """Extract private keys from net605 scan results"""
    
    print("\n🔍 EXTRACTING NET605 PRIVATE KEYS...")
    
    private_keys = set()
    current_key = None
    
    # Read scan results
    try:
        with open('net605_scan_results.txt', 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Look for private key indicators
                if "PRIVATE KEY FOUND" in line:
                    # Extract from line like "🔑 PRIVATE KEY FOUND: L1234..."
                    key_match = re.search(r'PRIVATE KEY FOUND:\s*([A-Za-z0-9]{51,52})', line)
                    if key_match:
                        private_keys.add(key_match.group(1))
                        current_key = key_match.group(1)
                
                # Look for numbered private keys
                elif re.match(r'^\d+\.\s+([A-Za-z0-9]{51,52})', line):
                    key_match = re.match(r'^\d+\.\s+([A-Za-z0-9]{51,52})', line)
                    if key_match:
                        private_keys.add(key_match.group(1))
                        current_key = key_match.group(1)
                
                # Look for standalone keys (51-52 chars, alphanumeric)
                elif len(line) >= 51 and len(line) <= 52 and line.isalnum():
                    if line.startswith(('L', 'K', '5')):  # Common Bitcoin private key prefixes
                        private_keys.add(line)
                        current_key = line
                
                # Context-based extraction
                elif current_key and ("Ethereum" in line or "Bitcoin" in line):
                    continue
                else:
                    current_key = None
    
    except FileNotFoundError:
        print("❌ net605_scan_results.txt not found")
        return []
    
    # Convert to list and validate
    valid_keys = []
    for key in private_keys:
        if len(key) >= 51 and len(key) <= 52 and key.isalnum():
            valid_keys.append(key)
    
    print(f"✅ Found {len(valid_keys)} unique private keys in net605")
    
    # Save keys
    keys_data = {
        "source": "net605",
        "extraction_date": "2025-08-12",
        "total_keys_found": len(valid_keys),
        "private_keys": valid_keys[:1000]  # Limit for initial check
    }
    
    with open('net605_extracted_keys.json', 'w') as f:
        json.dump(keys_data, f, indent=2)
    
    # Show sample
    print("\n📋 FIRST 10 KEYS:")
    for i, key in enumerate(valid_keys[:10], 1):
        print(f"{i:2d}. {key}")
    
    if len(valid_keys) > 10:
        print(f"    ... and {len(valid_keys) - 10} more")
    
    print(f"\n💾 Saved to: net605_extracted_keys.json")
    return valid_keys

if __name__ == "__main__":
    print("🚀 EXTRACTING PRIVATE KEYS FROM NET602 AND NET605")
    print("="*60)
    
    keys_602 = extract_net602_keys()
    keys_605 = extract_net605_keys()
    
    total_keys = len(keys_602) + len(keys_605)
    
    print(f"\n📊 EXTRACTION SUMMARY:")
    print(f"   NET602: {len(keys_602)} keys")
    print(f"   NET605: {len(keys_605)} keys")
    print(f"   TOTAL: {total_keys} keys ready for balance checking")
    print("\n✅ Ready for batch balance checking!")
