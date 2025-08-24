#!/usr/bin/env python3
"""
Target Address Locator - Find the exact file containing our target address
"""

import os
import re

def find_target_address():
    target_address = "0x6e59e2a98d12f45ab5872942fe45a1036b1ea9c9"
    recovery_key = "8AKP9G3UJYWK4OYGFLRWEUBHZTA="
    
    print(f"🔍 SEARCHING FOR TARGET ADDRESS: {target_address}")
    print(f"🔍 SEARCHING FOR RECOVERY KEY: {recovery_key}")
    print("-" * 80)
    
    # Search all directories
    search_dirs = [
        "/home/admin/wallet_tool/net605",
        "/home/admin/wallet_tool/net607", 
        "/home/admin/wallet_tool"
    ]
    
    found_files = []
    
    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
            
        print(f"📁 Searching in: {search_dir}")
        
        for root, dirs, files in os.walk(search_dir):
            for file in files:
                filepath = os.path.join(root, file)
                
                # Skip binary files
                if any(ext in filepath.lower() for ext in ['.exe', '.dll', '.bin', '.db', '.sqlite']):
                    continue
                    
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    # Check for target address
                    if target_address.lower() in content.lower():
                        print(f"✅ Found target address in: {filepath}")
                        found_files.append((filepath, 'target_address'))
                        
                        # Also check if recovery key is in same file
                        if recovery_key in content:
                            print(f"🎯 BOTH target address AND recovery key found in: {filepath}")
                            
                        # Extract context
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if target_address.lower() in line.lower():
                                start = max(0, i - 10)
                                end = min(len(lines), i + 10)
                                context = lines[start:end]
                                print(f"   Context around line {i+1}:")
                                for j, ctx_line in enumerate(context):
                                    marker = ">>> " if j == (i - start) else "    "
                                    print(f"   {marker}{start+j+1}: {ctx_line[:100]}")
                                print()
                                break
                                
                    # Check for recovery key
                    elif recovery_key in content:
                        print(f"🔑 Found recovery key in: {filepath}")
                        found_files.append((filepath, 'recovery_key'))
                        
                except Exception as e:
                    continue
                    
    print(f"\n📊 SUMMARY:")
    print(f"Found {len(found_files)} files with target data")
    
    for filepath, data_type in found_files:
        print(f"   📄 {os.path.basename(filepath)} ({data_type})")
        print(f"      Path: {filepath}")
    
    return found_files

if __name__ == "__main__":
    find_target_address()
