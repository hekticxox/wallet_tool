#!/usr/bin/env python3
"""
Quick Net501 Private Key Sample Extractor
Gets a sample of the most promising private keys for balance checking
"""

import json
import re
from datetime import datetime
import os
import random

def extract_sample_keys():
    """Extract a manageable sample of private keys"""
    
    print("Finding wallet files in net501...")
    
    # Look for specific wallet-related files
    wallet_files = []
    net501_path = "/home/admin/Downloads/net501"
    
    # Find files that are likely to contain actual wallet data
    for root, dirs, files in os.walk(net501_path):
        for file in files:
            file_lower = file.lower()
            if any(keyword in file_lower for keyword in [
                'wallet', 'keystore', 'private', 'seed', 'mnemonic',
                'bitcoin', 'ethereum', 'crypto', 'keys'
            ]):
                wallet_files.append(os.path.join(root, file))
    
    print(f"Found {len(wallet_files)} potential wallet files")
    
    # Also sample some browser files
    browser_files = []
    for root, dirs, files in os.walk(net501_path):
        for file in files:
            if file.lower() in ['history.txt', 'cookies.txt', 'passwords.txt']:
                browser_files.append(os.path.join(root, file))
    
    # Sample 50 random browser files
    sampled_browser = random.sample(browser_files, min(50, len(browser_files)))
    
    all_files = wallet_files + sampled_browser
    print(f"Processing {len(all_files)} files...")
    
    private_keys = set()
    
    for i, file_path in enumerate(all_files):
        if i % 10 == 0:
            print(f"Processing file {i+1}/{len(all_files)}: {os.path.basename(file_path)}")
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Look for 64-character hex strings
            hex_keys = re.findall(r'\b[0-9a-fA-F]{64}\b', content)
            for key in hex_keys:
                if len(key) == 64:
                    # Basic validation - ensure it's not all zeros or obvious non-key
                    if not (key.count('0') > 50 or key.count('f') > 50 or key.count('F') > 50):
                        private_keys.add(key.lower())
                        
                        # Stop after finding 1000 keys to keep it manageable
                        if len(private_keys) >= 1000:
                            break
            
            if len(private_keys) >= 1000:
                break
                
        except Exception as e:
            continue
    
    unique_keys = list(private_keys)
    
    print(f"\nFound {len(unique_keys)} unique private keys")
    
    # Save to file
    with open('/home/admin/wallet_tool/net501_sample_keys.txt', 'w') as f:
        for key in unique_keys:
            f.write(key + '\n')
    
    print(f"Saved to: /home/admin/wallet_tool/net501_sample_keys.txt")
    
    # Show sample
    print(f"\nFirst 10 keys (sample):")
    for i, key in enumerate(unique_keys[:10]):
        print(f"{i+1}: {key}")
    
    return unique_keys

def main():
    print("="*60)
    print("NET501 SAMPLE PRIVATE KEY EXTRACTOR")
    print("="*60)
    
    keys = extract_sample_keys()
    
    print(f"\n✅ Extraction complete! Found {len(keys)} sample private keys from net501")

if __name__ == "__main__":
    main()
