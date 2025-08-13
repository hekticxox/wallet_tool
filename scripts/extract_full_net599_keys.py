#!/usr/bin/env python3

import re
import json
from collections import defaultdict

def extract_full_private_keys():
    """Extract full private keys from net599 scan results"""
    
    private_keys = set()
    key_data = []
    
    print("🔍 Extracting full private keys from net599 scan...")
    
    try:
        with open('net599_scan_results.txt', 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        current_file = ""
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Track current file being scanned
            if "🎯" in line and ".json" in line:
                current_file = line
            
            # Look for private key lines
            if "🔑 PRIVATE KEY:" in line:
                # Extract the truncated key display
                key_match = re.search(r'PRIVATE KEY: ([a-fA-F0-9]+)\.\.\.([a-fA-F0-9]+)', line)
                if key_match:
                    key_start = key_match.group(1)
                    key_end = key_match.group(2)
                    
                    # Look for the full key in surrounding context
                    # Check previous and next few lines for full hex strings
                    search_range = max(0, i-5), min(len(lines), i+5)
                    
                    for j in range(search_range[0], search_range[1]):
                        context_line = lines[j].strip()
                        
                        # Look for 64-character hex strings (Ethereum private keys)
                        full_key_matches = re.findall(r'\b([a-fA-F0-9]{64})\b', context_line)
                        
                        for full_key in full_key_matches:
                            # Check if this matches our truncated key
                            if (full_key.lower().startswith(key_start.lower()) and 
                                full_key.lower().endswith(key_end.lower())):
                                
                                # Validate it's not all zeros or ones
                                if (not all(c == '0' for c in full_key) and
                                    not all(c == 'f' for c in full_key.lower()) and
                                    not all(c == '1' for c in full_key)):
                                    
                                    private_keys.add(full_key.lower())
                                    key_data.append({
                                        'key': full_key.lower(),
                                        'source_file': current_file,
                                        'type': 'ethereum'
                                    })
        
        print(f"✅ Extracted {len(private_keys)} unique private keys")
        
        if private_keys:
            # Save keys
            with open('net599_extracted_keys.txt', 'w') as f:
                for key in sorted(private_keys):
                    f.write(f"{key}\n")
            
            # Save detailed data
            with open('net599_key_data.json', 'w') as f:
                json.dump(key_data, f, indent=2)
            
            print(f"💾 Keys saved to net599_extracted_keys.txt")
            print(f"💾 Detailed data saved to net599_key_data.json")
            
            # Show first 10 keys
            print("\nFirst 10 private keys:")
            for i, key in enumerate(sorted(private_keys)[:10], 1):
                print(f"{i:2d}. {key}")
        
        return list(private_keys)
        
    except Exception as e:
        print(f"❌ Error extracting keys: {e}")
        return []

if __name__ == "__main__":
    keys = extract_full_private_keys()
    
    if keys:
        print(f"\n🎯 SUCCESS: Extracted {len(keys)} private keys from net599!")
        print("🚀 Ready to check balances for these keys!")
    else:
        print("\n❌ Could not extract full private keys")
