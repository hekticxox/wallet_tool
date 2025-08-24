#!/usr/bin/env python3
"""
Quick preview of comprehensive_scan_results.json to understand the data structure
"""

import json
import os

def preview_comprehensive_scan():
    filepath = '/home/admin/wallet_tool/comprehensive_scan_results.json'
    
    if not os.path.exists(filepath):
        print("File not found!")
        return
        
    with open(filepath, 'r') as f:
        data = json.load(f)
        
    print("=== COMPREHENSIVE SCAN RESULTS PREVIEW ===")
    print(f"File size: {os.path.getsize(filepath)} bytes")
    
    # Show summary
    if 'scan_summary' in data:
        print("\nSCAN SUMMARY:")
        for key, value in data['scan_summary'].items():
            print(f"  {key}: {value}")
    
    # Show first few private keys
    if 'private_keys_found' in data and data['private_keys_found']:
        print(f"\nFIRST 3 PRIVATE KEYS STRUCTURE:")
        for i, key_data in enumerate(data['private_keys_found'][:3]):
            print(f"  Key {i+1}:")
            if isinstance(key_data, dict):
                for k, v in key_data.items():
                    print(f"    {k}: {str(v)[:100]}...")
            else:
                print(f"    {str(key_data)[:100]}...")
            print()
    
    # Show addresses structure
    if 'addresses_found' in data and data['addresses_found']:
        print(f"FIRST 3 ADDRESSES STRUCTURE:")
        for i, addr_data in enumerate(data['addresses_found'][:3]):
            print(f"  Address {i+1}:")
            if isinstance(addr_data, dict):
                for k, v in addr_data.items():
                    print(f"    {k}: {str(v)[:100]}...")
            else:
                print(f"    {str(addr_data)[:100]}...")
            print()
    
    # Count total unique addresses
    addresses = set()
    
    def extract_addresses_recursive(obj):
        if isinstance(obj, str) and obj.startswith('0x') and len(obj) == 42:
            addresses.add(obj)
        elif isinstance(obj, dict):
            for v in obj.values():
                extract_addresses_recursive(v)
        elif isinstance(obj, list):
            for item in obj:
                extract_addresses_recursive(item)
    
    extract_addresses_recursive(data)
    print(f"\nTOTAL UNIQUE ETHEREUM ADDRESSES FOUND: {len(addresses)}")
    
    # Show some sample addresses
    sample_addresses = list(addresses)[:10]
    print(f"\nSAMPLE ADDRESSES:")
    for addr in sample_addresses:
        print(f"  {addr}")

if __name__ == "__main__":
    preview_comprehensive_scan()
