#!/usr/bin/env python3
"""
Pattern-Focused Address Hunter - Specifically targets addresses matching proven successful patterns
"""
import json
import sys
from collections import defaultdict

def find_pattern_matches(addresses, target_patterns):
    """Find addresses that match the proven successful patterns"""
    
    matches = {pattern: [] for pattern in target_patterns}
    
    print(f"🎯 HUNTING FOR PROVEN SUCCESSFUL PATTERNS")
    print(f"📊 Scanning {len(addresses):,} addresses for {len(target_patterns)} proven patterns")
    print()
    
    for pattern in target_patterns:
        print(f"🔍 Searching for pattern: {pattern}")
    
    print()
    
    for addr_data in addresses:
        address = addr_data.get('address', '')
        
        # Check if address matches any successful pattern
        for pattern in target_patterns:
            if pattern.lower() in address.lower():
                matches[pattern].append(addr_data)
    
    return matches

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 pattern_hunter.py <json_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Proven successful patterns from system overview
    proven_patterns = [
        '0x9Ef2',  # Found: 5.03e-16 ETH
        '0x5238',  # Found: 1.60e-17 ETH  
        '0x9E0F',  # Found: 1.20e-17 ETH
    ]
    
    print("🎯 PATTERN-FOCUSED ADDRESS HUNTER")
    print("=" * 50)
    print("📋 Using PROVEN successful patterns from previous discoveries")
    print()
    
    # Load addresses
    print(f"📂 Loading addresses from: {input_file}")
    with open(input_file, 'r') as f:
        addresses = json.load(f)
    
    print(f"📊 Loaded {len(addresses):,} addresses")
    print()
    
    # Find pattern matches
    matches = find_pattern_matches(addresses, proven_patterns)
    
    # Report results
    total_matches = 0
    all_matches = []
    
    for pattern, matched_addresses in matches.items():
        count = len(matched_addresses)
        total_matches += count
        all_matches.extend(matched_addresses)
        
        print(f"🎯 Pattern {pattern}: {count:,} matches")
        
        # Show first few matches
        if count > 0:
            print(f"   📋 Sample matches:")
            for i, addr in enumerate(matched_addresses[:5], 1):
                source_short = addr.get('source', 'unknown').split('/')[-1][:25]
                print(f"      {i}. {addr['address']} ({addr['chain']}, {source_short})")
            if count > 5:
                print(f"      ... and {count - 5} more")
        print()
    
    print(f"🏆 TOTAL PATTERN MATCHES: {total_matches:,} addresses")
    print()
    
    if total_matches > 0:
        # Save pattern matches
        output_file = "pattern_matches.json"
        with open(output_file, 'w') as f:
            json.dump(all_matches, f, indent=2)
        
        print(f"💾 Pattern matches saved to: {output_file}")
        print(f"🚀 Ready to check {total_matches} addresses with PROVEN success patterns!")
        
        # Show breakdown by chain
        chain_counts = defaultdict(int)
        for addr in all_matches:
            chain_counts[addr.get('chain', 'unknown')] += 1
        
        print(f"\n📊 Breakdown by blockchain:")
        for chain, count in chain_counts.items():
            print(f"   {chain}: {count:,} addresses")
    else:
        print("❌ No addresses found matching the proven successful patterns")
        print("💡 This suggests the current dataset may not contain the same wallet types")
        print("    that produced the previous successful finds.")

if __name__ == "__main__":
    main()
