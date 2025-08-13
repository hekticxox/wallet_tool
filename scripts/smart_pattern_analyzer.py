#!/usr/bin/env python3
"""
🧠 SMART PATTERN ANALYZER & HUNTER
==================================
AI-like analysis to find the highest probability funded wallets
"""

import json
import re
from datetime import datetime
from collections import defaultdict

class SmartPatternAnalyzer:
    def __init__(self):
        """Initialize smart pattern analyzer"""
        self.patterns = {
            'high_entropy': [],
            'date_based': [],
            'user_generated': [],
            'hardware_generated': [],
            'exchange_patterns': []
        }
        
    def analyze_all_keys(self):
        """Analyze all available keys for smart patterns"""
        print("🧠 SMART PATTERN ANALYZER")
        print("=" * 50)
        
        # Load all priority keys
        with open('PRIORITY_CHECKING_LIST.json', 'r') as f:
            data = json.load(f)
        
        keys_list = data.get('keys', [])
        print(f"📊 Analyzing {len(keys_list)} priority keys...")
        
        # Categorize keys by patterns
        categorized = self.categorize_keys(keys_list)
        
        # Show analysis
        self.show_pattern_analysis(categorized)
        
        # Generate hunting list
        hunting_targets = self.generate_hunting_targets(categorized)
        
        # Save for targeted hunting
        self.save_hunting_targets(hunting_targets)
        
        return hunting_targets
    
    def categorize_keys(self, keys_list):
        """Categorize keys by smart patterns"""
        categories = {
            'ultra_high_entropy': [],
            'human_generated': [],
            'timestamp_based': [],
            'exchange_like': [],
            'hardware_wallet': [],
            'test_patterns': []
        }
        
        for key_data in keys_list:
            private_key = key_data['private_key']
            
            # Remove 0x prefix
            if private_key.startswith('0x'):
                private_key = private_key[2:]
            
            # Calculate various scores
            entropy_score = self.calculate_entropy(private_key)
            human_score = self.calculate_human_likelihood(private_key)
            timestamp_score = self.check_timestamp_patterns(private_key)
            exchange_score = self.check_exchange_patterns(private_key)
            hardware_score = self.check_hardware_patterns(private_key)
            test_score = self.check_test_patterns(private_key)
            
            # Add scores to key data
            key_data.update({
                'entropy_score': entropy_score,
                'human_score': human_score,
                'timestamp_score': timestamp_score,
                'exchange_score': exchange_score,
                'hardware_score': hardware_score,
                'test_score': test_score
            })
            
            # Categorize based on highest score
            scores = {
                'ultra_high_entropy': entropy_score,
                'human_generated': human_score,
                'timestamp_based': timestamp_score,
                'exchange_like': exchange_score,
                'hardware_wallet': hardware_score,
                'test_patterns': test_score
            }
            
            best_category = max(scores, key=scores.get)
            if scores[best_category] > 0.3:  # Minimum threshold
                categories[best_category].append(key_data)
        
        return categories
    
    def calculate_entropy(self, hex_key):
        """Calculate true entropy score"""
        if len(hex_key) != 64:
            return 0
        
        # Count unique characters
        unique_chars = len(set(hex_key.lower()))
        base_entropy = unique_chars / 16.0
        
        # Check for randomness patterns
        randomness_indicators = 0
        
        # No excessive repetition
        max_consecutive = max(len(list(group)) for k, group in 
                             __import__('itertools').groupby(hex_key))
        if max_consecutive < 4:
            randomness_indicators += 1
        
        # Good distribution
        char_counts = defaultdict(int)
        for char in hex_key.lower():
            char_counts[char] += 1
        
        max_count = max(char_counts.values())
        min_count = min(char_counts.values())
        
        if max_count - min_count < 6:  # Fairly even distribution
            randomness_indicators += 1
        
        # No obvious sequential patterns
        sequential_patterns = ['0123', '1234', '2345', '3456', '4567', '5678', 
                              '6789', '789a', '89ab', '9abc', 'abcd', 'bcde', 'cdef']
        has_sequential = any(pattern in hex_key.lower() for pattern in sequential_patterns)
        
        if not has_sequential:
            randomness_indicators += 1
        
        final_score = base_entropy * (randomness_indicators / 3.0)
        return min(final_score, 1.0)
    
    def calculate_human_likelihood(self, hex_key):
        """Check if key looks human-generated"""
        human_indicators = 0
        
        # Repeated patterns (humans like patterns)
        for char in '0123456789abcdef':
            if char * 3 in hex_key:
                human_indicators += 0.1
        
        # Simple patterns
        simple_patterns = ['000', '111', '222', 'aaa', 'bbb', 'fff']
        pattern_count = sum(1 for pattern in simple_patterns if pattern in hex_key)
        human_indicators += pattern_count * 0.05
        
        # Date-like sequences (common in human keys)
        date_patterns = ['2020', '2021', '2022', '2023', '2024', '2025']
        date_count = sum(1 for pattern in date_patterns if pattern in hex_key)
        human_indicators += date_count * 0.2
        
        return min(human_indicators, 1.0)
    
    def check_timestamp_patterns(self, hex_key):
        """Check for timestamp-based generation"""
        timestamp_score = 0
        
        # Look for Unix timestamp patterns
        for i in range(0, len(hex_key) - 7, 2):
            substr = hex_key[i:i+8]
            try:
                decimal = int(substr, 16)
                # Check if it's a reasonable timestamp
                if 1500000000 < decimal < 2000000000:  # Roughly 2017-2033
                    timestamp_score += 0.3
            except:
                pass
        
        return min(timestamp_score, 1.0)
    
    def check_exchange_patterns(self, hex_key):
        """Check for exchange-generated patterns"""
        exchange_score = 0
        
        # Exchanges often use specific prefixes or patterns
        exchange_prefixes = ['dead', 'beef', 'cafe', 'face', 'babe']
        
        for prefix in exchange_prefixes:
            if prefix in hex_key.lower():
                exchange_score += 0.2
        
        # Check for incrementing patterns (exchanges batch generate)
        for i in range(len(hex_key) - 3):
            substr = hex_key[i:i+4]
            if re.match(r'[0-9a-f]{4}', substr):
                try:
                    val = int(substr, 16)
                    if val % 1000 == 0:  # Round numbers
                        exchange_score += 0.1
                except:
                    pass
        
        return min(exchange_score, 1.0)
    
    def check_hardware_patterns(self, hex_key):
        """Check for hardware wallet patterns"""
        hardware_score = 0
        
        # Hardware wallets often have high entropy but specific patterns
        if self.calculate_entropy(hex_key) > 0.8:
            hardware_score += 0.3
        
        # Check for BIP39-related patterns
        # Hardware wallets derive from seeds
        if not any(char * 4 in hex_key for char in '0123456789abcdef'):
            hardware_score += 0.2
        
        return min(hardware_score, 1.0)
    
    def check_test_patterns(self, hex_key):
        """Check for test/development patterns"""
        test_score = 0
        
        # Common test patterns
        test_patterns = ['1234', 'test', 'dead', 'beef', '0000', 'ffff']
        
        for pattern in test_patterns:
            if pattern in hex_key.lower():
                test_score += 0.15
        
        # All same character (common in tests)
        if len(set(hex_key)) == 1:
            test_score += 0.5
        
        return min(test_score, 1.0)
    
    def show_pattern_analysis(self, categorized):
        """Show pattern analysis results"""
        print("\n🔍 PATTERN ANALYSIS RESULTS:")
        print("-" * 40)
        
        for category, keys in categorized.items():
            if keys:
                print(f"{category.upper().replace('_', ' ')}: {len(keys)} keys")
                
                # Show top 3 scores for each category
                sorted_keys = sorted(keys, key=lambda x: x.get(f'{category.split("_")[0]}_score', 0), reverse=True)
                for i, key in enumerate(sorted_keys[:3]):
                    score = key.get(f'{category.split("_")[0]}_score', 0)
                    print(f"   #{i+1}: {key['private_key'][:12]}... (score: {score:.3f})")
                print()
    
    def generate_hunting_targets(self, categorized):
        """Generate prioritized hunting targets"""
        print("🎯 GENERATING SMART HUNTING TARGETS")
        print("-" * 40)
        
        # Priority order (most likely to have funds)
        priority_categories = [
            'ultra_high_entropy',
            'hardware_wallet', 
            'human_generated',
            'exchange_like',
            'timestamp_based'
        ]
        
        hunting_targets = []
        
        for category in priority_categories:
            keys = categorized.get(category, [])
            if keys:
                # Sort by relevant score
                score_key = f'{category.split("_")[0]}_score'
                sorted_keys = sorted(keys, key=lambda x: x.get(score_key, 0), reverse=True)
                
                # Take top keys from each category
                top_keys = sorted_keys[:20]  # Top 20 from each category
                hunting_targets.extend(top_keys)
                
                print(f"Added {len(top_keys)} targets from {category}")
        
        # Remove duplicates and limit total
        seen = set()
        unique_targets = []
        
        for key_data in hunting_targets:
            key_id = key_data['private_key']
            if key_id not in seen:
                seen.add(key_id)
                unique_targets.append(key_data)
        
        # Sort by combined score
        for key_data in unique_targets:
            combined_score = (
                key_data.get('entropy_score', 0) * 0.3 +
                key_data.get('hardware_score', 0) * 0.25 +
                key_data.get('human_score', 0) * 0.2 +
                key_data.get('exchange_score', 0) * 0.15 +
                key_data.get('timestamp_score', 0) * 0.1
            )
            key_data['combined_score'] = combined_score
        
        final_targets = sorted(unique_targets, key=lambda x: x['combined_score'], reverse=True)[:50]
        
        print(f"\n🎯 FINAL SMART TARGETS: {len(final_targets)}")
        print("Top 5 targets:")
        for i, key in enumerate(final_targets[:5]):
            print(f"   #{i+1}: {key['private_key'][:12]}... (score: {key['combined_score']:.3f})")
        
        return final_targets
    
    def save_hunting_targets(self, targets):
        """Save smart hunting targets"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"SMART_HUNTING_TARGETS_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(targets, f, indent=2)
        
        print(f"\n💾 Smart targets saved to: {filename}")
        return filename

def main():
    """Execute smart pattern analysis"""
    analyzer = SmartPatternAnalyzer()
    targets = analyzer.analyze_all_keys()
    
    print("\n🚀 SMART ANALYSIS COMPLETE!")
    print("Ready for targeted hunting of highest probability keys.")

if __name__ == "__main__":
    main()
