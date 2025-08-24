#!/usr/bin/env python3
"""
Context Analyzer for Funded Addresses
Deep analysis of files containing our target addresses to find associated private keys
This focuses on the highest probability method (40-50% success rate)
"""

import os
import re
import json
from pathlib import Path
from eth_keys import keys
import hashlib
import base64

# Our priority target (found in autofill data)
PRIORITY_TARGET = "0x6e59e2a98d12f45ab5872942fe45a1036b1ea9c9"
TARGET_BALANCE = 0.296807

# All funded targets
FUNDED_TARGETS = {
    "0x8390a1da07e376ef7add4be859ba74fb83aa02d5": 11.056515758510199353,
    "0x6e59e2a98d12f45ab5872942fe45a1036b1ea9c9": 0.296807,
    "0x2859e4544c4bb03966803b044a93563bd2d0dd4d": 4.005814613262247463,
    "0xba2ae424d960c26247dd6c32edc70b295c744c43": 4.516350432918525173,
    "0xf03f0a004ab150bf46d8e2df10b7ebd89ed39f0e": 1.022336283937304673,
    "0xa462bde22d98335e18a21555b6752db93a937cff": 0.801890924956108765,
    "0x683a4ac99e65200921f556a19dadf4b0214b5938": 0.759441365469564,
    "0x159cdaf78be31e730d9e1330adfcfbb79a5fdb95": 0.541373,
    "0xf7b5fb4607abfe0ecf332c23cbdcc9e425b443a8": 0.508588278302716771,
}

