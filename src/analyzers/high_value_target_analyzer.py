#!/usr/bin/env python3
"""
High-Value Target Wallet Recovery Tool
Deep analysis and private key extraction for 0x8390a1da07e376ef7add4be859ba74fb83aa02d5 (11.0565 ETH)
"""

import os
import json
import re
import subprocess
import time
from typing import Dict, List, Any, Optional

# Configuration
TARGET_ADDRESS = "0x8390a1da07e376ef7add4be859ba74fb83aa02d5"
TARGET_BALANCE_ETH = "11.0565157585102"
TARGET_VALUE_USD = 27641  # Approximately
DATA_DIR = "/home/admin/wallet_tool/net607"
REPORT_FILE = "high_value_target_recovery.json"

class HighValueTargetAnalyzer:
    def __init__(self):
        self.results = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            "target": {
                "address": TARGET_ADDRESS,
                "balance_eth": TARGET_BALANCE_ETH,
                "value_usd": TARGET_VALUE_USD,
                "priority": "HIGHEST_VALUE"
            },
            "source_files": [],
            "context_analysis": {},
            "potential_keys": [],
            "form_data": [],
            "credentials": [],
            "recovery_candidates": []
        }
    
    def find_source_files(self) -> List[str]:
        """Find all files containing the target address"""
        source_files = []
        
        try:
            # Use grep to find files
            result = subprocess.run([
                "find", DATA_DIR, "-name", "*.txt", "-exec", 
                "grep", "-l", TARGET_ADDRESS.lower(), "{}", "+"
            ], capture_output=True, text=True, timeout=60)
            
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        source_files.append(line.strip())
            
        except Exception as e:
            print(f"Error finding source files: {e}")
        
        return source_files[:20]  # Limit to first 20 files
    
    def extract_file_context(self, file_path: str) -> Dict[str, Any]:
        """Extract detailed context from a file containing the target address"""
        context = {
            "file_path": file_path,
            "file_type": self.classify_file_type(file_path),
            "target_lines": [],
            "surrounding_data": [],
            "potential_keys": [],
            "form_fields": [],
            "urls": [],
            "timestamps": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Find lines containing the target address
            target_line_nums = []
            for i, line in enumerate(lines):
                if TARGET_ADDRESS.lower() in line.lower():
                    target_line_nums.append(i)
                    context["target_lines"].append({
                        "line_number": i + 1,
                        "content": line.strip()
                    })
            
            # Extract context around each target line
            for line_num in target_line_nums:
                start = max(0, line_num - 25)
                end = min(len(lines), line_num + 26)
                
                surrounding = []
                for i in range(start, end):
                    line_content = lines[i].strip()
                    line_data = {
                        "line": i + 1,
                        "distance": i - line_num,
                        "content": line_content,
                        "analysis": self.analyze_line_content(line_content)
                    }
                    surrounding.append(line_data)
                    
                    # Check for potential private keys
                    if self.is_potential_private_key(line_content):
                        key_info = {
                            "source_file": file_path,
                            "line": i + 1,
                            "distance_from_target": i - line_num,
                            "content": line_content[:100] + "..." if len(line_content) > 100 else line_content,
                            "type": self.classify_key_type(line_content),
                            "confidence": self.calculate_confidence(line_content, file_path)
                        }
                        context["potential_keys"].append(key_info)
                        self.results["potential_keys"].append(key_info)
                
                context["surrounding_data"].append({
                    "target_line": line_num + 1,
                    "context_range": f"{start + 1}-{end}",
                    "surrounding_lines": surrounding
                })
            
            # Extract URLs, form fields, and other relevant data
            self.extract_additional_data(lines, context)
            
        except Exception as e:
            context["error"] = str(e)
        
        return context
    
    def classify_file_type(self, file_path: str) -> str:
        """Classify the type of file based on path"""
        file_path_lower = file_path.lower()
        
        if "autofills" in file_path_lower:
            return "browser_autofill"
        elif "passwords" in file_path_lower:
            return "browser_passwords"
        elif "history" in file_path_lower:
            return "browser_history"
        elif "cookies" in file_path_lower:
            return "browser_cookies"
        elif "brute" in file_path_lower:
            return "brute_force_data"
        elif "clipboard" in file_path_lower:
            return "clipboard_history"
        elif "discord" in file_path_lower:
            return "discord_tokens"
        elif "steam" in file_path_lower:
            return "steam_tokens"
        else:
            return "unknown"
    
    def analyze_line_content(self, line: str) -> Dict[str, Any]:
        """Analyze a line for various wallet-related patterns"""
        analysis = {
            "contains_hex": bool(re.search(r'[0-9a-fA-F]{32,}', line)),
            "contains_email": bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', line)),
            "contains_url": bool(re.search(r'https?://[^\s]+', line)),
            "contains_key_pattern": self.is_potential_private_key(line),
            "contains_password": any(keyword in line.lower() for keyword in ['password', 'pass', 'pwd', 'key']),
            "contains_wallet_terms": any(term in line.lower() for term in ['wallet', 'ethereum', 'metamask', 'seed', 'mnemonic', 'private'])
        }
        return analysis
    
    def extract_additional_data(self, lines: List[str], context: Dict[str, Any]):
        """Extract URLs, form fields, timestamps, etc."""
        for i, line in enumerate(lines):
            # URLs
            urls = re.findall(r'https?://[^\s]+', line)
            for url in urls:
                if url not in [u['url'] for u in context['urls']]:
                    context['urls'].append({
                        "line": i + 1,
                        "url": url
                    })
            
            # Email addresses
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', line)
            for email in emails:
                context['form_fields'].append({
                    "line": i + 1,
                    "type": "email",
                    "value": email
                })
            
            # Timestamps
            timestamp_patterns = [
                r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}',
                r'\d{10,13}',  # Unix timestamps
            ]
            for pattern in timestamp_patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    context['timestamps'].append({
                        "line": i + 1,
                        "timestamp": match
                    })
    
    def is_potential_private_key(self, text: str) -> bool:
        """Enhanced private key detection"""
        text = text.strip()
        
        # Ethereum private key (64 hex chars)
        if re.match(r'^[0-9a-fA-F]{64}$', text):
            return True
        
        # Ethereum private key with 0x prefix
        if re.match(r'^0x[0-9a-fA-F]{64}$', text):
            return True
        
        # Bitcoin WIF format
        if len(text) in [51, 52] and text[0] in ['5', 'K', 'L']:
            return True
        
        # Base64-encoded keys (common lengths)
        if len(text) in [44, 64, 88] and re.match(r'^[A-Za-z0-9+/=]+$', text):
            return True
        
        # Other hex patterns that could be keys
        if len(text) >= 32 and re.match(r'^[0-9a-fA-F]+$', text):
            return True
        
        return False
    
    def classify_key_type(self, text: str) -> str:
        """Classify the type of potential private key"""
        text = text.strip()
        
        if re.match(r'^0x[0-9a-fA-F]{64}$', text):
            return "ethereum_private_key"
        elif re.match(r'^[0-9a-fA-F]{64}$', text):
            return "raw_hex_64"
        elif text.startswith('5'):
            return "bitcoin_wif_uncompressed"
        elif text.startswith(('K', 'L')):
            return "bitcoin_wif_compressed"
        elif re.match(r'^[A-Za-z0-9+/=]+$', text):
            return "base64_encoded"
        else:
            return "unknown_hex"
    
    def calculate_confidence(self, key_text: str, file_path: str) -> int:
        """Calculate confidence score for a potential private key"""
        confidence = 50  # Base confidence
        
        # File type bonuses
        if "autofills" in file_path.lower():
            confidence += 30
        elif "passwords" in file_path.lower():
            confidence += 25
        elif "clipboard" in file_path.lower():
            confidence += 20
        
        # Key format bonuses
        if re.match(r'^0x[0-9a-fA-F]{64}$', key_text):
            confidence += 25
        elif re.match(r'^[0-9a-fA-F]{64}$', key_text):
            confidence += 20
        
        # Length penalties for very long strings (less likely to be keys)
        if len(key_text) > 100:
            confidence -= 15
        
        return min(100, max(0, confidence))
    
    def run_analysis(self):
        """Execute the complete high-value target analysis"""
        print(f"🎯 ANALYZING HIGH-VALUE TARGET: {TARGET_ADDRESS}")
        print(f"💰 Value: {TARGET_BALANCE_ETH} ETH (~${TARGET_VALUE_USD:,})")
        print("=" * 70)
        
        # Find source files
        source_files = self.find_source_files()
        self.results["source_files"] = source_files
        
        print(f"\n📁 FOUND TARGET ADDRESS IN {len(source_files)} FILES")
        print("-" * 50)
        
        # Analyze each source file
        for i, file_path in enumerate(source_files, 1):
            print(f"\n{i:2d}. 📄 {os.path.basename(file_path)}")
            print(f"     File Type: {self.classify_file_type(file_path)}")
            
            context = self.extract_file_context(file_path)
            self.results["context_analysis"][file_path] = context
            
            if context.get("potential_keys"):
                print(f"     🔑 Found {len(context['potential_keys'])} potential key(s)")
                for key in context["potential_keys"]:
                    print(f"        • {key['type']} (confidence: {key['confidence']}%) at line {key['line']}")
        
        # Summary
        total_keys = len(self.results["potential_keys"])
        print(f"\n🔍 ANALYSIS SUMMARY")
        print("-" * 30)
        print(f"Source files analyzed: {len(source_files)}")
        print(f"Potential private keys found: {total_keys}")
        
        if total_keys > 0:
            # Sort by confidence
            sorted_keys = sorted(self.results["potential_keys"], 
                               key=lambda x: x["confidence"], reverse=True)
            
            print(f"\n🏆 TOP RECOVERY CANDIDATES:")
            for i, key in enumerate(sorted_keys[:10], 1):
                print(f"{i:2d}. {key['type']} (confidence: {key['confidence']}%)")
                print(f"     Source: {os.path.basename(key['source_file'])}")
                print(f"     Line: {key['line']} (distance: {key['distance_from_target']})")
                print(f"     Preview: {key['content'][:80]}...")
                print()
        
        # Save results
        with open(REPORT_FILE, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"💾 Detailed analysis saved to: {REPORT_FILE}")
        
        if total_keys > 0:
            print(f"\n🚀 NEXT STEPS:")
            print("1. Test the highest confidence private key candidates")
            print("2. Run key derivation tests on potential keys")
            print("3. Check for encrypted or encoded variants")
            print("4. Execute recovery transaction if key found")
        else:
            print(f"\n❌ NO PRIVATE KEYS FOUND IN CONTEXT")
            print("Consider searching for:")
            print("• Encrypted wallet files")
            print("• Browser keystore data")
            print("• Related email/password combinations")
        
        return self.results

def main():
    analyzer = HighValueTargetAnalyzer()
    results = analyzer.run_analysis()
    
    # Return summary for follow-up
    return {
        "target_address": TARGET_ADDRESS,
        "source_files_count": len(results["source_files"]),
        "potential_keys_count": len(results["potential_keys"]),
        "top_candidates": sorted(results["potential_keys"], 
                               key=lambda x: x["confidence"], reverse=True)[:5]
    }

if __name__ == "__main__":
    summary = main()
    print(f"\n✅ Analysis complete. Ready for key testing phase.")
