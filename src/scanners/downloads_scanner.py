#!/usr/bin/env python3
"""
Downloads Directory Private Key Scanner
Simple scanner without complex dependencies
"""

import os
import re
import json
from pathlib import Path
from eth_keys import keys

# Our high-value target addresses
TARGET_ADDRESSES = {
    "0x8390a1da07e376ef7add4be859ba74fb83aa02d5": 11.056515758510199353,
    "0x6e59e2a98d12f45ab5872942fe45a1036b1ea9c9": 0.296807,
    "0x2859e4544c4bb03966803b044a93563bd2d0dd4d": 4.005814613262247463,
    "0xba2ae424d960c26247dd6c32edc70b295c744c43": 4.516350432918525173,
    "0xf03f0a004ab150bf46d8e2df10b7ebd89ed39f0e": 1.022336283937304673,
    "0xa462bde22d98335e18a21555b6752db93a937cff": 0.801890924956108765,
    "0x683a4ac99e65200921f556a19dadf4b0214b5938": 0.759441365469564,
    "0x159cdaf78be31e730d9e1330adfcfbb79a5fdb95": 0.541373,
    "0xf7b5fb4607abfe0ecf332c23cbdcc9e425b443a8": 0.508588278302716771,
}

def ethereum_address_from_private_key(private_key_hex):
    """Convert private key to Ethereum address"""
    try:
        if private_key_hex.startswith('0x'):
            private_key_hex = private_key_hex[2:]
        
        if len(private_key_hex) != 64:
            return None
            
        private_key_bytes = bytes.fromhex(private_key_hex)
        private_key = keys.PrivateKey(private_key_bytes)
        return private_key.public_key.to_checksum_address().lower()
        
    except Exception:
        return None

def extract_hex_patterns(content):
    """Extract potential private key patterns"""
    patterns = set()
    
    # 64-character hex strings
    hex_64 = re.findall(r'\b[a-fA-F0-9]{64}\b', content)
    patterns.update(hex_64)
    
    # 0x prefixed hex
    hex_0x = re.findall(r'\b0x[a-fA-F0-9]{64}\b', content)
    patterns.update([h[2:] for h in hex_0x])
    
    # Also try nearby our target addresses
    for target_addr in TARGET_ADDRESSES.keys():
        # Find address in content
        addr_pos = content.lower().find(target_addr.lower())
        if addr_pos != -1:
            # Extract 1000 characters before and after
            start = max(0, addr_pos - 1000)
            end = min(len(content), addr_pos + 1000)
            context = content[start:end]
            
            # Look for hex patterns in this context
            context_hex = re.findall(r'\b[a-fA-F0-9]{64}\b', context)
            patterns.update(context_hex)
    
    return patterns

def scan_file(file_path):
    """Scan a single file for private keys"""
    results = []
    
    try:
        # Skip very large files
        if file_path.stat().st_size > 50 * 1024 * 1024:  # 50MB limit
            return results
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Extract potential private keys
        hex_patterns = extract_hex_patterns(content)
        
        print(f"   📄 {file_path.name}: Found {len(hex_patterns)} hex patterns")
        
        # Test each pattern
        for hex_pattern in hex_patterns:
            try:
                address = ethereum_address_from_private_key(hex_pattern)
                if address and address in TARGET_ADDRESSES:
                    balance = TARGET_ADDRESSES[address]
                    result = {
                        'file': str(file_path),
                        'address': address,
                        'private_key': hex_pattern,
                        'balance': balance
                    }
                    results.append(result)
                    
                    print(f"\n🎉 PRIVATE KEY FOUND!")
                    print(f"   File: {file_path}")
                    print(f"   Address: {address}")
                    print(f"   Balance: {balance:.6f} ETH")
                    print(f"   Private Key: {hex_pattern}")
                    
            except Exception:
                continue
                
    except Exception as e:
        print(f"   ❌ Error reading {file_path}: {e}")
    
    return results

def scan_downloads():
    """Scan Downloads directory for private keys"""
    
    downloads_dir = Path("/home/admin/Downloads")
    
    print("🔍 DOWNLOADS DIRECTORY PRIVATE KEY SCANNER")
    print("="*70)
    print(f"🎯 Searching for keys to {len(TARGET_ADDRESSES)} target addresses")
    
    total_value = sum(TARGET_ADDRESSES.values())
    print(f"💰 Total potential recovery: {total_value:.6f} ETH (~${total_value * 2500:.0f})")
    
    print(f"\n📁 Scanning: {downloads_dir}")
    
    # Find all text-based files
    searchable_files = []
    
    for root, dirs, files in os.walk(downloads_dir):
        # Skip some directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            file_path = Path(root) / file
            
            # Include text files and files with wallet-related names
            if (file_path.suffix.lower() in {'.txt', '.json', '.csv', '.log', '.dat'} or
                'wallet' in file.lower() or
                'key' in file.lower() or
                'autofill' in file.lower() or
                'cookie' in file.lower() or
                'password' in file.lower()):
                searchable_files.append(file_path)
    
    print(f"📄 Found {len(searchable_files)} searchable files")
    
    if not searchable_files:
        print("❌ No searchable files found")
        return []
    
    # Scan files
    all_results = []
    
    for i, file_path in enumerate(searchable_files):
        print(f"\n📍 Scanning {i+1}/{len(searchable_files)}: {file_path.name}")
        
        results = scan_file(file_path)
        all_results.extend(results)
        
        if i % 50 == 0 and i > 0:
            print(f"   Progress: {i}/{len(searchable_files)} files ({i/len(searchable_files)*100:.1f}%)")
    
    print(f"\n📊 SCAN COMPLETE")
    print(f"   Files scanned: {len(searchable_files)}")
    print(f"   Private keys found: {len(all_results)}")
    
    if all_results:
        total_recovered = sum(result['balance'] for result in all_results)
        print(f"💰 Total recoverable: {total_recovered:.6f} ETH (~${total_recovered * 2500:.0f})")
        
        # Save results
        with open('DOWNLOADS_RECOVERY_RESULTS.json', 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"💾 Results saved to: DOWNLOADS_RECOVERY_RESULTS.json")
        
        for result in all_results:
            print(f"\n🔑 Found:")
            print(f"   Address: {result['address']}")
            print(f"   Balance: {result['balance']:.6f} ETH")
            print(f"   File: {result['file']}")
    else:
        print(f"❌ No private keys found for target addresses")
        print(f"💡 Files contained wallet data but no matching private keys")
    
    return all_results

if __name__ == "__main__":
    results = scan_downloads()
