#!/usr/bin/env python3
"""
Targeted Autofill Analysis
Focus on the specific lines where our funded addresses were found
"""

import re
import json
from typing import Dict, List

def analyze_autofill_context():
    """Analyze the context around our funded addresses in autofill data"""
    
    print("🔍 TARGETED AUTOFILL ANALYSIS")
    print("="*60)
    
    target_info = {
        "0x6e59e2a98d12f45ab5872942fe45a1036b1ea9c9": {
            "balance": 0.296807,
            "line_numbers": [5284, 5287]  # From previous grep search
        },
        "0x8bd210f4a679eced866b725a85ba75a2c158f651": {
            "balance": 0.194946,
            "line_numbers": [94]  # From previous grep search
        }
    }
    
    autofill_file = "text/Autofills.txt"
    
    try:
        with open(autofill_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        print(f"📁 Loaded {len(lines)} lines from {autofill_file}")
        
        for address, info in target_info.items():
            balance = info['balance']
            line_nums = info['line_numbers']
            
            print(f"\n🎯 Analyzing address: {address}")
            print(f"   Balance: {balance} ETH")
            print(f"   Found at lines: {line_nums}")
            
            for line_num in line_nums:
                # Extract context around the line (1-indexed to 0-indexed)
                idx = line_num - 1
                
                if 0 <= idx < len(lines):
                    print(f"\n📍 Line {line_num} context:")
                    
                    # Show 20 lines before and after
                    start = max(0, idx - 20)
                    end = min(len(lines), idx + 21)
                    
                    for i in range(start, end):
                        line_content = lines[i].strip()
                        marker = ">>>" if i == idx else "   "
                        print(f"{marker} {i+1:4d}: {line_content}")
                        
                        # Look for private key patterns in nearby lines
                        if i != idx:  # Don't check the address line itself
                            # Check for 64-char hex strings
                            hex_matches = re.findall(r'\b[a-fA-F0-9]{64}\b', line_content)
                            if hex_matches:
                                print(f"         🔑 Potential key: {hex_matches[0]}")
                                
                                # Test if this key generates our address
                                test_result = test_private_key(hex_matches[0], address)
                                if test_result:
                                    print(f"         ✅ KEY MATCH FOUND!")
                                    return hex_matches[0], address
                            
                            # Check for other wallet-related patterns
                            if any(keyword in line_content.lower() for keyword in 
                                   ['private', 'key', 'seed', 'mnemonic', 'wallet', 'ethereum']):
                                print(f"         🔍 Wallet-related content: {line_content[:100]}...")
                    
                else:
                    print(f"   ⚠️  Line {line_num} is out of range")
        
        # Try broader context search
        print(f"\n🔍 BROADER CONTEXT SEARCH")
        print("-" * 40)
        
        for address in target_info.keys():
            search_broader_context(lines, address, target_info[address]['balance'])
        
    except FileNotFoundError:
        print(f"❌ Could not find {autofill_file}")
        return None, None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None
    
    return None, None

def test_private_key(private_key_hex: str, target_address: str) -> bool:
    """Test if a private key generates the target address"""
    try:
        from eth_keys import keys
        
        # Remove 0x prefix if present
        if private_key_hex.startswith('0x'):
            private_key_hex = private_key_hex[2:]
        
        if len(private_key_hex) != 64:
            return False
            
        private_key_bytes = bytes.fromhex(private_key_hex)
        private_key = keys.PrivateKey(private_key_bytes)
        generated_address = private_key.public_key.to_checksum_address().lower()
        
        return generated_address == target_address.lower()
        
    except Exception:
        return False

def search_broader_context(lines: List[str], target_address: str, balance: float):
    """Search for the address and look at broader context"""
    
    print(f"\n🔍 Searching for {target_address} ({balance} ETH)")
    
    # Find all occurrences of this address
    occurrences = []
    for i, line in enumerate(lines):
        if target_address.lower() in line.lower():
            occurrences.append(i)
    
    print(f"   Found at {len(occurrences)} locations: lines {[i+1 for i in occurrences]}")
    
    # For each occurrence, look at surrounding form data
    for occurrence in occurrences:
        print(f"\n   📍 Occurrence at line {occurrence + 1}:")
        
        # Look at 100 lines before and after for form patterns
        start = max(0, occurrence - 100)
        end = min(len(lines), occurrence + 101)
        
        context_text = '\n'.join(lines[start:end])
        
        # Look for form field patterns that might indicate private keys
        form_patterns = [
            r'(private[_\s]*key|privatekey)[^\n]*([a-fA-F0-9]{64})',
            r'(seed|mnemonic)[^\n]*([a-zA-Z\s]{100,})',  # Seed phrases
            r'(password|pass)[^\n]*([^\n]{10,50})',      # Passwords
            r'([a-fA-F0-9]{64})[^\n]*(private|key)',     # Key before label
        ]
        
        for pattern in form_patterns:
            matches = re.finditer(pattern, context_text, re.IGNORECASE)
            for match in matches:
                print(f"      🔑 Potential pattern: {match.group()[:100]}...")
                
                # Extract potential key
                hex_parts = re.findall(r'[a-fA-F0-9]{64}', match.group())
                for hex_part in hex_parts:
                    if test_private_key(hex_part, target_address):
                        print(f"      ✅ PRIVATE KEY FOUND: {hex_part}")
                        return hex_part

def main():
    result = analyze_autofill_context()
    if result[0]:
        print(f"\n🎉 SUCCESS!")
        print(f"Private Key: {result[0]}")
        print(f"Address: {result[1]}")
        
        # Save the result
        with open('FOUND_PRIVATE_KEY.txt', 'w') as f:
            f.write(f"Address: {result[1]}\n")
            f.write(f"Private Key: {result[0]}\n")
            f.write(f"Source: Autofill context analysis\n")
    else:
        print(f"\n❌ No private keys found in autofill context")

if __name__ == "__main__":
    main()
