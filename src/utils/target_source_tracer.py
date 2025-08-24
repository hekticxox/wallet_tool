#!/usr/bin/env python3
"""
Source File Tracer for High-Value Target
Find exact source files containing the target address for recovery analysis
"""

import os
import json
import subprocess
import time
from typing import Dict, List, Optional, Any

# Configuration
TARGET_ADDRESS = "0x8390a1da07e376ef7add4be859ba74fb83aa02d5"
SEARCH_DIRS = [
    "/home/admin/Downloads/net605",
    "/home/admin/Downloads/net501"
]
REPORT_FILE = "target_source_trace.json"

class SourceTracer:
    def __init__(self):
        self.results = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            "target_address": TARGET_ADDRESS,
            "source_files": [],
            "context_extracts": {},
            "potential_keys": [],
            "error_log": []
        }
    
    def search_files(self, directory: str) -> List[Dict[str, Any]]:
        """Search for target address in all files in directory"""
        found_files = []
        
        if not os.path.exists(directory):
            self.results["error_log"].append(f"Directory not found: {directory}")
            return found_files
        
        try:
            # Use ripgrep for fast search
            cmd = [
                "rg", "--json", "--ignore-case", "--max-count", "10",
                TARGET_ADDRESS.lower(), directory
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if data.get("type") == "match":
                            file_info = {
                                "file_path": data["data"]["path"]["text"],
                                "line_number": data["data"]["line_number"],
                                "line_text": data["data"]["lines"]["text"],
                                "directory": directory
                            }
                            found_files.append(file_info)
                    except json.JSONDecodeError:
                        continue
            
        except subprocess.TimeoutExpired:
            self.results["error_log"].append(f"Search timeout in {directory}")
        except Exception as e:
            self.results["error_log"].append(f"Search error in {directory}: {str(e)}")
        
        return found_files
    
    def extract_context(self, file_path: str, line_num: int, context_lines: int = 20) -> Dict[str, Any]:
        """Extract context around the target address"""
        context = {
            "file_path": file_path,
            "target_line": line_num,
            "context": [],
            "potential_keys": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            start_line = max(0, line_num - context_lines - 1)
            end_line = min(len(lines), line_num + context_lines)
            
            for i in range(start_line, end_line):
                line_data = {
                    "line_number": i + 1,
                    "content": lines[i].strip(),
                    "is_target": i + 1 == line_num
                }
                context["context"].append(line_data)
                
                # Look for potential private keys in nearby lines
                line_content = lines[i].strip()
                if self.is_potential_private_key(line_content):
                    context["potential_keys"].append({
                        "line": i + 1,
                        "content": line_content[:100] + "..." if len(line_content) > 100 else line_content,
                        "type": self.identify_key_type(line_content)
                    })
            
        except Exception as e:
            context["error"] = str(e)
        
        return context
    
    def is_potential_private_key(self, text: str) -> bool:
        """Check if text could be a private key"""
        text_clean = text.strip().lower()
        
        # Hex private keys (64 chars)
        if len(text_clean) == 64 and all(c in '0123456789abcdef' for c in text_clean):
            return True
        
        # Hex with 0x prefix
        if text_clean.startswith('0x') and len(text_clean) == 66:
            return all(c in '0123456789abcdef' for c in text_clean[2:])
        
        # Base64-like strings
        if len(text_clean) > 40 and text_clean.replace('+', '').replace('/', '').replace('=', '').isalnum():
            return True
        
        # WIF format (Bitcoin style)
        if len(text_clean) in [51, 52] and (text_clean.startswith('5') or text_clean.startswith('K') or text_clean.startswith('L')):
            return True
        
        return False
    
    def identify_key_type(self, text: str) -> str:
        """Identify the type of potential key"""
        text_clean = text.strip().lower()
        
        if text_clean.startswith('0x') and len(text_clean) == 66:
            return "ethereum_hex"
        elif len(text_clean) == 64 and all(c in '0123456789abcdef' for c in text_clean):
            return "raw_hex"
        elif text_clean.startswith('5'):
            return "bitcoin_wif"
        elif text_clean.startswith(('k', 'l')):
            return "bitcoin_compressed_wif"
        else:
            return "base64_or_encoded"
    
    def analyze_all_sources(self):
        """Run complete source analysis"""
        print(f"🎯 TRACING SOURCE FOR: {TARGET_ADDRESS}")
        print("=" * 60)
        
        all_files = []
        for directory in SEARCH_DIRS:
            print(f"\n📁 Searching in: {directory}")
            files = self.search_files(directory)
            all_files.extend(files)
            print(f"   Found in {len(files)} files")
        
        self.results["source_files"] = all_files
        
        # Extract context from each file
        print(f"\n🔍 EXTRACTING CONTEXT FROM {len(all_files)} FILES")
        print("-" * 50)
        
        for file_info in all_files:
            file_path = file_info["file_path"]
            line_num = file_info["line_number"]
            
            print(f"📄 {os.path.basename(file_path)} (line {line_num})")
            
            context = self.extract_context(file_path, line_num)
            self.results["context_extracts"][file_path] = context
            
            # Collect all potential keys
            for key_info in context["potential_keys"]:
                key_data = {
                    "source_file": file_path,
                    "line": key_info["line"],
                    "content": key_info["content"],
                    "type": key_info["type"]
                }
                self.results["potential_keys"].append(key_data)
        
        # Summary
        print(f"\n📊 TRACE SUMMARY")
        print("-" * 30)
        print(f"Source files found: {len(all_files)}")
        print(f"Potential keys found: {len(self.results['potential_keys'])}")
        
        for key in self.results['potential_keys']:
            print(f"  • {key['type']} in {os.path.basename(key['source_file'])} (line {key['line']})")
        
        # Save results
        with open(REPORT_FILE, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: {REPORT_FILE}")
        
        return self.results

def main():
    tracer = SourceTracer()
    results = tracer.analyze_all_sources()
    
    if results["potential_keys"]:
        print(f"\n🔥 FOUND {len(results['potential_keys'])} POTENTIAL PRIVATE KEYS!")
        print("Next step: Test these keys against the target address")
    else:
        print("\n❌ No potential private keys found in context")
        print("May need to search in browser data, keystores, or encrypted files")

if __name__ == "__main__":
    main()
