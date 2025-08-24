#!/usr/bin/env python3
"""
Next Target Analysis - High-Value Wallet Investigation
Focusing on: 0x8390a1da07e376ef7add4be859ba74fb83aa02d5 (11.0565 ETH)
"""

import os
import re
import json
from datetime import datetime
from eth_keys import keys

class NextTargetAnalyzer:
    def __init__(self):
        # High-value target information
        self.target_address = "0x8390a1da07e376ef7add4be859ba74fb83aa02d5"
        self.target_balance = 11.0565157585101993
        self.target_value_usd = 27641  # Approximate at current ETH price
        
        # All our discovered funded addresses for reference
        self.funded_addresses = {
            "0x8390a1da07e376ef7add4be859ba74fb83aa02d5": 11.0565157585101993,
            "0x2859e4544c4bb03966803b044a93563bd2d0dd4d": 4.005814613262247463,
            "0xba2ae424d960c26247dd6c32edc70b295c744c43": 4.516350432918525173,
            "0xf03f0a004ab150bf46d8e2df10b7ebd89ed39f0e": 1.022336283937304673,
            "0xa462bde22d98335e18a21555b6752db93a937cff": 0.801890924956108765,
            "0x683a4ac99e65200921f556a19dadf4b0214b5938": 0.759441365469564,
            "0x6e59e2a98d12f45ab5872942fe45a1036b1ea9c9": 0.296807,  # Previous target
            "0x159cdaf78be31e730d9e1330adfcfbb79a5fdb95": 0.541373,
            "0x8bd210f4a679eced866b725a85ba75a2c158f651": 0.194946
        }
        
        self.results = []
    
    def analyze_target_context(self):
        """Analyze the context where this high-value target was found"""
        print("🎯 NEXT TARGET: HIGH-VALUE WALLET ANALYSIS")
        print("=" * 60)
        print(f"Target Address: {self.target_address}")
        print(f"Balance: {self.target_balance} ETH")
        print(f"USD Value: ~${self.target_value_usd:,}")
        print(f"Priority: HIGHEST VALUE TARGET")
        print("-" * 60)
        
        # First, let's find where this address was discovered
        self.locate_target_source()
        
    def locate_target_source(self):
        """Find the source files containing our new target"""
        print("\n🔍 LOCATING TARGET IN SOURCE DATA")
        print("-" * 40)
        
        target_files = []
        search_paths = [
            "/home/admin/Downloads/net605/",
            "/home/admin/Downloads/net501/",
            "/home/admin/wallet_tool/"
        ]
        
        files_found = 0
        
        for search_path in search_paths:
            if os.path.exists(search_path):
                print(f"Searching: {search_path}")
                
                for root, dirs, files in os.walk(search_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        # Skip binary files
                        if any(ext in file.lower() for ext in ['.exe', '.dll', '.bin', '.jpg', '.png']):
                            continue
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            
                            # Check if our target address is in this file
                            if self.target_address.lower() in content.lower():
                                files_found += 1
                                
                                print(f"  ✅ Found in: {file_path}")
                                
                                # Extract context around the address
                                self.extract_target_context(file_path, content)
                                
                                target_files.append(file_path)
                                
                                if files_found >= 5:  # Limit to first 5 files for now
                                    break
                        
                        except Exception:
                            continue
                    
                    if files_found >= 5:
                        break
                
                if files_found >= 5:
                    break
        
        print(f"\n📊 Target found in {files_found} files")
        return target_files
    
    def extract_target_context(self, file_path, content):
        """Extract detailed context around the target address"""
        print(f"\n📄 ANALYZING: {os.path.basename(file_path)}")
        
        lines = content.split('\n')
        target_lines = []
        
        # Find all lines containing our target
        for i, line in enumerate(lines):
            if self.target_address.lower() in line.lower():
                target_lines.append(i+1)
        
        print(f"  Found on {len(target_lines)} lines: {target_lines}")
        
        # Extract context for each occurrence
        for line_num in target_lines[:3]:  # First 3 occurrences
            start_line = max(0, line_num - 10)
            end_line = min(len(lines), line_num + 10)
            
            print(f"\n  📍 Context around line {line_num}:")
            for i in range(start_line, end_line):
                prefix = "  >>> " if i+1 == line_num else "      "
                print(f"{prefix}Line {i+1:4d}: {lines[i].strip()}")
            
            # Look for potential private keys or wallet data in nearby lines
            self.scan_for_wallet_data_nearby(lines, line_num)
    
    def scan_for_wallet_data_nearby(self, lines, target_line):
        """Scan for potential wallet data near the target address"""
        print(f"\n  🔍 Scanning for wallet data near line {target_line}:")
        
        # Check 20 lines before and after
        start_scan = max(0, target_line - 20)
        end_scan = min(len(lines), target_line + 20)
        
        potential_keys = []
        
        for i in range(start_scan, end_scan):
            line = lines[i].strip()
            
            # Look for hex patterns that could be private keys
            hex_64_patterns = re.findall(r'\b[0-9a-fA-F]{64}\b', line)
            for pattern in hex_64_patterns:
                potential_keys.append({
                    'type': 'hex_64',
                    'line': i+1,
                    'value': pattern,
                    'distance': abs(i+1 - target_line)
                })
            
            # Look for base64 patterns
            base64_patterns = re.findall(r'\b[A-Za-z0-9+/]{32,}={0,2}\b', line)
            for pattern in base64_patterns:
                if len(pattern) >= 32:
                    potential_keys.append({
                        'type': 'base64',
                        'line': i+1,
                        'value': pattern,
                        'distance': abs(i+1 - target_line)
                    })
            
            # Look for seed phrase patterns (12+ words)
            words = line.split()
            if len(words) >= 12 and all(word.isalpha() and len(word) > 2 for word in words[:12]):
                potential_keys.append({
                    'type': 'seed_phrase',
                    'line': i+1,
                    'value': ' '.join(words[:12]),
                    'distance': abs(i+1 - target_line)
                })
        
        # Sort by distance from target
        potential_keys.sort(key=lambda x: x['distance'])
        
        print(f"    Found {len(potential_keys)} potential wallet data patterns:")
        for key in potential_keys[:5]:  # Show first 5
            print(f"    • {key['type']} at line {key['line']} (distance: {key['distance']})")
            print(f"      {key['value'][:50]}{'...' if len(key['value']) > 50 else ''}")
            
            # Test if this could be a private key for our target
            if key['type'] == 'hex_64':
                if self.test_private_key(key['value']):
                    print(f"    🎯 POTENTIAL MATCH FOUND!")
                    return key['value']
        
        return None
    
    def test_private_key(self, private_key_hex):
        """Test if a private key generates our target address"""
        try:
            if private_key_hex.startswith('0x'):
                private_key_hex = private_key_hex[2:]
            
            if len(private_key_hex) != 64:
                return False
            
            # Validate it's valid hex
            int(private_key_hex, 16)
            
            private_key = keys.PrivateKey(bytes.fromhex(private_key_hex))
            derived_address = private_key.public_key.to_checksum_address()
            
            if derived_address.lower() == self.target_address.lower():
                print(f"    🎯 PRIVATE KEY MATCH FOUND!")
                print(f"    Private Key: {private_key_hex}")
                print(f"    Address: {derived_address}")
                print(f"    Value: {self.target_balance} ETH (~${self.target_value_usd:,})")
                return True
            
            return False
            
        except Exception:
            return False
    
    def analyze_file_patterns(self):
        """Analyze file patterns where high-value addresses are found"""
        print(f"\n📊 HIGH-VALUE ADDRESS DISTRIBUTION ANALYSIS")
        print("-" * 50)
        
        # Load our comprehensive scan results
        results_file = "/home/admin/wallet_tool/comprehensive_recheck_results_20250814_094229.json"
        
        if os.path.exists(results_file):
            try:
                with open(results_file, 'r') as f:
                    scan_data = json.load(f)
                
                print(f"Loaded scan data with {len(scan_data)} addresses")
                
                # Find our target in the scan data
                target_entry = None
                for entry in scan_data:
                    if entry.get('address', '').lower() == self.target_address.lower():
                        target_entry = entry
                        break
                
                if target_entry:
                    print(f"\n🎯 TARGET FOUND IN SCAN DATA:")
                    print(f"  Address: {target_entry.get('address')}")
                    print(f"  Balance: {target_entry.get('balance_eth')} ETH")
                    print(f"  API Used: {target_entry.get('api_used')}")
                    print(f"  Has Balance: {target_entry.get('has_balance')}")
                    
                    # This tells us the address was extracted from our data
                    print(f"\n✅ Target confirmed as extracted from dataset")
                    print(f"🎯 Need to find source file containing this address")
                
            except Exception as e:
                print(f"❌ Error loading scan results: {e}")
        
        # Now search for the specific source file
        self.find_exact_source_file()
    
    def find_exact_source_file(self):
        """Find the exact source file containing our target address"""
        print(f"\n🔍 FINDING EXACT SOURCE FILE")
        print("-" * 30)
        
        # Common locations for wallet data
        search_locations = [
            "/home/admin/Downloads/net605/",
            "/home/admin/Downloads/net501/",
        ]
        
        # File types likely to contain wallet addresses
        target_files = ['Autofills.txt', 'Passwords.txt', 'History.txt', 'Storage.txt', 'LocalStorage.txt']
        
        matches_found = []
        
        for search_path in search_locations:
            if not os.path.exists(search_path):
                continue
                
            print(f"Searching in: {search_path}")
            
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    if any(target_file.lower() in file.lower() for target_file in target_files):
                        file_path = os.path.join(root, file)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            
                            if self.target_address.lower() in content.lower():
                                matches_found.append(file_path)
                                print(f"  ✅ Found in: {file_path}")
                                
                                # Extract detailed context from this file
                                self.deep_analysis_of_source_file(file_path)
                        
                        except Exception:
                            continue
        
        print(f"\n📊 Target found in {len(matches_found)} source files")
        return matches_found
    
    def deep_analysis_of_source_file(self, file_path):
        """Perform deep analysis of the file containing our target"""
        print(f"\n🔬 DEEP ANALYSIS: {os.path.basename(file_path)}")
        print("-" * 40)
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            print(f"File size: {len(content)} characters, {len(lines)} lines")
            
            # Find all occurrences of our target
            target_line_numbers = []
            for i, line in enumerate(lines):
                if self.target_address.lower() in line.lower():
                    target_line_numbers.append(i+1)
            
            print(f"Target appears on lines: {target_line_numbers}")
            
            # Analyze each occurrence
            for line_num in target_line_numbers:
                print(f"\n📍 ANALYZING OCCURRENCE AT LINE {line_num}:")
                
                # Get extended context (50 lines before and after)
                start = max(0, line_num - 50)
                end = min(len(lines), line_num + 50)
                
                context_block = lines[start:end]
                
                # Look for patterns in this context block
                self.analyze_context_block(context_block, line_num - start)
        
        except Exception as e:
            print(f"❌ Error analyzing file: {e}")
    
    def analyze_context_block(self, context_lines, target_index):
        """Analyze a block of context around the target address"""
        print(f"    Analyzing {len(context_lines)} lines of context...")
        
        # Look for form fields, key-value pairs, and wallet-related terms
        wallet_terms = ['private', 'key', 'seed', 'mnemonic', 'wallet', 'recovery', 'backup', 'export']
        form_patterns = []
        potential_credentials = []
        
        for i, line in enumerate(context_lines):
            line_clean = line.strip()
            
            # Check for form field patterns
            if 'FORM:' in line_clean or 'VALUE:' in line_clean:
                form_patterns.append((i, line_clean))
            
            # Check for wallet-related terms
            if any(term in line_clean.lower() for term in wallet_terms):
                potential_credentials.append((i, line_clean))
            
            # Check for hex patterns (potential private keys)
            hex_64_matches = re.findall(r'\b[0-9a-fA-F]{64}\b', line_clean)
            if hex_64_matches:
                for hex_match in hex_64_matches:
                    print(f"    🔑 Potential private key at line {i}: {hex_match}")
                    if self.test_private_key(hex_match):
                        return hex_match
        
        # Show relevant form patterns
        if form_patterns:
            print(f"    📝 Found {len(form_patterns)} form-related lines")
            for i, (line_idx, line_content) in enumerate(form_patterns[:10]):
                distance = abs(line_idx - target_index)
                print(f"      Line {line_idx} (distance: {distance}): {line_content[:60]}...")
        
        # Show potential credentials
        if potential_credentials:
            print(f"    🔐 Found {len(potential_credentials)} wallet-related lines")
            for i, (line_idx, line_content) in enumerate(potential_credentials[:5]):
                distance = abs(line_idx - target_index)
                print(f"      Line {line_idx} (distance: {distance}): {line_content[:60]}...")
    
    def generate_next_target_report(self):
        """Generate comprehensive report for the next target"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'target_address': self.target_address,
            'target_balance_eth': self.target_balance,
            'target_value_usd': self.target_value_usd,
            'priority': 'HIGHEST_VALUE',
            'analysis_status': 'IN_PROGRESS',
            'next_steps': [
                'Complete source file analysis',
                'Extract wallet context and credentials',
                'Test discovered private key candidates',
                'Develop recovery strategy',
                'Execute recovery if key found'
            ]
        }
        
        with open('/home/admin/wallet_tool/next_target_analysis.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Analysis report saved to: next_target_analysis.json")
        return report
    
    def run_next_target_analysis(self):
        """Execute complete analysis of next target"""
        self.analyze_target_context()
        self.analyze_file_patterns()
        self.generate_next_target_report()
        
        print(f"\n🎯 NEXT TARGET ANALYSIS SUMMARY")
        print("=" * 50)
        print(f"Target: {self.target_address}")
        print(f"Value: {self.target_balance} ETH (~${self.target_value_usd:,})")
        print(f"Status: Source files located, analyzing for private keys")
        print(f"Next: Deep extraction of wallet credentials")

if __name__ == "__main__":
    analyzer = NextTargetAnalyzer()
    analyzer.run_next_target_analysis()
