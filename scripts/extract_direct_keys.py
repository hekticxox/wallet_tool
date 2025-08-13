#!/usr/bin/env python3

import json
import re
import os
import glob
from pathlib import Path

def extract_keys_from_files(base_path):
    """Extract private keys from actual source files"""
    
    print(f"🔍 SCANNING FILES IN {base_path}...")
    
    private_keys = set()
    addresses = set()
    
    # Common wallet file patterns
    wallet_patterns = [
        "**/*Cookies*.txt",
        "**/*History*.txt", 
        "**/*Autofills*.txt",
        "**/*Password*.txt",
        "**/*Bookmarks*.txt",
        "**/wallet.dat",
        "**/default_wallet",
        "**/*.json",
        "**/*.log"
    ]
    
    files_scanned = 0
    keys_found_per_file = {}
    
    for pattern in wallet_patterns:
        pattern_path = os.path.join(base_path, pattern)
        files = glob.glob(pattern_path, recursive=True)
        
        for file_path in files:
            try:
                if os.path.getsize(file_path) > 50 * 1024 * 1024:  # Skip files > 50MB
                    continue
                    
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                files_scanned += 1
                file_keys = 0
                
                # Extract 64-character hex keys (most common private key format)
                hex_keys = re.findall(r'\b[a-fA-F0-9]{64}\b', content)
                for key in hex_keys:
                    # Basic validation - not all zeros or all same character
                    if key != '0' * 64 and not all(c == key[0] for c in key) and len(set(key)) > 4:
                        private_keys.add(key.lower())
                        file_keys += 1
                
                # Extract Bitcoin WIF keys
                wif_keys = re.findall(r'\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b', content)
                for key in wif_keys:
                    private_keys.add(key)
                    file_keys += 1
                
                # Extract Ethereum format (0x prefix)
                eth_keys = re.findall(r'\b0x[a-fA-F0-9]{64}\b', content)
                for key in eth_keys:
                    clean_key = key[2:].lower()  # Remove 0x prefix
                    if len(set(clean_key)) > 4:
                        private_keys.add(clean_key)
                        file_keys += 1
                
                # Extract addresses
                addr_patterns = [
                    r'\b1[A-Za-z0-9]{25,34}\b',    # Bitcoin Legacy
                    r'\b3[A-Za-z0-9]{25,34}\b',    # Bitcoin SegWit
                    r'\bbc1[a-z0-9]{39,59}\b',     # Bitcoin Bech32
                    r'\b0x[a-fA-F0-9]{40}\b',      # Ethereum
                ]
                
                for pattern in addr_patterns:
                    matches = re.findall(pattern, content)
                    for address in matches:
                        addresses.add(address)
                
                if file_keys > 0:
                    keys_found_per_file[file_path] = file_keys
                    print(f"   📄 {os.path.basename(file_path)}: {file_keys} keys")
                
            except Exception as e:
                continue
    
    print(f"✅ Scanned {files_scanned} files")
    print(f"✅ Found {len(private_keys)} unique private keys")
    print(f"✅ Found {len(addresses)} unique addresses")
    
    return list(private_keys), list(addresses), keys_found_per_file

def main():
    print("🚀 EXTRACTING PRIVATE KEYS FROM SOURCE FILES")
    print("="*60)
    
    # Extract from net602
    print("\n🔍 PROCESSING NET602...")
    keys_602, addr_602, files_602 = extract_keys_from_files('/home/admin/Downloads/net602')
    
    # Extract from net605 
    print("\n🔍 PROCESSING NET605...")
    keys_605, addr_605, files_605 = extract_keys_from_files('/home/admin/Downloads/net605')
    
    # Save net602 data
    if keys_602:
        keys_data_602 = {
            "source": "net602_direct",
            "extraction_date": "2025-08-12",
            "total_keys_found": len(keys_602),
            "total_addresses_found": len(addr_602),
            "private_keys": keys_602[:1000],  # First 1000 for checking
            "addresses": addr_602[:500],
            "source_files": files_602
        }
        
        with open('net602_direct_keys.json', 'w') as f:
            json.dump(keys_data_602, f, indent=2)
        
        print(f"\n📋 NET602 - FIRST 10 PRIVATE KEYS:")
        for i, key in enumerate(keys_602[:10], 1):
            print(f"{i:2d}. {key}")
        
        print(f"\n💾 Saved to: net602_direct_keys.json")
    
    # Save net605 data
    if keys_605:
        keys_data_605 = {
            "source": "net605_direct",
            "extraction_date": "2025-08-12",
            "total_keys_found": len(keys_605),
            "total_addresses_found": len(addr_605),
            "private_keys": keys_605[:1000],  # First 1000 for checking
            "addresses": addr_605[:500],
            "source_files": files_605
        }
        
        with open('net605_direct_keys.json', 'w') as f:
            json.dump(keys_data_605, f, indent=2)
        
        print(f"\n📋 NET605 - FIRST 10 PRIVATE KEYS:")
        for i, key in enumerate(keys_605[:10], 1):
            print(f"{i:2d}. {key}")
        
        print(f"\n💾 Saved to: net605_direct_keys.json")
    
    total_keys = len(keys_602) + len(keys_605)
    total_addresses = len(addr_602) + len(addr_605)
    
    print(f"\n📊 FINAL EXTRACTION SUMMARY:")
    print(f"   NET602: {len(keys_602)} keys, {len(addr_602)} addresses")
    print(f"   NET605: {len(keys_605)} keys, {len(addr_605)} addresses")  
    print(f"   TOTAL: {total_keys} keys, {total_addresses} addresses")
    
    if total_keys > 0:
        print(f"\n🎯 NEXT STEP: Run batch balance checker on {total_keys} keys!")
        print("   Command: python batch_balance_checker.py")
    else:
        print("\n❌ No private keys extracted")

if __name__ == "__main__":
    main()
