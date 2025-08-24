#!/usr/bin/env python3
"""
Phase 1 Investigation - Manual Context Review & Credential Search
Extract detailed context around target address and search for VegasPix credentials
"""

import os
import re
import json
from datetime import datetime

class Phase1Investigator:
    def __init__(self):
        self.target_address = "0x6e59e2a98d12f45ab5872942fe45a1036b1ea9c9"
        self.recovery_key = "8AKP9G3UJYWK4OYGFLRWEUBHZTA="
        self.autofill_file = "/home/admin/wallet_tool/net605/[BR]170.247.37.63/Chrome/Profile 1/Autofills.txt"
        self.results = []
        
    def extract_detailed_context(self):
        """Extract comprehensive context around the target address"""
        print("🔍 EXTRACTING DETAILED AUTOFILL CONTEXT")
        print("-" * 50)
        
        if not os.path.exists(self.autofill_file):
            print(f"❌ Autofill file not found: {self.autofill_file}")
            return None
            
        try:
            with open(self.autofill_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            target_lines = []
            recovery_lines = []
            
            # Find all occurrences
            for i, line in enumerate(lines):
                if self.target_address.lower() in line.lower():
                    target_lines.append(i)
                if self.recovery_key in line:
                    recovery_lines.append(i)
                    
            print(f"✅ Found target address on lines: {target_lines}")
            print(f"✅ Found recovery key on lines: {recovery_lines}")
            
            # Extract comprehensive context (100 lines before and after each occurrence)
            all_context_lines = set()
            for line_num in target_lines + recovery_lines:
                start = max(0, line_num - 100)
                end = min(len(lines), line_num + 100)
                all_context_lines.update(range(start, end))
                
            context_lines = sorted(list(all_context_lines))
            context_data = []
            
            for line_num in context_lines:
                context_data.append({
                    'line_number': line_num + 1,  # 1-indexed for display
                    'content': lines[line_num].strip(),
                    'is_target': self.target_address.lower() in lines[line_num].lower(),
                    'is_recovery': self.recovery_key in lines[line_num]
                })
                
            # Save detailed context
            with open('detailed_autofill_context.json', 'w') as f:
                json.dump(context_data, f, indent=2)
                
            print(f"✅ Extracted {len(context_data)} lines of context")
            print(f"💾 Saved to: detailed_autofill_context.json")
            
            # Analyze the context for patterns
            self.analyze_context_patterns(context_data)
            
            return context_data
            
        except Exception as e:
            print(f"❌ Error extracting context: {str(e)}")
            return None
            
    def analyze_context_patterns(self, context_data):
        """Analyze the extracted context for useful patterns"""
        print(f"\n🔍 ANALYZING CONTEXT PATTERNS")
        print("-" * 50)
        
        # Patterns to look for
        patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'username': r'(?:username|user|login|email)["\s:=]+([^\s"\']+)',
            'password': r'(?:password|pass|pwd)["\s:=]+([^\s"\']+)',
            'url': r'https?://[^\s"\'<>]+',
            'crypto_address': r'0x[a-fA-F0-9]{40}',
            'private_key': r'[a-fA-F0-9]{64}',
            'recovery_phrase': r'(?:seed|mnemonic|phrase)["\s:=]+([^"\']+)',
            'session_id': r'(?:session|token|id)["\s:=]+([^\s"\']+)',
            'user_id': r'(?:userid|uid|account)["\s:=]+([^\s"\']+)',
            'api_key': r'(?:api|key|secret)["\s:=]+([^\s"\']+)'
        }
        
        findings = {}
        content_text = ' '.join([line['content'] for line in context_data])
        
        for pattern_name, pattern in patterns.items():
            matches = re.findall(pattern, content_text, re.IGNORECASE)
            if matches:
                findings[pattern_name] = list(set(matches))  # Remove duplicates
                
        if findings:
            print("✅ Found interesting patterns:")
            for pattern_name, matches in findings.items():
                print(f"   📍 {pattern_name}: {len(matches)} matches")
                for match in matches[:5]:  # Show first 5 matches
                    print(f"      • {match}")
                if len(matches) > 5:
                    print(f"      ... and {len(matches) - 5} more")
                    
            # Save findings
            with open('context_analysis.json', 'w') as f:
                json.dump(findings, f, indent=2)
            print(f"💾 Analysis saved to: context_analysis.json")
        else:
            print("❌ No additional patterns found in context")
            
        return findings
        
    def search_vegaspix_credentials(self):
        """Search for VegasPix-related credentials across all files"""
        print(f"\n🌐 SEARCHING FOR VEGASPIX CREDENTIALS")
        print("-" * 50)
        
        # Search patterns
        vegaspix_patterns = [
            r'vegaspix',
            r'vegas.*pix',
            r'pix.*vegas',
            r'casino.*login',
            r'gambling.*account'
        ]
        
        credential_patterns = [
            r'(?:username|user|login|email)["\s:=]+([^\s"\']+)',
            r'(?:password|pass|pwd)["\s:=]+([^\s"\']+)',
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        ]
        
        # Search in browser data directories
        search_paths = [
            "/home/admin/wallet_tool/net605",
            "/home/admin/wallet_tool/net607"
        ]
        
        vegaspix_files = []
        
        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue
                
            print(f"🔍 Searching in: {search_path}")
            
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    filepath = os.path.join(root, file)
                    
                    # Skip binary files
                    if any(ext in filepath.lower() for ext in ['.exe', '.dll', '.bin', '.dat']):
                        continue
                        
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read(50000)  # First 50KB
                            
                        # Check for VegasPix mentions
                        for pattern in vegaspix_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                vegaspix_files.append(filepath)
                                print(f"   📁 Found VegasPix mention: {filepath}")
                                break
                                
                    except Exception:
                        continue
                        
        if vegaspix_files:
            print(f"\n✅ Found {len(vegaspix_files)} files with VegasPix mentions")
            
            # Analyze VegasPix files for credentials
            credentials = {}
            for filepath in vegaspix_files[:10]:  # Limit to first 10 files
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    file_creds = {}
                    for cred_pattern in credential_patterns:
                        matches = re.findall(cred_pattern, content, re.IGNORECASE)
                        if matches:
                            file_creds[cred_pattern] = matches[:10]  # First 10 matches
                            
                    if file_creds:
                        credentials[filepath] = file_creds
                        
                except Exception:
                    continue
                    
            if credentials:
                print(f"\n✅ Found credentials in {len(credentials)} files:")
                for filepath, creds in credentials.items():
                    print(f"   📄 {os.path.basename(filepath)}")
                    for pattern, matches in creds.items():
                        print(f"      • Found {len(matches)} credential matches")
                        
                # Save credential findings
                with open('vegaspix_credentials.json', 'w') as f:
                    json.dump(credentials, f, indent=2)
                print(f"💾 Credentials saved to: vegaspix_credentials.json")
            else:
                print("❌ No credentials found in VegasPix files")
        else:
            print("❌ No VegasPix-related files found")
            
        return vegaspix_files
        
    def search_email_patterns(self):
        """Search for email patterns that might contain VegasPix communications"""
        print(f"\n📧 SEARCHING EMAIL PATTERNS")
        print("-" * 50)
        
        email_keywords = [
            'vegaspix', 'casino', 'gambling', 'wallet', 'account',
            'verification', 'registration', 'confirm', 'recovery',
            'password', 'reset', 'login', 'welcome'
        ]
        
        email_files = []
        search_paths = [
            "/home/admin/wallet_tool/net605",
            "/home/admin/wallet_tool/net607"
        ]
        
        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue
                
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    # Look for email-related files
                    if any(keyword in file.lower() for keyword in ['mail', 'inbox', 'sent', 'draft']):
                        email_files.append(os.path.join(root, file))
                        
        if email_files:
            print(f"✅ Found {len(email_files)} potential email files")
            
            email_matches = {}
            for email_file in email_files[:5]:  # Check first 5
                try:
                    with open(email_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(100000)  # First 100KB
                        
                    matches = []
                    for keyword in email_keywords:
                        if re.search(keyword, content, re.IGNORECASE):
                            matches.append(keyword)
                            
                    if matches:
                        email_matches[email_file] = matches
                        print(f"   📧 {os.path.basename(email_file)}: {matches}")
                        
                except Exception:
                    continue
                    
            if email_matches:
                with open('email_patterns.json', 'w') as f:
                    json.dump(email_matches, f, indent=2)
                print(f"💾 Email patterns saved to: email_patterns.json")
        else:
            print("❌ No email files found")
            
        return email_files
        
    def run_phase1_investigation(self):
        """Run complete Phase 1 investigation"""
        print("🚀 PHASE 1 INVESTIGATION - MANUAL CONTEXT REVIEW")
        print("=" * 70)
        
        results = {}
        
        # Step 1: Extract detailed context
        print("Step 1: Extracting detailed autofill context...")
        context_data = self.extract_detailed_context()
        results['context_extraction'] = len(context_data) if context_data else 0
        
        # Step 2: Search for VegasPix credentials
        print("\nStep 2: Searching for VegasPix credentials...")
        vegaspix_files = self.search_vegaspix_credentials()
        results['vegaspix_files'] = len(vegaspix_files)
        
        # Step 3: Search email patterns
        print("\nStep 3: Searching email patterns...")
        email_files = self.search_email_patterns()
        results['email_files'] = len(email_files)
        
        # Save results summary
        results['timestamp'] = datetime.now().isoformat()
        results['target_address'] = self.target_address
        results['recovery_key'] = self.recovery_key
        
        with open('phase1_investigation_results.json', 'w') as f:
            json.dump(results, f, indent=2)
            
        print(f"\n✅ PHASE 1 COMPLETE")
        print(f"📊 Results Summary:")
        print(f"   📋 Context lines extracted: {results['context_extraction']}")
        print(f"   🌐 VegasPix files found: {results['vegaspix_files']}")
        print(f"   📧 Email files found: {results['email_files']}")
        print(f"💾 Summary saved to: phase1_investigation_results.json")
        
        return results

if __name__ == "__main__":
    investigator = Phase1Investigator()
    investigator.run_phase1_investigation()
