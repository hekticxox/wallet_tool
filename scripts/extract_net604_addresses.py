#!/usr/bin/env python3

import re
from collections import Counter

def extract_addresses_from_scan():
    """Extract unique addresses from net604 scan results"""
    
    bitcoin_addresses = set()
    
    print("🔍 Extracting Bitcoin addresses from net604 scan results...")
    
    try:
        with open('net604_scan_results.txt', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Extract Bitcoin Legacy addresses (1...)
            legacy_pattern = r'\b(1[A-HJ-NP-Z1-9]{25,34})\b'
            legacy_matches = re.findall(legacy_pattern, content)
            
            # Extract Bitcoin SegWit addresses (3...)
            segwit_pattern = r'\b(3[A-HJ-NP-Z1-9]{25,34})\b'
            segwit_matches = re.findall(segwit_pattern, content)
            
            # Extract Bitcoin Bech32 addresses (bc1...)
            bech32_pattern = r'\b(bc1[a-z0-9]{39,59})\b'
            bech32_matches = re.findall(bech32_pattern, content)
            
            all_addresses = legacy_matches + segwit_matches + bech32_matches
            
            # Filter out obviously invalid addresses (too short, repeating patterns)
            valid_addresses = []
            for addr in all_addresses:
                if len(addr) >= 26 and not all(c == addr[0] for c in addr):  # Not all same character
                    valid_addresses.append(addr)
            
            bitcoin_addresses.update(valid_addresses)
            
        print(f"✅ Found {len(bitcoin_addresses)} unique Bitcoin addresses")
        
        # Count by type
        legacy_count = sum(1 for addr in bitcoin_addresses if addr.startswith('1'))
        segwit_count = sum(1 for addr in bitcoin_addresses if addr.startswith('3'))
        bech32_count = sum(1 for addr in bitcoin_addresses if addr.startswith('bc1'))
        
        print(f"   - Legacy (1...): {legacy_count}")
        print(f"   - SegWit (3...): {segwit_count}")
        print(f"   - Bech32 (bc1...): {bech32_count}")
        
        # Save addresses
        with open('net604_bitcoin_addresses.txt', 'w') as f:
            for addr in sorted(bitcoin_addresses):
                f.write(f"{addr}\n")
        
        print(f"💾 Addresses saved to net604_bitcoin_addresses.txt")
        
        # Show first 10 addresses
        print("\nFirst 10 addresses found:")
        for i, addr in enumerate(sorted(bitcoin_addresses)[:10], 1):
            print(f"{i:2d}. {addr}")
            
        return list(bitcoin_addresses)
        
    except Exception as e:
        print(f"❌ Error extracting addresses: {e}")
        return []

if __name__ == "__main__":
    addresses = extract_addresses_from_scan()
    
    print(f"\n🎯 Summary: Found {len(addresses)} unique Bitcoin addresses from net604")
    print("💡 Note: These are addresses only (no private keys found)")
    print("   They may be watch-only addresses or require exchange login")
