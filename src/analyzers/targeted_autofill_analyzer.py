#!/usr/bin/env python3
"""
Targeted Autofill Analyzer
Focused analysis of the specific autofill file containing our target address
"""

import re
import json
from eth_keys import keys
import hashlib
import base64

TARGET_FILE = "/home/admin/Downloads/net605/[BR]170.247.37.63/Chrome/Profile 1/Autofills.txt"
TARGET_ADDRESS = "0x6e59e2a98d12f45ab5872942fe45a1036b1ea9c9"
TARGET_BALANCE = 0.296807

def address_from_private_key(private_key_hex):
    """Generate Ethereum address from private key"""
    try:
        if private_key_hex.startswith('0x'):
            private_key_hex = private_key_hex[2:]
        if len(private_key_hex) != 64:
            return None
        private_key_bytes = bytes.fromhex(private_key_hex)
        private_key = keys.PrivateKey(private_key_bytes)
        return private_key.public_key.to_checksum_address().lower()
    except:
        return None

def analyze_autofill_file():
    """Deep analysis of the autofill file containing our target"""
    
    print("🎯 TARGETED AUTOFILL ANALYSIS")
    print("="*60)
    print(f"📁 File: {TARGET_FILE}")
    print(f"🎯 Target: {TARGET_ADDRESS}")
    print(f"💰 Balance: {TARGET_BALANCE:.6f} ETH")
    
    try:
        with open(TARGET_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        print(f"📄 File size: {len(content):,} characters")
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None
    
    # Find the exact location of our target address
    target_positions = []
    search_content = content.lower()
    target_lower = TARGET_ADDRESS.lower()
    
    start = 0
    while True:
        pos = search_content.find(target_lower, start)
        if pos == -1:
            break
        target_positions.append(pos)
        start = pos + 1
    
    print(f"📍 Found target address at {len(target_positions)} positions: {target_positions}")
    
    if not target_positions:
        print("❌ Target address not found in file")
        return None
    
    # Analyze context around each occurrence
    results = []
    
    for i, pos in enumerate(target_positions, 1):
        print(f"\n🔍 ANALYZING OCCURRENCE {i} (position {pos})")
        print("-" * 40)
        
        # Extract large context (5000 chars before/after)
        context_start = max(0, pos - 5000)
        context_end = min(len(content), pos + 5000)
        context = content[context_start:context_end]
        
        print(f"📊 Context size: {len(context)} characters")
        
        # Show the immediate area around the address
        local_start = max(0, pos - context_start - 200)
        local_end = min(len(context), pos - context_start + 200)
        local_context = context[local_start:local_end]
        
        print(f"\n📝 LOCAL CONTEXT AROUND ADDRESS:")
        lines = local_context.split('\n')
        for line_num, line in enumerate(lines, 1):
            marker = ">>>" if TARGET_ADDRESS.lower() in line.lower() else "   "
            print(f"{marker} {line_num:2d}: {line}")
        
        # Extract all potential private key patterns from the full context
        print(f"\n🔑 SEARCHING FOR PRIVATE KEY PATTERNS...")
        
        candidates = set()
        
        # Pattern 1: 64-character hex strings
        hex_64 = re.findall(r'\b[a-fA-F0-9]{64}\b', context)
        candidates.update(hex_64)
        print(f"   Found {len(hex_64)} 64-char hex patterns")
        
        # Pattern 2: Form field patterns
        form_patterns = [
            r'privatekey[=:\s]+([a-fA-F0-9]{64})',
            r'private_key[=:\s]+([a-fA-F0-9]{64})',
            r'privkey[=:\s]+([a-fA-F0-9]{64})',
            r'key[=:\s]+([a-fA-F0-9]{64})',
            r'secret[=:\s]+([a-fA-F0-9]{64})',
            r'wallet[=:\s]+([a-fA-F0-9]{64})',
            r'password[=:\s]+([a-fA-F0-9]{64})',
        ]
        
        form_matches = 0
        for pattern in form_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            candidates.update(matches)
            form_matches += len(matches)
        print(f"   Found {form_matches} form field patterns")
        
        # Pattern 3: Base64 patterns
        base64_pattern = r'\b[A-Za-z0-9+/]{43}=?\b'
        base64_matches = re.findall(base64_pattern, context)
        
        base64_keys = 0
        for b64 in base64_matches:
            try:
                decoded = base64.b64decode(b64 + '==')
                if len(decoded) == 32:
                    hex_key = decoded.hex()
                    candidates.add(hex_key)
                    base64_keys += 1
            except:
                continue
        print(f"   Found {base64_keys} valid base64 32-byte patterns")
        
        # Pattern 4: Lines near the address
        context_lines = context.split('\n')
        address_lines = []
        
        for line_idx, line in enumerate(context_lines):
            if TARGET_ADDRESS.lower() in line.lower():
                address_lines.append(line_idx)
        
        nearby_patterns = 0
        for addr_line in address_lines:
            # Check 10 lines before and after the address
            for offset in range(-10, 11):
                check_line = addr_line + offset
                if 0 <= check_line < len(context_lines):
                    line = context_lines[check_line]
                    line_hex = re.findall(r'\b[a-fA-F0-9]{64}\b', line)
                    candidates.update(line_hex)
                    nearby_patterns += len(line_hex)
        print(f"   Found {nearby_patterns} patterns near address lines")
        
        # Pattern 5: Hash common words from context
        words = re.findall(r'\b\w{4,20}\b', context.lower())
        unique_words = list(set(words))[:100]  # Limit to 100 most common
        
        hashed_words = 0
        for word in unique_words:
            if word.isalpha() and len(word) >= 4:
                # Hash variations
                variations = [word, word.upper(), word.capitalize(), f"{word}123", f"123{word}", f"{word}1"]
                for variation in variations:
                    word_hash = hashlib.sha256(variation.encode()).hexdigest()
                    candidates.add(word_hash)
                    hashed_words += 1
        print(f"   Generated {hashed_words} word-based hash candidates")
        
        print(f"\n🧪 TESTING {len(candidates)} PRIVATE KEY CANDIDATES...")
        
        # Test all candidates
        tested = 0
        for candidate in candidates:
            tested += 1
            if tested % 100 == 0:
                print(f"   Tested {tested}/{len(candidates)} candidates...")
            
            try:
                generated_address = address_from_private_key(candidate)
                if generated_address and generated_address == TARGET_ADDRESS.lower():
                    result = {
                        'file': TARGET_FILE,
                        'address': TARGET_ADDRESS,
                        'private_key': candidate,
                        'balance': TARGET_BALANCE,
                        'occurrence': i,
                        'context_position': pos
                    }
                    
                    results.append(result)
                    
                    print(f"\n🎉 PRIVATE KEY FOUND!")
                    print(f"   Address: {TARGET_ADDRESS}")
                    print(f"   Balance: {TARGET_BALANCE:.6f} ETH")
                    print(f"   Private Key: {candidate}")
                    print(f"   Occurrence: {i}")
                    
                    # Save immediately
                    with open('AUTOFILL_PRIVATE_KEY_FOUND.json', 'w') as f:
                        json.dump(result, f, indent=2)
                    
                    return result
                    
            except Exception:
                continue
        
        print(f"   ❌ No matches found in {tested} candidates for occurrence {i}")
    
    print(f"\n📊 ANALYSIS COMPLETE")
    print(f"   Occurrences analyzed: {len(target_positions)}")
    print(f"   Private keys found: {len(results)}")
    
    if not results:
        print(f"\n💡 MANUAL INSPECTION RECOMMENDED")
        print(f"   The private key might be:")
        print(f"   • In a different encoding format")
        print(f"   • Split across multiple fields")
        print(f"   • Encrypted or obfuscated")
        print(f"   • In a nearby file or form field")
    
    return results

def main():
    result = analyze_autofill_file()
    
    if result:
        print(f"\n✅ SUCCESS! Private key recovered!")
        print(f"💰 Can recover: {TARGET_BALANCE:.6f} ETH (~${TARGET_BALANCE * 2500:.2f})")
        print(f"📁 Details saved to: AUTOFILL_PRIVATE_KEY_FOUND.json")
    else:
        print(f"\n⚠️  Private key not found in automated analysis")
        print(f"🔍 Consider manual inspection of the autofill file")
        print(f"📁 File location: {TARGET_FILE}")

if __name__ == "__main__":
    main()
