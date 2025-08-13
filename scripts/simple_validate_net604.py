#!/usr/bin/env python3

import re

def is_valid_bitcoin_address(address):
    """Basic validation for Bitcoin addresses"""
    
    # Legacy addresses (1...)
    if address.startswith('1'):
        if len(address) < 26 or len(address) > 35:
            return False
        # Check for valid Base58 characters
        base58_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        return all(c in base58_chars for c in address)
    
    # SegWit addresses (3...)
    elif address.startswith('3'):
        if len(address) < 26 or len(address) > 35:
            return False
        # Check for valid Base58 characters
        base58_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        return all(c in base58_chars for c in address)
    
    # Bech32 addresses (bc1...)
    elif address.startswith('bc1'):
        if len(address) < 42 or len(address) > 62:
            return False
        # Bech32 uses only lowercase letters and numbers
        return address.islower() and all(c in "023456789acdefghjklmnpqrstuvwxyz" for c in address[3:])
    
    return False

def extract_valid_addresses():
    """Extract and validate Bitcoin addresses from scan results"""
    
    print("🔍 Extracting valid Bitcoin addresses from net604 scan...")
    
    valid_addresses = set()
    
    try:
        with open('net604_scan_results.txt', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Find all potential Bitcoin addresses
            patterns = [
                r'\b(1[A-HJ-NP-Z1-9a-km-z]{25,34})\b',  # Legacy
                r'\b(3[A-HJ-NP-Z1-9a-km-z]{25,34})\b',  # SegWit
                r'\b(bc1[a-z0-9]{39,59})\b'             # Bech32
            ]
            
            all_candidates = []
            for pattern in patterns:
                matches = re.findall(pattern, content)
                all_candidates.extend(matches)
            
            # Validate each candidate
            for candidate in all_candidates:
                if is_valid_bitcoin_address(candidate):
                    valid_addresses.add(candidate)
    
        print(f"✅ Found {len(valid_addresses)} potentially valid Bitcoin addresses")
        
        if valid_addresses:
            # Count by type
            legacy_count = sum(1 for addr in valid_addresses if addr.startswith('1'))
            segwit_count = sum(1 for addr in valid_addresses if addr.startswith('3'))
            bech32_count = sum(1 for addr in valid_addresses if addr.startswith('bc1'))
            
            print(f"   - Legacy (1...): {legacy_count}")
            print(f"   - SegWit (3...): {segwit_count}")
            print(f"   - Bech32 (bc1...): {bech32_count}")
            
            # Save addresses
            with open('net604_valid_addresses.txt', 'w') as f:
                for addr in sorted(valid_addresses):
                    f.write(f"{addr}\n")
            
            print(f"💾 Valid addresses saved to net604_valid_addresses.txt")
            
            # Show some examples
            print("\nFirst 15 valid addresses:")
            for i, addr in enumerate(sorted(valid_addresses)[:15], 1):
                print(f"{i:2d}. {addr}")
        else:
            print("❌ No valid Bitcoin addresses found")
            
        return list(valid_addresses)
        
    except Exception as e:
        print(f"❌ Error extracting addresses: {e}")
        return []

if __name__ == "__main__":
    addresses = extract_valid_addresses()
    
    if addresses:
        print(f"\n🎯 Found {len(addresses)} potentially valid Bitcoin addresses")
        print("💡 These are watch-only addresses (no private keys)")
        print("   Can check balances but cannot spend from them")
    else:
        print("\n❌ No valid Bitcoin addresses found in net604")
