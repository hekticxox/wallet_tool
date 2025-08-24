#!/usr/bin/env python3
"""
NET607 Comprehensive Key Extractor
Extract ALL possible keys from NET607 with advanced pattern matching
"""

import os
import re
import time
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import hashlib

class NET607ComprehensiveExtractor:
    def __init__(self):
        self.extracted_keys = []
        self.file_stats = defaultdict(int)
        self.country_stats = defaultdict(int)
        self.start_time = time.time()
        
        # Advanced regex patterns for various crypto formats
        self.patterns = {
            'ethereum_hex': re.compile(r'\b[a-fA-F0-9]{64}\b'),
            'ethereum_0x': re.compile(r'\b0x[a-fA-F0-9]{64}\b'),
            'bitcoin_wif': re.compile(r'\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b'),
            'compressed_wif': re.compile(r'\b[KL][1-9A-HJ-NP-Za-km-z]{51}\b'),
            'mnemonic_12': re.compile(r'\b(?:[a-z]+ ){11}[a-z]+\b'),
            'mnemonic_24': re.compile(r'\b(?:[a-z]+ ){23}[a-z]+\b'),
            'base58_key': re.compile(r'\b[1-9A-HJ-NP-Za-km-z]{44,88}\b'),
            'wallet_dat_key': re.compile(r'[a-fA-F0-9]{64}'),
            'private_key_label': re.compile(r'(?:private.{0,5}key|key).{0,50}[a-fA-F0-9]{40,64}', re.IGNORECASE),
            'seed_phrase': re.compile(r'(?:seed|mnemonic).{0,50}(?:[a-z]+ ){5,23}[a-z]+', re.IGNORECASE),
        }
        
        # High-value file keywords
        self.high_value_keywords = [
            'wallet', 'private', 'key', 'seed', 'mnemonic', 'backup', 'recovery',
            'btc', 'bitcoin', 'eth', 'ethereum', 'crypto', 'coin', 'address',
            'password', 'secret', 'important', 'confidential', 'btcrecover',
            'electrum', 'myetherwallet', 'metamask', 'blockchain', 'coinbase',
            'binance', 'kraken', 'bitfinex', 'poloniex', 'huobi'
        ]
    
    def calculate_file_priority(self, file_path: Path) -> float:
        """Calculate priority score for a file"""
        score = 0.1  # Base score
        
        filename_lower = file_path.name.lower()
        path_lower = str(file_path).lower()
        
        # Keyword matching
        for keyword in self.high_value_keywords:
            if keyword in filename_lower:
                score += 0.3
            elif keyword in path_lower:
                score += 0.1
        
        # File extension bonuses
        ext = file_path.suffix.lower()
        if ext in ['.key', '.wallet', '.dat', '.backup', '.seed']:
            score += 0.4
        elif ext in ['.txt', '.log', '.conf', '.json']:
            score += 0.2
        elif ext in ['.pdf', '.doc', '.docx']:
            score += 0.1
        
        # Size bonus (moderate size files are good)
        try:
            size = file_path.stat().st_size
            if 100 < size < 100000:  # 100 bytes to 100KB
                score += 0.2
            elif 1000 < size < 50000:  # 1KB to 50KB
                score += 0.3
        except:
            pass
        
        # Path depth (deeper = more likely to be important)
        depth = len(file_path.parts)
        if depth > 5:
            score += 0.1
        
        return score
    
    def extract_keys_from_file(self, file_path: Path) -> list:
        """Extract all possible keys from a file"""
        keys_found = []
        
        try:
            # Try different encodings
            content = None
            for encoding in ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                        content = f.read(500000)  # Read first 500KB
                    break
                except:
                    continue
            
            if not content:
                return keys_found
            
            # Apply all patterns
            for pattern_name, pattern in self.patterns.items():
                matches = pattern.findall(content)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match[0] else match[1] if len(match) > 1 else ""
                    
                    match = match.strip()
                    if len(match) < 20:  # Skip very short matches
                        continue
                    
                    key_data = {
                        'key': match,
                        'pattern_type': pattern_name,
                        'source_file': str(file_path.relative_to(Path('net607'))),
                        'file_size': file_path.stat().st_size,
                        'priority_score': self.calculate_key_priority(match, pattern_name, str(file_path))
                    }
                    
                    keys_found.append(key_data)
            
            # Look for hex strings in specific contexts
            hex_context_patterns = [
                r'private.{0,10}[a-fA-F0-9]{40,64}',
                r'key.{0,10}[a-fA-F0-9]{40,64}',
                r'secret.{0,10}[a-fA-F0-9]{40,64}',
                r'wallet.{0,10}[a-fA-F0-9]{40,64}',
            ]
            
            for context_pattern in hex_context_patterns:
                matches = re.findall(context_pattern, content, re.IGNORECASE)
                for match in matches:
                    # Extract just the hex part
                    hex_match = re.search(r'[a-fA-F0-9]{40,64}', match)
                    if hex_match:
                        hex_key = hex_match.group()
                        if len(hex_key) >= 40:
                            key_data = {
                                'key': hex_key,
                                'pattern_type': 'contextual_hex',
                                'source_file': str(file_path.relative_to(Path('net607'))),
                                'file_size': file_path.stat().st_size,
                                'priority_score': self.calculate_key_priority(hex_key, 'contextual_hex', str(file_path))
                            }
                            keys_found.append(key_data)
            
        except Exception as e:
            pass
        
        return keys_found
    
    def calculate_key_priority(self, key: str, pattern_type: str, file_path: str) -> float:
        """Calculate priority score for a key"""
        score = 0.3  # Base score
        
        # Pattern type bonuses
        pattern_scores = {
            'ethereum_0x': 0.4,
            'ethereum_hex': 0.3,
            'bitcoin_wif': 0.3,
            'mnemonic_12': 0.4,
            'mnemonic_24': 0.5,
            'contextual_hex': 0.3,
            'private_key_label': 0.4,
            'seed_phrase': 0.4,
        }
        score += pattern_scores.get(pattern_type, 0.2)
        
        # Key characteristics
        if len(key) == 64 and all(c in '0123456789abcdefABCDEF' for c in key):
            score += 0.2  # Perfect hex length
        
        if key.startswith('0x'):
            score += 0.1
        
        # Entropy check
        if self.has_good_entropy(key):
            score += 0.2
        
        # File path bonuses
        file_path_lower = file_path.lower()
        if any(keyword in file_path_lower for keyword in self.high_value_keywords):
            score += 0.2
        
        # Country priority (some countries more likely to have active wallets)
        high_value_countries = ['US', 'CN', 'GB', 'DE', 'JP', 'KR', 'SG', 'CH', 'NL', 'CA']
        for country in high_value_countries:
            if f'[{country}]' in file_path:
                score += 0.1
                break
        
        return min(score, 1.0)  # Cap at 1.0
    
    def has_good_entropy(self, key: str) -> bool:
        """Check if key has good entropy"""
        if len(key) < 20:
            return False
        
        # Count unique characters
        unique_chars = len(set(key.lower()))
        entropy_ratio = unique_chars / len(key)
        
        return entropy_ratio > 0.3
    
    def extract_all_keys(self, max_countries: int = 100, max_files_per_country: int = 200):
        """Extract keys from all NET607 directories"""
        net607_path = Path('net607')
        if not net607_path.exists():
            print("❌ NET607 directory not found")
            return
        
        print(f"🔍 Starting comprehensive key extraction from NET607...")
        print(f"📊 Max countries: {max_countries}, Max files per country: {max_files_per_country}")
        
        # Get all country directories
        country_dirs = [d for d in net607_path.iterdir() if d.is_dir()]
        print(f"🌍 Found {len(country_dirs)} country directories")
        
        # Prioritize high-value countries
        priority_countries = ['US', 'CN', 'GB', 'DE', 'JP', 'KR', 'SG', 'CH', 'NL', 'CA']
        
        # Sort directories by priority
        def sort_key(directory):
            country_code = directory.name.split(']')[0].strip('[')
            if country_code in priority_countries:
                return (0, priority_countries.index(country_code))
            else:
                return (1, country_code)
        
        sorted_dirs = sorted(country_dirs, key=sort_key)[:max_countries]
        
        total_files = 0
        processed_files = 0
        
        for i, country_dir in enumerate(sorted_dirs, 1):
            country_code = country_dir.name.split(']')[0].strip('[')
            print(f"\n🔍 [{i}/{len(sorted_dirs)}] Processing {country_dir.name}...")
            
            # Get all files in this country directory
            all_files = []
            for file_path in country_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        # Skip very large files (>50MB) and very small files (<10 bytes)
                        size = file_path.stat().st_size
                        if 10 < size < 50 * 1024 * 1024:
                            priority = self.calculate_file_priority(file_path)
                            all_files.append((file_path, priority))
                    except:
                        continue
            
            # Sort files by priority and take top ones
            all_files.sort(key=lambda x: x[1], reverse=True)
            selected_files = all_files[:max_files_per_country]
            
            total_files += len(selected_files)
            
            # Process selected files
            for file_path, priority in selected_files:
                keys_from_file = self.extract_keys_from_file(file_path)
                
                # Add country info to each key
                for key_data in keys_from_file:
                    key_data['country'] = country_code
                    key_data['file_priority'] = priority
                
                self.extracted_keys.extend(keys_from_file)
                processed_files += 1
                
                # Update stats
                ext = file_path.suffix.lower() or 'no_ext'
                self.file_stats[ext] += 1
                self.country_stats[country_code] += len(keys_from_file)
                
                if processed_files % 100 == 0:
                    print(f"    📄 Processed {processed_files} files, found {len(self.extracted_keys)} keys")
            
            print(f"    ✅ {country_code}: {len(selected_files)} files processed, {self.country_stats[country_code]} keys found")
        
        print(f"\n✅ EXTRACTION COMPLETE!")
        print(f"📁 Countries processed: {len(sorted_dirs)}")
        print(f"📄 Files processed: {processed_files}")
        print(f"🔑 Total keys extracted: {len(self.extracted_keys)}")
        
        # Sort all keys by priority
        self.extracted_keys.sort(key=lambda x: x['priority_score'], reverse=True)
    
    def save_results(self):
        """Save extraction results"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"NET607_COMPREHENSIVE_KEYS_{timestamp}.json"
        
        # Organize keys by priority
        high_priority = []
        medium_priority = []
        low_priority = []
        
        for key_data in self.extracted_keys:
            score = key_data['priority_score']
            if score >= 0.7:
                high_priority.append(key_data)
            elif score >= 0.5:
                medium_priority.append(key_data)
            else:
                low_priority.append(key_data)
        
        results = {
            'extraction_info': {
                'timestamp': timestamp,
                'total_keys': len(self.extracted_keys),
                'processing_time_seconds': time.time() - self.start_time,
                'high_priority_count': len(high_priority),
                'medium_priority_count': len(medium_priority),
                'low_priority_count': len(low_priority)
            },
            'country_stats': dict(self.country_stats),
            'file_type_stats': dict(self.file_stats),
            'prioritized_keys': {
                'high_priority': high_priority[:5000],  # Top 5000
                'medium_priority': medium_priority[:2000],  # Top 2000
                'low_priority': low_priority[:1000]  # Top 1000
            }
        }
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")
        return results_file
    
    def print_summary(self):
        """Print extraction summary"""
        elapsed = time.time() - self.start_time
        
        print(f"\n📊 EXTRACTION SUMMARY")
        print(f"==================================================")
        print(f"⏱️  Total Time: {elapsed:.1f} seconds")
        print(f"🔑 Keys Extracted: {len(self.extracted_keys):,}")
        print(f"⚡ Rate: {len(self.extracted_keys)/elapsed:.1f} keys/sec")
        
        # Priority breakdown
        priority_counts = {'high': 0, 'medium': 0, 'low': 0}
        for key_data in self.extracted_keys:
            score = key_data['priority_score']
            if score >= 0.7:
                priority_counts['high'] += 1
            elif score >= 0.5:
                priority_counts['medium'] += 1
            else:
                priority_counts['low'] += 1
        
        print(f"\n🎯 PRIORITY BREAKDOWN:")
        print(f"    🏆 High Priority (≥0.7): {priority_counts['high']:,}")
        print(f"    ⭐ Medium Priority (≥0.5): {priority_counts['medium']:,}")
        print(f"    📝 Low Priority (<0.5): {priority_counts['low']:,}")
        
        # Top countries
        print(f"\n🌍 TOP COUNTRIES BY KEYS:")
        top_countries = sorted(self.country_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        for country, count in top_countries:
            print(f"    {country}: {count:,} keys")
        
        # Top file types
        print(f"\n📄 TOP FILE TYPES:")
        top_types = sorted(self.file_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        for file_type, count in top_types:
            print(f"    {file_type}: {count:,} files")

def main():
    """Main execution function"""
    extractor = NET607ComprehensiveExtractor()
    
    try:
        # Extract keys from top 100 countries, max 200 files per country
        extractor.extract_all_keys(max_countries=100, max_files_per_country=200)
        
        # Save results
        results_file = extractor.save_results()
        
        # Print summary
        extractor.print_summary()
        
        print(f"\n🎉 Ready for balance checking!")
        print(f"📂 Use the prioritized keys from: {results_file}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        extractor.save_results()
        extractor.print_summary()
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        extractor.save_results()

if __name__ == "__main__":
    print("🎯 NET607 COMPREHENSIVE KEY EXTRACTOR")
    print("=" * 50)
    main()
