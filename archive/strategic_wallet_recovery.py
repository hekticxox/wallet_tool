#!/usr/bin/env python3
"""
Strategic Wallet Recovery - Focus on Most Promising Wallets
==========================================================
Targets the highest likelihood accessible wallets for balance checking.
"""

import json
import logging
from collections import defaultdict
from unified_wallet_scanner import UnifiedWalletScanner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('strategic_recovery.log'),
        logging.StreamHandler()
    ]
)

def load_accessible_wallets():
    """Load accessible wallets and prioritize them."""
    try:
        with open('accessible_wallets_report.json', 'r') as f:
            data = json.load(f)
        return data['accessible_wallets']
    except Exception as e:
        print(f"❌ Error loading accessible wallets: {e}")
        return []

def score_wallet_promise(wallet):
    """Score a wallet based on likelihood indicators."""
    score = 0
    
    # More private keys = higher chance
    keys_count = len(wallet.get('private_keys', []))
    score += keys_count * 2
    
    # Mnemonic presence
    if wallet.get('mnemonic'):
        score += 10
    
    # Source file indicators (prioritize certain file types)
    source = wallet.get('source', '').lower()
    
    if 'wallet' in source:
        score += 15
    elif 'metamask' in source or 'ethereum' in source:
        score += 12
    elif 'bitcoin' in source or 'btc' in source:
        score += 10
    elif 'crypto' in source:
        score += 8
    elif 'password' in source:
        score += 5
    elif 'autofill' in source:
        score += 3
    elif 'cookie' in source:
        score += 1
    
    # Penalize very short keys (likely not real)
    for key in wallet.get('private_keys', []):
        if len(key) < 20:
            score -= 1
    
    return score

def extract_unique_addresses_from_wallets(wallets, limit=1000):
    """Extract and deduplicate addresses from top scoring wallets."""
    print(f"🎯 Targeting top {limit} most promising accessible wallets...")
    
    # Score and sort wallets
    scored_wallets = []
    for wallet in wallets:
        score = score_wallet_promise(wallet)
        if score > 0:  # Only include wallets with positive scores
            scored_wallets.append((score, wallet))
    
    scored_wallets.sort(key=lambda x: x[0], reverse=True)
    
    print(f"📊 Wallet scoring complete:")
    print(f"   • Total accessible wallets: {len(wallets):,}")
    print(f"   • Wallets with positive scores: {len(scored_wallets):,}")
    
    if scored_wallets:
        top_score = scored_wallets[0][0]
        print(f"   • Highest score: {top_score}")
        print(f"   • Processing top {min(limit, len(scored_wallets))} wallets")
    
    # Extract addresses from top wallets
    address_sources = {}
    processed = 0
    
    for score, wallet in scored_wallets[:limit]:
        if processed % 50 == 0 and processed > 0:
            print(f"   Processed {processed}/{min(limit, len(scored_wallets))} wallets...")
        
        # Add addresses from the wallet
        for addr in wallet.get('addresses', []):
            if len(addr) >= 26 and addr not in address_sources:  # Basic address validation
                address_sources[addr] = {
                    'source': wallet.get('source', 'unknown'),
                    'score': score,
                    'private_keys_count': len(wallet.get('private_keys', [])),
                    'has_mnemonic': bool(wallet.get('mnemonic'))
                }
        
        processed += 1
        
        if len(address_sources) >= 2000:  # Limit total addresses
            break
    
    print(f"✅ Address extraction complete:")
    print(f"   • Unique addresses found: {len(address_sources):,}")
    
    return address_sources

def main():
    """Main strategic recovery process."""
    print("🎯 STRATEGIC WALLET RECOVERY")
    print("=" * 50)
    print()
    
    # Load accessible wallets
    print("🔍 Loading accessible wallets...")
    wallets = load_accessible_wallets()
    if not wallets:
        print("❌ No accessible wallets found")
        return
    
    print(f"✅ Loaded {len(wallets):,} accessible wallets")
    
    # Extract and prioritize addresses
    address_sources = extract_unique_addresses_from_wallets(wallets, limit=500)
    
    if not address_sources:
        print("❌ No valid addresses extracted")
        return
    
    # Initialize scanner
    print("\n🚀 Initializing balance checker...")
    try:
        scanner = UnifiedWalletScanner()
        print("✅ Scanner initialized")
    except Exception as e:
        print(f"❌ Scanner initialization failed: {e}")
        return
    
    # Check balances
    print(f"\n💰 Checking balances for {len(address_sources):,} prioritized addresses...")
    
    funded_addresses = []
    checked_count = 0
    
    for address, source_info in address_sources.items():
        checked_count += 1
        
        if checked_count % 100 == 0:
            print(f"   Progress: {checked_count:,}/{len(address_sources):,}")
        
        try:
            # Check balance using the unified scanner
            result = scanner.process_address(address)
            
            if result and result.get('balance_info'):
                balance_info = result['balance_info']
                if balance_info.get('has_balance'):
                    print(f"💎 FUNDED ADDRESS FOUND!")
                    print(f"   Address: {address}")
                    print(f"   Balance: {balance_info.get('balance')} {balance_info.get('currency', 'unknown')}")
                    print(f"   Source: {source_info['source']}")
                    print(f"   Wallet score: {source_info['score']}")
                    
                    funded_addresses.append({
                        'address': address,
                        'balance': balance_info.get('balance'),
                        'currency': balance_info.get('currency'),
                        'source': source_info['source'],
                        'wallet_score': source_info['score'],
                        'private_keys_count': source_info['private_keys_count'],
                        'has_mnemonic': source_info['has_mnemonic']
                    })
        
        except Exception as e:
            if checked_count % 500 == 0:  # Only log occasionally
                logging.warning(f"Error checking {address}: {e}")
    
    # Generate results
    print(f"\n📊 STRATEGIC RECOVERY RESULTS")
    print("=" * 50)
    print(f"• Addresses checked: {checked_count:,}")
    print(f"• Funded addresses found: {len(funded_addresses)}")
    
    if funded_addresses:
        print(f"\n💎 FUNDED ADDRESSES:")
        for addr_info in funded_addresses:
            print(f"   • {addr_info['address']}")
            print(f"     Balance: {addr_info['balance']} {addr_info['currency']}")
            print(f"     Source: {addr_info['source']}")
            print(f"     Wallet Score: {addr_info['wallet_score']}")
            print(f"     Private Keys: {addr_info['private_keys_count']}")
            print(f"     Has Mnemonic: {addr_info['has_mnemonic']}")
            print()
    
    else:
        print("\n😔 No funded addresses found")
        print("💡 Possible reasons:")
        print("   • All wallets have been emptied")
        print("   • Addresses are on networks not checked")
        print("   • Private keys may not correspond to found addresses")
        print("   • May need to check additional wallet sources")
    
    # Save results
    results = {
        'summary': {
            'addresses_checked': checked_count,
            'funded_addresses_found': len(funded_addresses),
            'success_rate': len(funded_addresses) / checked_count * 100 if checked_count > 0 else 0
        },
        'funded_addresses': funded_addresses,
        'methodology': 'Strategic prioritization of accessible wallets by scoring'
    }
    
    with open('strategic_recovery_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved to strategic_recovery_results.json")
    print("=" * 50)

if __name__ == '__main__':
    main()
