#!/usr/bin/env python3
"""
Extract Private Keys from Net501 Dataset
Processes the massive 112k+ address dataset to find actual private keys
"""

import json
import re
from datetime import datetime

def extract_private_keys_from_net501():
    """Extract private keys from the comprehensive scan results"""
    
    print("Loading comprehensive scan results...")
    
    with open('/home/admin/wallet_tool/comprehensive_scan_results.json', 'r') as f:
        scan_data = json.load(f)
    
    print(f"Scan found {scan_data['scan_summary']['private_keys_found']} private keys")
    print(f"Scan found {scan_data['scan_summary']['addresses_found']} total addresses")
    
    # Extract private keys (not just addresses derived from keys)
    private_keys = set()
    
    # Look for actual private key patterns in scan data
    for key_data in scan_data.get('private_keys_found', []):
        # Extract full key from the file if available
        file_path = key_data.get('file_path', '')
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Find 64-character hex strings
                hex_keys = re.findall(r'[0-9a-fA-F]{64}', content)
                for key in hex_keys:
                    # Basic validation
                    if len(key) == 64 and all(c in '0123456789abcdefABCDEF' for c in key):
                        private_keys.add(key.lower())
                
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    # Also search for standalone private key patterns in the content
    if 'raw_content' in scan_data:
        content = scan_data['raw_content']
        hex_keys = re.findall(r'[0-9a-fA-F]{64}', content)
        for key in hex_keys:
            if len(key) == 64:
                private_keys.add(key.lower())
    
    unique_keys = list(private_keys)
    
    print(f"Found {len(unique_keys)} unique private keys")
    
    # Save to file
    with open('/home/admin/wallet_tool/net501_private_keys.txt', 'w') as f:
        for key in unique_keys:
            f.write(key + '\n')
    
    print(f"Saved to: /home/admin/wallet_tool/net501_private_keys.txt")
    
    # Show sample
    print(f"\nFirst 10 private keys (sample):")
    for i, key in enumerate(unique_keys[:10]):
        print(f"{i+1}: {key}")
    
    return unique_keys

def main():
    print("="*60)
    print("NET501 PRIVATE KEY EXTRACTOR")
    print("="*60)
    
    keys = extract_private_keys_from_net501()
    
    print(f"\n✅ Extraction complete! Found {len(keys)} private keys from net501 dataset")

if __name__ == "__main__":
    main()