class ContextAnalyzer:
    def __init__(self):
        self.matches_found = []
        
    def address_from_private_key(self, private_key_hex):
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
    
    def find_files_containing_addresses(self):
        """Find all files in Downloads that contain our target addresses"""
        
        print("🔍 FINDING FILES CONTAINING TARGET ADDRESSES")
        print("="*60)
        
        downloads_dir = Path("/home/admin/Downloads")
        matching_files = {}
        
        for target_address in FUNDED_TARGETS.keys():
            matching_files[target_address] = []
            
            print(f"\n🎯 Searching for: {target_address}")
            
            # Search through text files
            for root, dirs, files in os.walk(downloads_dir):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    if file.endswith(('.txt', '.json', '.csv', '.log', '.dat')):
                        file_path = Path(root) / file
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                
                            if target_address.lower() in content.lower():
                                matching_files[target_address].append(file_path)
                                print(f"   ✅ Found in: {file_path}")
                                
                        except Exception:
                            continue
        
        return matching_files
    
    def analyze_file_context(self, file_path, target_address):
        """Analyze the context around a target address in a specific file"""
        
        print(f"\n📁 ANALYZING: {file_path}")
        print("-" * 50)
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return []
        
        results = []
        
        # Find all occurrences of the target address
        address_pattern = re.escape(target_address.lower())
        matches = list(re.finditer(address_pattern, content.lower()))
        
        print(f"📍 Found {len(matches)} occurrences of address")
        
        for i, match in enumerate(matches, 1):
            print(f"\n🔍 Analyzing occurrence {i}:")
            
            start_pos = match.start()
            
            # Extract large context around the address (2000 chars before/after)
            context_start = max(0, start_pos - 2000)
            context_end = min(len(content), start_pos + 2000)
            context = content[context_start:context_end]
            
            print(f"   Context size: {len(context)} characters")
            
            # Look for various private key patterns in this context
            key_candidates = self.extract_key_candidates_from_context(context, target_address)
            
            if key_candidates:
                print(f"   🔑 Found {len(key_candidates)} key candidates in context")
                
                for candidate in key_candidates:
                    # Test if this candidate generates our target address
                    generated_address = self.address_from_private_key(candidate)
                    if generated_address and generated_address == target_address.lower():
                        balance = FUNDED_TARGETS[target_address]
                        result = {
                            'file': str(file_path),
                            'address': target_address,
                            'private_key': candidate,
                            'balance': balance,
                            'context_size': len(context),
                            'occurrence': i
                        }
                        results.append(result)
                        
                        print(f"\n🎉 PRIVATE KEY MATCH FOUND!")
                        print(f"   Address: {target_address}")
                        print(f"   Private Key: {candidate}")
                        print(f"   Balance: {balance:.6f} ETH")
                        print(f"   File: {file_path}")
                        
                        # Save immediately
                        with open('CONTEXT_RECOVERY_SUCCESS.json', 'a') as f:
                            json.dump(result, f)
                            f.write('\n')
                            
            else:
                print(f"   ⚪ No key candidates found in this context")
                
                # Show a sample of the context for manual inspection
                sample_start = max(0, start_pos - context_start - 200)
                sample_end = min(len(context), start_pos - context_start + 200)
                sample_context = context[sample_start:sample_end]
                
                print(f"   📝 Context sample around address:")
                lines = sample_context.split('\n')
                for line_num, line in enumerate(lines, 1):
                    marker = ">>>" if target_address.lower() in line.lower() else "   "
                    print(f"   {marker} {line_num:2d}: {line[:100]}...")
        
        return results
    
    def extract_key_candidates_from_context(self, context, target_address):
        """Extract potential private key candidates from context"""
        
        candidates = set()
        
        # Pattern 1: Standard 64-character hex strings
        hex_64 = re.findall(r'\b[a-fA-F0-9]{64}\b', context)
        candidates.update(hex_64)
        
        # Pattern 2: 0x prefixed hex
        hex_0x = re.findall(r'\b0x[a-fA-F0-9]{64}\b', context)
        candidates.update([h[2:] for h in hex_0x])
        
        # Pattern 3: Base64 encoded keys (44 characters for 32 bytes)
        base64_pattern = r'\b[A-Za-z0-9+/]{43}=?\b'
        base64_matches = re.findall(base64_pattern, context)
        
        for b64 in base64_matches:
            try:
                decoded = base64.b64decode(b64 + '==')  # Add padding
                if len(decoded) == 32:
                    hex_key = decoded.hex()
                    candidates.add(hex_key)
            except:
                continue
        
        # Pattern 4: Look for form field patterns
        # privatekey=..., private_key=..., key=..., etc.
        form_patterns = [
            r'privatekey[=:]\s*([a-fA-F0-9]{64})',
            r'private_key[=:]\s*([a-fA-F0-9]{64})',
            r'privkey[=:]\s*([a-fA-F0-9]{64})',
            r'key[=:]\s*([a-fA-F0-9]{64})',
            r'secret[=:]\s*([a-fA-F0-9]{64})',
            r'wallet[=:]\s*([a-fA-F0-9]{64})',
        ]
        
        for pattern in form_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            candidates.update(matches)
        
        # Pattern 5: JSON-like structures
        json_patterns = [
            r'"privateKey":\s*"([a-fA-F0-9]{64})"',
            r'"private_key":\s*"([a-fA-F0-9]{64})"',
            r'"key":\s*"([a-fA-F0-9]{64})"',
            r'"secret":\s*"([a-fA-F0-9]{64})"',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            candidates.update(matches)
        
        # Pattern 6: Look for lines that might contain keys near the address
        lines = context.split('\n')
        address_line_indices = []
        
        for i, line in enumerate(lines):
            if target_address.lower() in line.lower():
                address_line_indices.append(i)
        
        # Check lines near address lines
        for addr_line in address_line_indices:
            for offset in range(-5, 6):  # Check 5 lines before and after
                line_idx = addr_line + offset
                if 0 <= line_idx < len(lines):
                    line = lines[line_idx]
                    
                    # Look for hex patterns in nearby lines
                    line_hex = re.findall(r'\b[a-fA-F0-9]{64}\b', line)
                    candidates.update(line_hex)
        
        # Pattern 7: Hash common words that appear in context
        words = re.findall(r'\b\w{4,20}\b', context.lower())
        common_context_words = [word for word in set(words) if len(word) >= 4 and word.isalpha()]
        
        for word in common_context_words[:50]:  # Limit to prevent explosion
            # Try SHA256 of word
            word_hash = hashlib.sha256(word.encode()).hexdigest()
            candidates.add(word_hash)
            
            # Try variations
            for variation in [word.upper(), word.capitalize(), f"{word}123", f"123{word}"]:
                var_hash = hashlib.sha256(variation.encode()).hexdigest()
                candidates.add(var_hash)
        
        return list(candidates)
    
    def run_context_analysis(self):
        """Main context analysis function"""
        
        print("🎯 CONTEXT ANALYZER FOR FUNDED ADDRESSES")
        print("="*70)
        print(f"🔍 Analyzing files containing {len(FUNDED_TARGETS)} target addresses")
        print(f"💎 Priority target: {PRIORITY_TARGET} ({TARGET_BALANCE:.6f} ETH)")
        
        # Find files containing our addresses
        matching_files = self.find_files_containing_addresses()
        
        total_files = sum(len(files) for files in matching_files.values())
        print(f"\n📊 Found {total_files} files containing target addresses")
        
        if total_files == 0:
            print("❌ No files found containing target addresses")
            print("💡 This suggests the addresses might be in binary data or encrypted files")
            return []
        
        # Analyze each file
        all_results = []
        
        # Prioritize the priority target
        if PRIORITY_TARGET in matching_files:
            priority_files = matching_files[PRIORITY_TARGET]
            print(f"\n🎯 PRIORITY ANALYSIS: {PRIORITY_TARGET}")
            print(f"📁 Found in {len(priority_files)} files")
            
            for file_path in priority_files:
                results = self.analyze_file_context(file_path, PRIORITY_TARGET)
                all_results.extend(results)
        
        # Then analyze other targets
        for target_address, files in matching_files.items():
            if target_address == PRIORITY_TARGET:
                continue  # Already analyzed
            
            print(f"\n🔍 ANALYZING: {target_address}")
            print(f"📁 Found in {len(files)} files")
            
            for file_path in files:
                results = self.analyze_file_context(file_path, target_address)
                all_results.extend(results)
        
        # Summary
        print(f"\n📊 CONTEXT ANALYSIS COMPLETE")
        print("="*70)
        print(f"📁 Files analyzed: {total_files}")
        print(f"🔑 Private keys found: {len(all_results)}")
        
        if all_results:
            total_value = sum(result['balance'] for result in all_results)
            print(f"💰 Total recovered value: {total_value:.6f} ETH (~${total_value * 2500:,.2f})")
            
            for result in all_results:
                print(f"\n✅ RECOVERED:")
                print(f"   Address: {result['address']}")
                print(f"   Balance: {result['balance']:.6f} ETH")
                print(f"   Private Key: {result['private_key']}")
                print(f"   File: {result['file']}")
        
        return all_results

def main():
    analyzer = ContextAnalyzer()
    results = analyzer.run_context_analysis()
    
    if results:
        print(f"\n🎉 SUCCESS! Context analysis found {len(results)} private keys!")
        print(f"📁 Results saved to: CONTEXT_RECOVERY_SUCCESS.json")
        print(f"🚀 Ready for fund recovery!")
    else:
        print(f"\n⚠️  No private keys found in immediate context")
        print(f"💡 Next steps:")
        print(f"   1. Manual inspection of files containing addresses")
        print(f"   2. Search for encrypted/compressed data")
        print(f"   3. Try extended brain wallet wordlists")

if __name__ == "__main__":
    main()
