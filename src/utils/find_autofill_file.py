#!/usr/bin/env python3
"""
Find the exact autofill file containing both target address and recovery key
"""

import os
import re

def find_autofill_with_context():
    target_address = "0x6e59e2a98d12f45ab5872942fe45a1036b1ea9c9"
    recovery_key = "8AKP9G3UJYWK4OYGFLRWEUBHZTA="
    
    print(f"🔍 SEARCHING FOR AUTOFILL FILE WITH CONTEXT")
    print(f"Target Address: {target_address}")
    print(f"Recovery Key: {recovery_key}")
    print("-" * 80)
    
    # Search in all possible locations
    search_paths = [
        "/home/admin/Downloads",
        "/home/admin/wallet_tool",
        "/home/admin"
    ]
    
    autofill_files = []
    
    # Find all Autofills.txt files
    for search_path in search_paths:
        if os.path.exists(search_path):
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    if "autofill" in file.lower() or file == "Autofills.txt":
                        full_path = os.path.join(root, file)
                        autofill_files.append(full_path)
    
    print(f"📁 Found {len(autofill_files)} autofill files")
    for f in autofill_files:
        print(f"   {f}")
    
    print("\n🔍 SEARCHING FOR TARGET CONTENT...")
    
    for file_path in autofill_files:
        try:
            print(f"\n📄 Checking: {file_path}")
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                has_address = target_address.lower() in content.lower()
                has_recovery = recovery_key in content
                
                print(f"   Address found: {has_address}")
                print(f"   Recovery key found: {has_recovery}")
                
                if has_address and has_recovery:
                    print(f"🎯 BINGO! Found both in: {file_path}")
                    print(f"📊 File size: {len(content)} characters")
                    
                    # Extract context around both items
                    print(f"\n📍 CONTEXT EXTRACTION:")
                    
                    # Find address context
                    addr_pos = content.lower().find(target_address.lower())
                    if addr_pos >= 0:
                        start = max(0, addr_pos - 200)
                        end = min(len(content), addr_pos + len(target_address) + 200)
                        print(f"\n🏷️  ADDRESS CONTEXT:")
                        print(f"Position: {addr_pos}")
                        context = content[start:end]
                        print(f"Context:\n{context}")
                    
                    # Find recovery key context
                    key_pos = content.find(recovery_key)
                    if key_pos >= 0:
                        start = max(0, key_pos - 200)
                        end = min(len(content), key_pos + len(recovery_key) + 200)
                        print(f"\n🔑 RECOVERY KEY CONTEXT:")
                        print(f"Position: {key_pos}")
                        context = content[start:end]
                        print(f"Context:\n{context}")
                    
                    # Look for other patterns nearby
                    print(f"\n🔍 SCANNING FOR ADDITIONAL PATTERNS:")
                    
                    # Extract lines containing our items
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if target_address.lower() in line.lower() or recovery_key in line:
                            print(f"Line {i+1}: {line.strip()}")
                            # Show surrounding lines
                            for j in range(max(0, i-2), min(len(lines), i+3)):
                                if j != i:
                                    print(f"Line {j+1}: {lines[j].strip()}")
                            print("-" * 40)
                    
                    return file_path
                    
                elif has_address:
                    print(f"   ℹ️  Has address only")
                elif has_recovery:
                    print(f"   ℹ️  Has recovery key only")
                    
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")
    
    print(f"\n❌ No autofill file found containing both items")
    return None

if __name__ == "__main__":
    find_autofill_with_context()
