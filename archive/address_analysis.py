#!/usr/bin/env python3
"""
Address Analysis - Understanding what we extracted
================================================
Analyzes the types and quality of addresses found.
"""

import json
import re
from collections import Counter, defaultdict

def analyze_address_format(addr):
    """Determine the likely format/type of an address."""
    if not addr:
        return "empty"
    
    addr = addr.strip()
    
    # Ethereum addresses
    if re.match(r'^0x[a-fA-F0-9]{40}$', addr):
        return "ethereum"
    
    # Bitcoin Legacy (P2PKH)
    if re.match(r'^1[1-9A-HJ-NP-Za-km-z]{25,34}$', addr):
        return "bitcoin_legacy"
    
    # Bitcoin P2SH
    if re.match(r'^3[1-9A-HJ-NP-Za-km-z]{25,34}$', addr):
        return "bitcoin_p2sh"
    
    # Bitcoin Bech32
    if re.match(r'^bc1[a-z0-9]{39,59}$', addr.lower()):
        return "bitcoin_bech32"
    
    # Private key patterns
    if re.match(r'^[5KL][1-9A-HJ-NP-Za-km-z]{50,51}$', addr):
        return "bitcoin_wif"
    
    if re.match(r'^[a-fA-F0-9]{64}$', addr):
        return "hex_64"
    
    if re.match(r'^[a-fA-F0-9]{32}$', addr):
        return "hex_32"
    
    # Length-based classification
    if len(addr) >= 50 and len(addr) <= 60:
        return "potential_key"
    elif len(addr) >= 25 and len(addr) <= 45:
        return "potential_address"
    elif len(addr) >= 60:
        return "long_string"
    else:
        return "short_string"

def main():
    """Analyze extracted addresses."""
    print("🔍 ADDRESS ANALYSIS")
    print("=" * 50)
    
    # Load accessible wallets
    try:
        with open('accessible_wallets_report.json', 'r') as f:
            data = json.load(f)
        wallets = data['accessible_wallets']
        print(f"✅ Loaded {len(wallets):,} accessible wallets")
    except Exception as e:
        print(f"❌ Error loading wallets: {e}")
        return
    
    # Analyze all addresses
    all_addresses = []
    all_private_keys = []
    
    for wallet in wallets:
        # Collect addresses
        for addr in wallet.get('addresses', []):
            all_addresses.append(addr)
        
        # Collect private keys
        for key in wallet.get('private_keys', []):
            all_private_keys.append(key)
        
        # Collect mnemonic if present
        if wallet.get('mnemonic'):
            all_private_keys.append(wallet['mnemonic'])
    
    print(f"\n📊 EXTRACTION SUMMARY:")
    print(f"• Total addresses: {len(all_addresses):,}")
    print(f"• Total private keys: {len(all_private_keys):,}")
    print(f"• Unique addresses: {len(set(all_addresses)):,}")
    print(f"• Unique private keys: {len(set(all_private_keys)):,}")
    
    # Analyze address formats
    print(f"\n🏷️  ADDRESS FORMAT ANALYSIS:")
    address_formats = Counter(analyze_address_format(addr) for addr in all_addresses)
    
    for fmt, count in address_formats.most_common():
        percentage = (count / len(all_addresses)) * 100
        print(f"• {fmt}: {count:,} ({percentage:.1f}%)")
    
    # Analyze private key formats
    print(f"\n🔐 PRIVATE KEY FORMAT ANALYSIS:")
    key_formats = Counter(analyze_address_format(key) for key in all_private_keys)
    
    for fmt, count in key_formats.most_common():
        percentage = (count / len(all_private_keys)) * 100
        print(f"• {fmt}: {count:,} ({percentage:.1f}%)")
    
    # Show samples of each type
    print(f"\n📋 SAMPLES BY FORMAT:")
    
    # Group addresses by format
    addr_by_format = defaultdict(list)
    for addr in set(all_addresses):  # Use unique addresses only
        fmt = analyze_address_format(addr)
        if len(addr_by_format[fmt]) < 3:  # Keep only 3 samples per format
            addr_by_format[fmt].append(addr)
    
    for fmt, samples in sorted(addr_by_format.items()):
        print(f"\n• {fmt.upper()} samples:")
        for sample in samples:
            print(f"    {sample}")
    
    # Group private keys by format
    key_by_format = defaultdict(list)
    for key in set(all_private_keys):  # Use unique keys only
        fmt = analyze_address_format(key)
        if len(key_by_format[fmt]) < 3:  # Keep only 3 samples per format
            key_by_format[fmt].append(key)
    
    print(f"\n🔐 PRIVATE KEY SAMPLES:")
    for fmt, samples in sorted(key_by_format.items()):
        print(f"\n• {fmt.upper()} samples:")
        for sample in samples:
            # Truncate long keys for display
            display_sample = sample[:20] + "..." + sample[-10:] if len(sample) > 35 else sample
            print(f"    {display_sample}")
    
    # Quality analysis
    print(f"\n✅ QUALITY INDICATORS:")
    
    # Count valid-looking addresses
    valid_eth = len([a for a in all_addresses if analyze_address_format(a) == "ethereum"])
    valid_btc = len([a for a in all_addresses if analyze_address_format(a).startswith("bitcoin")])
    valid_keys = len([k for k in all_private_keys if analyze_address_format(k) in ["bitcoin_wif", "hex_64"]])
    
    print(f"• Valid Ethereum addresses: {valid_eth:,}")
    print(f"• Valid Bitcoin addresses: {valid_btc:,}")
    print(f"• Valid private keys: {valid_keys:,}")
    
    # Source file analysis
    print(f"\n📁 SOURCE FILE ANALYSIS:")
    source_types = Counter()
    
    for wallet in wallets:
        source = wallet.get('source', '').lower()
        if 'cookie' in source:
            source_types['cookies'] += 1
        elif 'history' in source:
            source_types['history'] += 1
        elif 'password' in source:
            source_types['passwords'] += 1
        elif 'autofill' in source:
            source_types['autofills'] += 1
        elif 'wallet' in source:
            source_types['wallet_files'] += 1
        else:
            source_types['other'] += 1
    
    for source_type, count in source_types.most_common():
        print(f"• {source_type}: {count:,} wallets")
    
    print(f"\n" + "=" * 50)
    print("Analysis complete! 📊")

if __name__ == '__main__':
    main()
