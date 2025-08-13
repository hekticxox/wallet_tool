#!/usr/bin/env python3
"""
Extract Private Keys from Comprehensive Scan Results
"""

import json
import re
from pathlib import Path

def extract_private_keys_from_file(file_path):
    """Extract full 64-character hex strings from a file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Find all 64-character hex strings
        pattern = r'[0-9a-fA-F]{64}'
        matches = re.findall(pattern, content)
        
        # Filter out obvious non-private keys (cookies, trackers, etc.)
        filtered_keys = []
        for key in matches:
            key_lower = key.lower()
            # Skip if it looks like a cookie ID, tracker, or analytics token
            if not any(marker in key_lower for marker in [
                'fbclid', 'utm_', 'gtm', 'ga_', '_ga', 'gclid', 
                'dclid', 'wbraid', 'gbraid', 'msclkid'
            ]):
                filtered_keys.append(key)
        
        return filtered_keys
    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def main():
    """Extract private keys from scan results"""
    
    # Load scan results
    with open('/home/admin/wallet_tool/comprehensive_scan_results.json', 'r') as f:
        scan_data = json.load(f)
    
    all_keys = set()
    files_to_check = []
    
    # Get unique files from scan results
    for key_data in scan_data['private_keys_found']:
        files_to_check.append(key_data['file_path'])
    
    files_to_check = list(set(files_to_check))
    
    print(f"Extracting private keys from {len(files_to_check)} files...")
    
    for file_path in files_to_check:
        print(f"Processing: {file_path}")
        keys_from_file = extract_private_keys_from_file(file_path)
        all_keys.update(keys_from_file)
        print(f"  Found {len(keys_from_file)} potential keys")
    
    # Convert to list and validate
    unique_keys = []
    for key in all_keys:
        # Basic validation: must be exactly 64 hex characters
        if len(key) == 64 and all(c in '0123456789abcdefABCDEF' for c in key):
            unique_keys.append(key.lower())  # Normalize to lowercase
    
    unique_keys = list(set(unique_keys))  # Remove duplicates
    
    print(f"\nFound {len(unique_keys)} unique valid private keys")
    
    # Save to file
    with open('/home/admin/wallet_tool/extracted_keys_172_58_122_84.txt', 'w') as f:
        for key in unique_keys:
            f.write(key + '\n')
    
    print(f"Saved to: /home/admin/wallet_tool/extracted_keys_172_58_122_84.txt")
    
    # Show first 10 keys as sample
    print(f"\nFirst 10 keys (sample):")
    for i, key in enumerate(unique_keys[:10]):
        print(f"{i+1}: {key}")

if __name__ == "__main__":
    main()
