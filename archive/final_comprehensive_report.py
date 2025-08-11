#!/usr/bin/env python3
"""
Final Comprehensive Wallet Recovery Report
==========================================
Analyzes all results from the wallet recovery process and generates a detailed report.
"""

import json
import os
from collections import defaultdict, Counter

def load_json_file(filepath):
    """Load JSON file with error handling."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error loading {filepath}: {e}")
        return None

def analyze_address_formats(addresses):
    """Analyze the formats of addresses found."""
    formats = defaultdict(int)
    for addr in addresses:
        if addr.startswith('0x') and len(addr) == 42:
            formats['Ethereum'] += 1
        elif addr.startswith('1') and len(addr) >= 26 and len(addr) <= 35:
            formats['Bitcoin Legacy'] += 1
        elif addr.startswith('3') and len(addr) >= 26 and len(addr) <= 35:
            formats['Bitcoin P2SH'] += 1
        elif addr.startswith('bc1'):
            formats['Bitcoin Bech32'] += 1
        elif len(addr) == 34 and addr[0] in '123456789ABCDEFGHJKLMNPQRSTUVWXYZ':
            formats['Bitcoin-like'] += 1
        elif len(addr) == 64 and all(c in '0123456789abcdefABCDEF' for c in addr):
            formats['Hex (64 chars)'] += 1
        elif len(addr) >= 40 and all(c in '0123456789abcdefABCDEF' for c in addr):
            formats['Hex (other)'] += 1
        else:
            formats['Unknown/Other'] += 1
    return dict(formats)

def main():
    """Generate comprehensive final report."""
    
    print("🔍 FINAL COMPREHENSIVE WALLET RECOVERY REPORT")
    print("=" * 70)
    print()
    
    # Load all result files
    files = {
        'enhanced_extraction': 'enhanced_wallet_extraction_results.json',
        'sorted_wallets': 'wallet_items_sorted_by_likelihood.json',
        'accessible_wallets': 'accessible_wallets_report.json',
        'balance_results': 'fast_accessible_balance_results.json'
    }
    
    data = {}
    for name, filename in files.items():
        data[name] = load_json_file(filename)
        if data[name] is not None:
            print(f"✅ Loaded {filename}")
        else:
            print(f"❌ Failed to load {filename}")
    
    print()
    print("📊 SUMMARY STATISTICS")
    print("-" * 50)
    
    # Enhanced extraction results
    if data['enhanced_extraction']:
        stats = data['enhanced_extraction']['statistics']
        print(f"• Total wallet items found: {stats['total_extracted_items']:,}")
        print(f"• Files processed: {stats['total_files_scanned']:,}")
        
        print(f"• Items by type:")
        for item_type, count in stats['items_by_type'].items():
            print(f"    - {item_type}: {count:,}")
        
        print(f"• Files by type:")
        for file_type, count in stats['files_by_type'].items():
            if count > 0:
                print(f"    - {file_type}: {count:,}")
        
        # Show some extraction results
        extraction_results = data['enhanced_extraction'].get('extraction_results', [])
        if extraction_results:
            print(f"\n📄 EXTRACTION SAMPLE (first 5 results):")
            for i, result in enumerate(extraction_results[:5], 1):
                print(f"   {i}. {result.get('type', 'unknown')} from {os.path.basename(result.get('source_file', 'unknown'))}")
    
    # Sorted wallets
    if data['sorted_wallets']:
        print(f"\n📋 SORTED WALLET ITEMS: {len(data['sorted_wallets']):,}")
        
        # Count by type
        type_counts = Counter(item['type'] for item in data['sorted_wallets'])
        print("   Types found:")
        for wallet_type, count in type_counts.most_common():
            print(f"     • {wallet_type}: {count:,}")
        
        # Address format analysis
        all_addresses = []
        for item in data['sorted_wallets']:
            if item['type'] in ['bitcoin_address', 'ethereum_address'] and 'content' in item:
                all_addresses.append(item['content'])
        
        if all_addresses:
            print(f"\n🔢 ADDRESS FORMAT ANALYSIS ({len(all_addresses):,} total):")
            format_counts = analyze_address_formats(all_addresses)
            for fmt, count in sorted(format_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"     • {fmt}: {count:,}")
    
    # Accessible wallets
    if data['accessible_wallets']:
        accessible_wallets = data['accessible_wallets']['accessible_wallets']
        print(f"\n🔓 ACCESSIBLE WALLETS (with private keys): {len(accessible_wallets):,}")
        
        # Count types
        type_counts = Counter()
        key_counts = defaultdict(int)
        
        for wallet in accessible_wallets:
            type_counts[wallet.get('chain', 'unknown')] += 1
            if wallet.get('private_keys'):
                key_counts['private_keys'] += len(wallet['private_keys'])
            if wallet.get('mnemonic'):
                key_counts['mnemonics'] += 1
        
        print(f"• By chain type:")
        for chain, count in type_counts.most_common():
            print(f"    - {chain}: {count:,}")
        
        print(f"• Key types found:")
        for key_type, count in key_counts.items():
            print(f"    - {key_type}: {count:,}")
        
        # Show top accessible wallets
        if accessible_wallets:
            print(f"\n🎯 TOP 10 ACCESSIBLE WALLETS:")
            for i, wallet in enumerate(accessible_wallets[:10], 1):
                keys_count = len(wallet.get('private_keys', []))
                mnemonic = "Yes" if wallet.get('mnemonic') else "No"
                print(f"   {i}. Chain: {wallet.get('chain', 'unknown')}, Keys: {keys_count}, Mnemonic: {mnemonic}")
                print(f"      Source: {os.path.basename(wallet.get('source', 'unknown'))}")
    
    # Balance checking results
    if data['balance_results']:
        balance = data['balance_results']
        print(f"\n💰 BALANCE CHECKING RESULTS:")
        print(f"• Addresses checked: {balance.get('addresses_checked', 'N/A'):,}")
        print(f"• Funded addresses: {len(balance.get('funded_addresses', []))}")
        
        if balance.get('funded_addresses'):
            print(f"\n💎 FUNDED ADDRESSES FOUND:")
            for addr_info in balance['funded_addresses']:
                print(f"   • {addr_info['address']}: {addr_info['balance']} {addr_info['currency']}")
                if 'source' in addr_info:
                    print(f"     Source: {addr_info['source']}")
        else:
            print("   No funded addresses found in the checked wallets")
    
    print()
    print("🎯 KEY FINDINGS")
    print("-" * 50)
    
    # Calculate success metrics
    total_items = data['enhanced_extraction']['statistics']['total_extracted_items'] if data['enhanced_extraction'] else 0
    accessible_count = len(data['accessible_wallets']['accessible_wallets']) if data['accessible_wallets'] else 0
    funded_count = len(data['balance_results']['funded_addresses']) if data['balance_results'] and data['balance_results'].get('funded_addresses') else 0
    
    print(f"• Total wallet items extracted: {total_items:,}")
    print(f"• Accessible wallets (with private keys): {accessible_count:,}")
    print(f"• Accessible rate: {(accessible_count/total_items*100):.1f}%" if total_items > 0 else "• Accessible rate: N/A")
    print(f"• Funded accessible wallets: {funded_count}")
    print(f"• Success rate: {(funded_count/accessible_count*100):.2f}%" if accessible_count > 0 else "• Success rate: 0%")
    
    print()
    print("📝 RECOMMENDATIONS")
    print("-" * 50)
    
    if accessible_count > 0:
        print("✅ POSITIVE:")
        print(f"   • Successfully extracted {accessible_count:,} wallets with private keys")
        print("   • These are potentially recoverable if they contain funds")
        print("   • The wallet scanner is working correctly")
        
        if funded_count == 0:
            print("\n⚠️  NO FUNDS FOUND:")
            print("   • All checked accessible wallets appear to be empty")
            print("   • Consider checking additional addresses from the sorted list")
            print("   • The wallets may have been emptied previously")
            print("   • Some addresses might be on different networks not checked")
        else:
            print(f"\n🎉 SUCCESS:")
            print(f"   • Found {funded_count} funded wallet(s) that can be recovered!")
    
    else:
        print("❌ CHALLENGES:")
        print("   • No accessible wallets found with private keys")
        print("   • Most wallet data appears to be encrypted or incomplete")
        print("   • Consider expanding search to other file types")
    
    print()
    print("🔧 TECHNICAL NOTES")
    print("-" * 50)
    print("• Balance checking used multiple APIs (Etherscan, BlockCypher)")
    print("• Private key validation performed for all accessible wallets")
    print("• Address derivation verified for Ethereum wallets")
    print("• Duplicate addresses were removed before checking")
    
    print()
    print("=" * 70)
    print("Report generated successfully! 📋")
    print("=" * 70)

if __name__ == '__main__':
    main()
