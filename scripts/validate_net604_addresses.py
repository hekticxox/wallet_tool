#!/usr/bin/env python3

import re
import hashlib
import base58

def validate_bitcoin_address(address):
    """Validate if a Bitcoin address is properly formatted"""
    
    # Check if it's a valid Base58 string (Legacy addresses)
    if address.startswith('1') or address.startswith('3'):
        try:
            # Bitcoin addresses should only contain Base58 characters
            base58_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
            if not all(c in base58_chars for c in address):
                return False
            
            # Length check
            if len(address) < 26 or len(address) > 35:
                return False
                
            # Try to decode - if it fails, invalid address
            decoded = base58.b58decode(address)
            if len(decoded) != 25:
                return False
                
            return True
        except:
            return False
    
    # Bech32 addresses (bc1...)
    elif address.startswith('bc1'):
        # Basic length and character check for bech32
        if len(address) < 42 or len(address) > 62:
            return False
        
        # Bech32 uses only lowercase and numbers
        allowed_chars = "023456789acdefghjklmnpqrstuvwxyz"
        if not all(c in allowed_chars for c in address.lower()):
            return False
            
        return True
    
    return False

def extract_valid_addresses():
    """Extract and validate Bitcoin addresses from scan results"""
    
    print("🔍 Validating Bitcoin addresses from net604 scan...")
    
    valid_addresses = set()
    
    try:
        with open('net604_scan_results.txt', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # More precise patterns for Bitcoin addresses
            patterns = [
                r'\b(1[A-HJ-NP-Z1-9]{25,34})\b',  # Legacy
                r'\b(3[A-HJ-NP-Z1-9]{25,34})\b',  # SegWit
                r'\b(bc1[a-z0-9]{39,59})\b'       # Bech32
            ]
            
            all_matches = []
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                all_matches.extend(matches)
            
            # Validate each address
            for addr in all_matches:
                if validate_bitcoin_address(addr):
                    valid_addresses.add(addr)
    
        print(f"✅ Found {len(valid_addresses)} valid Bitcoin addresses")
        
        if valid_addresses:
            # Count by type
            legacy_count = sum(1 for addr in valid_addresses if addr.startswith('1'))
            segwit_count = sum(1 for addr in valid_addresses if addr.startswith('3'))
            bech32_count = sum(1 for addr in valid_addresses if addr.startswith('bc1'))
            
            print(f"   - Legacy (1...): {legacy_count}")
            print(f"   - SegWit (3...): {segwit_count}")
            print(f"   - Bech32 (bc1...): {bech32_count}")
            
            # Save valid addresses
            with open('net604_valid_bitcoin_addresses.txt', 'w') as f:
                for addr in sorted(valid_addresses):
                    f.write(f"{addr}\n")
            
            print(f"💾 Valid addresses saved to net604_valid_bitcoin_addresses.txt")
            
            # Show first 20 valid addresses
            print("\nFirst 20 valid addresses:")
            for i, addr in enumerate(sorted(valid_addresses)[:20], 1):
                print(f"{i:2d}. {addr}")
        else:
            print("❌ No valid Bitcoin addresses found")
            
        return list(valid_addresses)
        
    except Exception as e:
        print(f"❌ Error validating addresses: {e}")
        return []

if __name__ == "__main__":
    addresses = extract_valid_addresses()
    
    if addresses:
        print(f"\n🎯 Summary: {len(addresses)} valid Bitcoin addresses found")
        print("💡 These addresses can be checked for balances (watch-only)")
        print("   No private keys means they cannot be spent from")
    else:
        print("\n❌ No valid Bitcoin addresses found in net604 dataset")
