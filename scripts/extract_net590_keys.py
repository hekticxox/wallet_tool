#!/usr/bin/env python3

import re
import json
from collections import defaultdict

def extract_net590_keys():
    """Extract private keys from net590 scan results"""
    
    print("🔍 Extracting private keys from net590 scan...")
    
    private_keys = set()
    source_files = defaultdict(list)
    
    try:
        with open('net590_scan_results.txt', 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        current_file = ""
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Track current file being processed
            if "🎯" in line and ("/" in line or ".json" in line or ".txt" in line):
                current_file = line.replace("🎯", "").strip()
            
            # Look for private key entries
            if "🔑 PRIVATE KEY:" in line:
                # Extract truncated key pattern
                key_match = re.search(r'PRIVATE KEY: ([a-fA-F0-9]+)\.\.\.([a-fA-F0-9]+)', line)
                if key_match:
                    key_start = key_match.group(1)
                    key_end = key_match.group(2)
                    
                    # Look for full 64-character hex keys in context
                    search_start = max(0, i-3)
                    search_end = min(len(lines), i+3)
                    
                    for j in range(search_start, search_end):
                        context_line = lines[j].strip()
                        
                        # Find all 64-char hex strings in the context
                        hex_matches = re.findall(r'\b([a-fA-F0-9]{64})\b', context_line)
                        
                        for hex_key in hex_matches:
                            # Check if this matches our truncated display
                            if (hex_key.lower().startswith(key_start.lower()) and 
                                hex_key.lower().endswith(key_end.lower())):
                                
                                # Validate it's a reasonable private key
                                if (not all(c == '0' for c in hex_key) and
                                    not all(c == 'f' for c in hex_key.lower()) and
                                    not all(c == '1' for c in hex_key) and
                                    hex_key.count('0') < 50):  # Not mostly zeros
                                    
                                    private_keys.add(hex_key.lower())
                                    source_files[hex_key.lower()].append(current_file)
        
        print(f"✅ Extracted {len(private_keys)} unique private keys from net590")
        
        if private_keys:
            # Save keys
            keys_list = sorted(private_keys)
            
            with open('net590_extracted_keys.txt', 'w') as f:
                for key in keys_list:
                    f.write(f"{key}\n")
            
            # Save detailed data with sources
            detailed_data = []
            for key in keys_list:
                detailed_data.append({
                    'key': key,
                    'source_files': source_files[key]
                })
            
            with open('net590_keys_detailed.json', 'w') as f:
                json.dump(detailed_data, f, indent=2)
            
            print(f"💾 Keys saved to net590_extracted_keys.txt")
            print(f"💾 Detailed data saved to net590_keys_detailed.json")
            
            # Show first 10 keys
            print("\nFirst 10 extracted keys:")
            for i, key in enumerate(keys_list[:10], 1):
                print(f"{i:2d}. {key}")
        
        return list(private_keys)
        
    except Exception as e:
        print(f"❌ Error extracting keys: {e}")
        return []

if __name__ == "__main__":
    keys = extract_net590_keys()
    
    if keys:
        print(f"\n🎯 SUCCESS! Extracted {len(keys)} private keys from net590!")
        print("🚀 Ready to check balances for these keys!")
    else:
        print("\n❌ No private keys could be extracted")
