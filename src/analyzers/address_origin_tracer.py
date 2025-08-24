#!/usr/bin/env python3
"""
Address Origin Tracer - Find the source of our high-value funded address
"""

import json
import os
import subprocess
from web3 import Web3
from eth_account import Account

# Configuration
TARGET_ADDRESS = "0x8390a1da07e376ef7add4be859ba74fb83aa02d5"

def check_extracted_keys():
    """Check our extracted private keys file for this address"""
    print("🔍 CHECKING EXTRACTED PRIVATE KEYS")
    print("-" * 40)
    
    try:
        with open("extracted_private_keys.json", 'r') as f:
            keys_data = json.load(f)
        
        print(f"Total private keys: {len(keys_data)}")
        
        # Test each key to see if it generates our target address
        matches_found = 0
        for i, key_entry in enumerate(keys_data, 1):
            if i % 100 == 0:
                print(f"Tested {i} keys...")
            
            try:
                key = key_entry.get("private_key", "").strip()
                if not key:
                    continue
                
                # Normalize key format
                if key.startswith("0x"):
                    key = key[2:]
                
                if len(key) != 64:
                    continue
                
                # Generate address from private key
                account = Account.from_key(key)
                generated_address = account.address.lower()
                
                if generated_address == TARGET_ADDRESS.lower():
                    print(f"🎉 MATCH FOUND!")
                    print(f"Private Key: {key}")
                    print(f"Address: {generated_address}")
                    print(f"Source: {key_entry.get('source', 'unknown')}")
                    print(f"Entry #{i}")
                    matches_found += 1
                    return key_entry
                    
            except Exception as e:
                continue
        
        print(f"❌ No matches found in {len(keys_data)} private keys")
        return None
        
    except FileNotFoundError:
        print("❌ extracted_private_keys.json not found")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def reverse_lookup_in_binary_files():
    """Search for the address in binary format in database files"""
    print("\n🔍 CHECKING BINARY DATABASE FILES")
    print("-" * 40)
    
    # The address without 0x prefix in lowercase
    address_hex = TARGET_ADDRESS[2:].lower()
    
    # Check for binary representation
    binary_files = []
    try:
        result = subprocess.run(
            ["find", ".", "-name", "*.ldb", "-o", "-name", "*.db"], 
            capture_output=True, text=True, timeout=30
        )
        binary_files = result.stdout.strip().split('\n') if result.stdout else []
    except:
        pass
    
    print(f"Found {len(binary_files)} binary database files")
    
    matches = []
    for file_path in binary_files[:20]:  # Check first 20 files
        if not file_path or not os.path.exists(file_path):
            continue
            
        try:
            # Search for hex pattern in binary file
            result = subprocess.run(
                ["strings", file_path], 
                capture_output=True, text=True, timeout=10
            )
            
            if address_hex in result.stdout.lower():
                matches.append(file_path)
                print(f"✅ Found in: {file_path}")
                
                # Extract context
                lines = result.stdout.split('\n')
                for i, line in enumerate(lines):
                    if address_hex in line.lower():
                        start = max(0, i-3)
                        end = min(len(lines), i+4)
                        print(f"   Context:")
                        for j in range(start, end):
                            marker = " >>> " if j == i else "     "
                            print(f"   {marker}{lines[j]}")
                        print()
                        break
        except:
            continue
    
    return matches

def check_comprehensive_scan_source():
    """Check where this address came from in our comprehensive scan"""
    print("\n🔍 TRACING COMPREHENSIVE SCAN SOURCE")
    print("-" * 40)
    
    # This address was found in our comprehensive scan
    # It must have come from one of our extracted addresses
    try:
        with open("enhanced_wallet_extraction_results.json", 'r') as f:
            extraction_data = json.load(f)
        
        print(f"Checking enhanced extraction results...")
        
        # Search for this address in the extraction results
        for entry in extraction_data:
            if isinstance(entry, dict) and "address" in entry:
                if entry["address"].lower() == TARGET_ADDRESS.lower():
                    print(f"🎉 FOUND IN EXTRACTION RESULTS!")
                    print(f"Entry: {json.dumps(entry, indent=2)}")
                    return entry
        
        print("❌ Not found in enhanced extraction results")
        return None
        
    except FileNotFoundError:
        print("❌ enhanced_wallet_extraction_results.json not found")
        return None

def trace_address_origin():
    """Complete address origin tracing"""
    print(f"🎯 TRACING ORIGIN OF: {TARGET_ADDRESS}")
    print(f"💰 Value: 11.0565 ETH (~$27,641)")
    print("=" * 60)
    
    # Step 1: Check extracted private keys
    key_match = check_extracted_keys()
    
    # Step 2: Check binary database files
    binary_matches = reverse_lookup_in_binary_files()
    
    # Step 3: Check comprehensive scan source
    scan_source = check_comprehensive_scan_source()
    
    # Summary
    print("\n📊 ORIGIN TRACE SUMMARY")
    print("-" * 30)
    print(f"Private key match: {'✅' if key_match else '❌'}")
    print(f"Binary file matches: {len(binary_matches) if binary_matches else 0}")
    print(f"Scan source found: {'✅' if scan_source else '❌'}")
    
    if key_match:
        print(f"\n🚀 READY FOR RECOVERY!")
        print(f"Private key available for address {TARGET_ADDRESS}")
        return key_match
    else:
        print(f"\n❌ PRIVATE KEY NOT FOUND")
        print("This address may be:")
        print("• From a hardware wallet or external source")
        print("• Encrypted with a password we don't have")
        print("• Generated from a seed phrase not in our data")
        print("• A derived key that needs additional computation")
        
        if binary_matches:
            print(f"\nFound in binary files: {binary_matches}")
            print("Consider extracting wallet databases for key derivation")
    
    return None

if __name__ == "__main__":
    result = trace_address_origin()
