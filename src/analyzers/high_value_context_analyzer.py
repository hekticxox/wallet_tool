#!/usr/bin/env python3
"""
High-Value Address Context Analyzer
Since the LevelDB file binary/097190.ldb isn't available in our workspace,
analyze existing extracted data for any additional context or keys related to
0x8390a1da07e376ef7add4be859ba74fb83aa02d5 (11.0565 ETH)
"""

import os
import json
import re
import time
from typing import Dict, List, Any, Optional
from web3 import Web3
from eth_account import Account

# Configuration
TARGET_ADDRESS = "0x8390a1da07e376ef7add4be859ba74fb83aa02d5"
REPORT_FILE = "high_value_context_analysis.json"

class HighValueContextAnalyzer:
    def __init__(self):
        self.results = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            "target_address": TARGET_ADDRESS,
            "target_balance": "11.0565 ETH",
            "source_file": "binary/097190.ldb",
            "analysis_complete": False,
            "context_sources": [],
            "private_key_candidates": [],
            "related_addresses": [],
            "recovery_strategies": []
        }
        
        self.web3 = Web3()
    
    def find_all_data_files(self) -> List[str]:
        """Find all JSON and text files that might contain relevant data"""
        data_files = []
        
        # Look for common data file patterns
        patterns = [
            "*.json",
            "*wallet*",
            "*private*",
            "*key*",
            "*extraction*",
            "*results*",
            "*.txt"
        ]
        
        for pattern in patterns:
            try:
                import glob
                files = glob.glob(pattern, recursive=True)
                data_files.extend(files)
            except:
                pass
        
        # Remove duplicates and sort
        data_files = sorted(list(set(data_files)))
        
        print(f"✅ Found {len(data_files)} potential data files")
        return data_files
    
    def analyze_file_for_address(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single file for references to our target address"""
        analysis = {
            "file": file_path,
            "contains_target": False,
            "references": [],
            "context": [],
            "nearby_keys": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check if target address is present
            if TARGET_ADDRESS.lower() in content.lower():
                analysis["contains_target"] = True
                
                # Find all references with context
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if TARGET_ADDRESS.lower() in line.lower():
                        # Get surrounding context
                        start_idx = max(0, i - 3)
                        end_idx = min(len(lines), i + 4)
                        context_lines = lines[start_idx:end_idx]
                        
                        analysis["references"].append({
                            "line_number": i + 1,
                            "line_content": line.strip(),
                            "context": context_lines
                        })
                
                # Look for nearby private key patterns
                hex_patterns = re.finditer(r'\b[a-fA-F0-9]{64}\b', content)
                for match in hex_patterns:
                    key_candidate = match.group()
                    
                    # Check if this is near our address in the text
                    address_pos = content.lower().find(TARGET_ADDRESS.lower())
                    key_pos = match.start()
                    distance = abs(address_pos - key_pos)
                    
                    if distance < 1000:  # Within 1000 characters
                        analysis["nearby_keys"].append({
                            "key_candidate": key_candidate,
                            "distance_from_address": distance,
                            "position": key_pos
                        })
        
        except Exception as e:
            analysis["error"] = str(e)
        
        return analysis
    
    def test_private_key_candidates(self, candidates: List[str]) -> List[Dict]:
        """Test private key candidates against our target address"""
        recovery_candidates = []
        
        print(f"\n🔑 TESTING {len(candidates)} PRIVATE KEY CANDIDATES")
        print("-" * 50)
        
        for candidate in candidates:
            try:
                # Normalize key format
                key = candidate.strip()
                if key.startswith("0x"):
                    key = key[2:]
                
                if len(key) != 64:
                    continue
                
                # Test if this key generates our target address
                account = Account.from_key(key)
                generated_address = account.address
                
                print(f"Testing: {key[:16]}... -> {generated_address}")
                
                if generated_address.lower() == TARGET_ADDRESS.lower():
                    recovery_candidate = {
                        "private_key": key,
                        "address": generated_address,
                        "match_type": "EXACT_MATCH",
                        "recovery_ready": True
                    }
                    recovery_candidates.append(recovery_candidate)
                    
                    print(f"🎉 EXACT MATCH FOUND!")
                    print(f"Private Key: {key}")
                    print(f"Address: {generated_address}")
                    
                    return recovery_candidates  # Return immediately on exact match
                
            except Exception as e:
                continue
        
        return recovery_candidates
    
    def search_for_related_patterns(self, all_data: str) -> Dict[str, Any]:
        """Search for patterns that might be related to our target address"""
        patterns = {
            "ethereum_addresses": re.findall(r'\b0x[a-fA-F0-9]{40}\b', all_data),
            "private_keys": re.findall(r'\b[a-fA-F0-9]{64}\b', all_data),
            "mnemonic_words": re.findall(r'\b[a-z]+\s+[a-z]+\s+[a-z]+\s+[a-z]+\s+[a-z]+\s+[a-z]+', all_data.lower()),
            "json_objects": re.findall(r'\{[^}]*"[^"]*"[^}]*\}', all_data),
            "base64_patterns": re.findall(r'\b[A-Za-z0-9+/]{32,}={0,2}\b', all_data)
        }
        
        return patterns
    
    def generate_recovery_strategies(self) -> List[Dict[str, str]]:
        """Generate specific recovery strategies for this high-value address"""
        strategies = [
            {
                "strategy": "LevelDB Direct Access",
                "description": "Locate and directly access the binary/097190.ldb file that contains this address",
                "action": "Search for LevelDB files in original data source, use hex editor or LevelDB tools to extract raw data",
                "priority": "HIGH"
            },
            {
                "strategy": "HD Wallet Derivation",
                "description": "Test HD wallet derivation paths since this address might be derived from a master seed",
                "action": "Test common derivation paths (m/44'/60'/0'/0/x) with any discovered seed phrases",
                "priority": "HIGH"
            },
            {
                "strategy": "Browser Wallet Recovery",
                "description": "Check if this address was from a browser extension wallet",
                "action": "Look for MetaMask, Phantom, or other wallet extension data in browser profiles",
                "priority": "MEDIUM"
            },
            {
                "strategy": "Encrypted Private Key Recovery",
                "description": "The private key might be encrypted in the database",
                "action": "Search for encrypted blobs near the address, attempt decryption with common passwords",
                "priority": "MEDIUM"
            },
            {
                "strategy": "Address Index Correlation",
                "description": "Find other addresses from the same wallet/source and check their private keys",
                "action": "Analyze other addresses from binary/097190.ldb, look for patterns",
                "priority": "MEDIUM"
            }
        ]
        
        return strategies
    
    def run_analysis(self) -> Dict[str, Any]:
        """Execute the complete context analysis"""
        print(f"🔍 HIGH-VALUE ADDRESS CONTEXT ANALYSIS")
        print(f"Target: {TARGET_ADDRESS}")
        print(f"Value: 11.0565 ETH (~$27,641)")
        print(f"Source: binary/097190.ldb")
        print("=" * 60)
        
        # Find all data files
        print(f"\n📂 SEARCHING FOR DATA FILES")
        print("-" * 30)
        data_files = self.find_all_data_files()
        
        # Analyze each file for our target address
        print(f"\n🔍 ANALYZING FILES FOR TARGET ADDRESS")
        print("-" * 40)
        
        all_analyses = []
        all_private_key_candidates = []
        all_data = ""
        
        for file_path in data_files:
            if os.path.exists(file_path):
                analysis = self.analyze_file_for_address(file_path)
                
                if analysis["contains_target"]:
                    print(f"✅ Found target in: {file_path}")
                    print(f"   References: {len(analysis['references'])}")
                    print(f"   Nearby keys: {len(analysis['nearby_keys'])}")
                    
                    # Collect private key candidates
                    for nearby_key in analysis["nearby_keys"]:
                        all_private_key_candidates.append(nearby_key["key_candidate"])
                
                all_analyses.append(analysis)
                self.results["context_sources"].append(analysis)
                
                # Add file content to combined data
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        all_data += f.read() + "\n"
                except:
                    pass
        
        # Test private key candidates
        if all_private_key_candidates:
            print(f"\n🔑 TESTING PRIVATE KEY CANDIDATES")
            print("-" * 35)
            
            unique_candidates = list(set(all_private_key_candidates))
            recovery_results = self.test_private_key_candidates(unique_candidates)
            
            self.results["private_key_candidates"] = unique_candidates
            
            if recovery_results:
                print(f"\n🚀 RECOVERY SUCCESS!")
                self.results["recovery_candidates"] = recovery_results
                self.results["analysis_complete"] = True
                
                # Save results immediately
                with open(REPORT_FILE, 'w') as f:
                    json.dump(self.results, f, indent=2)
                
                return recovery_results[0]  # Return the first match
        
        # Search for related patterns in all data
        print(f"\n🔍 SEARCHING FOR RELATED PATTERNS")
        print("-" * 35)
        patterns = self.search_for_related_patterns(all_data)
        
        print(f"Ethereum addresses found: {len(patterns['ethereum_addresses'])}")
        print(f"Private key patterns: {len(patterns['private_keys'])}")
        print(f"Possible mnemonics: {len(patterns['mnemonic_words'])}")
        
        self.results["patterns"] = {
            "ethereum_addresses": len(patterns["ethereum_addresses"]),
            "private_keys": len(patterns["private_keys"]),
            "mnemonic_words": len(patterns["mnemonic_words"])
        }
        
        # Generate recovery strategies
        print(f"\n📋 GENERATING RECOVERY STRATEGIES")
        print("-" * 35)
        strategies = self.generate_recovery_strategies()
        self.results["recovery_strategies"] = strategies
        
        for i, strategy in enumerate(strategies, 1):
            print(f"{i}. {strategy['strategy']} ({strategy['priority']})")
            print(f"   {strategy['description']}")
            print()
        
        # Save full results
        with open(REPORT_FILE, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Analysis saved to: {REPORT_FILE}")
        
        # Summary
        files_with_target = sum(1 for a in all_analyses if a["contains_target"])
        total_references = sum(len(a["references"]) for a in all_analyses)
        
        print(f"\n📊 ANALYSIS SUMMARY")
        print("-" * 20)
        print(f"Files analyzed: {len(data_files)}")
        print(f"Files containing target: {files_with_target}")
        print(f"Total references found: {total_references}")
        print(f"Private key candidates: {len(unique_candidates) if 'unique_candidates' in locals() else 0}")
        print(f"Recovery strategies: {len(strategies)}")
        
        if not recovery_results if 'recovery_results' in locals() else True:
            print(f"\n❌ No private key found in current data")
            print(f"Next steps:")
            print(f"1. Locate original binary/097190.ldb file")
            print(f"2. Use LevelDB tools for direct access")
            print(f"3. Check browser wallet extension data")
            print(f"4. Test HD wallet derivation paths")
        
        return self.results

def main():
    analyzer = HighValueContextAnalyzer()
    result = analyzer.run_analysis()
    
    return result

if __name__ == "__main__":
    result = main()
    
    if isinstance(result, dict) and result.get("recovery_ready"):
        print(f"\n🎯 RECOVERY READY!")
        print(f"Private Key: {result['private_key']}")
        print(f"Address: {result['address']}")
    else:
        print(f"\n🔍 Analysis complete. Check the recovery strategies for next steps.")
