#!/usr/bin/env python3
"""
Batch Balance Checker for Accessible Wallets
Checks balances for addresses where we have private keys
"""

import json
import time
from enhanced_balance_checker import EnhancedBalanceChecker

def main():
    print("🔍 BATCH BALANCE CHECK FOR ACCESSIBLE WALLETS")
    print("=" * 60)
    
    # Load accessible wallets
    try:
        with open('accessible_wallets_report.json', 'r') as f:
            accessible_data = json.load(f)
    except FileNotFoundError:
        print("❌ accessible_wallets_report.json not found!")
        return
    
    # Extract all addresses from accessible wallets
    all_addresses = []
    address_to_private_key = {}
    
    for wallet in accessible_data['accessible_wallets']:
        private_keys = wallet.get('private_keys', [])
        addresses = wallet.get('addresses', [])
        
        # Map addresses to their private keys
        for i, addr in enumerate(addresses):
            if addr and len(addr) > 20:  # Filter valid addresses
                all_addresses.append(addr)
                if i < len(private_keys):
                    address_to_private_key[addr] = private_keys[i]
    
    print(f"📊 Found {len(all_addresses)} addresses from accessible wallets")
    print(f"🔑 {len(address_to_private_key)} addresses have associated private keys")
    
    # Check balances in batches
    checker = EnhancedBalanceChecker()
    batch_size = 100
    funded_addresses = []
    
    # Check more addresses this time - up to 5000
    addresses_to_check = min(5000, len(all_addresses))
    print(f"🎯 Will check {addresses_to_check} addresses in batches of {batch_size}")
    
    for i in range(0, addresses_to_check, batch_size):
        batch = all_addresses[i:i+batch_size]
        print(f"\n🔍 Checking batch {i//batch_size + 1}: addresses {i+1} to {min(i+batch_size, addresses_to_check)}")
        
        results = checker.check_multiple_addresses(batch)
        
        for result in results:
            if result['success'] and result.get('balance', 0) > 0:
                funded_addresses.append({
                    'address': result['address'],
                    'balance': result['balance'],
                    'chain': result['chain'],
                    'private_key': address_to_private_key.get(result['address'], 'Not found'),
                    'api_used': result.get('api', 'unknown')
                })
                print(f"� FUNDED: {result['address']} = {result['balance']} {result['chain'].upper()}")
                print(f"    🔑 Private Key: {address_to_private_key.get(result['address'], 'Not found')[:20]}...")
        
        # Rate limiting - slightly faster
        time.sleep(1)
    
    # Summary
    print(f"\n" + "=" * 60)
    print("📊 BATCH BALANCE CHECK RESULTS")
    print("=" * 60)
    print(f"Addresses checked: {addresses_to_check}")
    print(f"Funded addresses found: {len(funded_addresses)}")
    
    if funded_addresses:
        print(f"\n💎 FUNDED ADDRESSES WITH PRIVATE KEYS:")
        total_eth = 0
        total_btc = 0
        
        for funded in funded_addresses:
            print(f"\n🎯 {funded['address']}")
            print(f"   Balance: {funded['balance']} {funded['chain'].upper()}")
            print(f"   Private Key: {funded['private_key'][:20]}...{funded['private_key'][-20:] if len(funded['private_key']) > 40 else funded['private_key']}")
            print(f"   API Used: {funded['api_used']}")
            
            if funded['chain'] == 'ethereum':
                total_eth += funded['balance']
            elif funded['chain'] == 'bitcoin':
                total_btc += funded['balance']
        
        print(f"\n💰 TOTAL VALUES:")
        if total_eth > 0:
            print(f"   Ethereum: {total_eth:.6f} ETH")
        if total_btc > 0:
            print(f"   Bitcoin: {total_btc:.8f} BTC")
        
        # Save results
        with open('funded_accessible_wallets.json', 'w') as f:
            json.dump({
                'scan_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'addresses_checked': min(500, len(all_addresses)),
                'funded_count': len(funded_addresses),
                'funded_addresses': funded_addresses,
                'totals': {
                    'ethereum': total_eth,
                    'bitcoin': total_btc
                }
            }, f, indent=2)
        
        print(f"\n💾 Results saved to: funded_accessible_wallets.json")
    else:
        print("\n✅ No funded addresses found in the checked batch")
        print("💡 Consider checking more addresses or different batches")

if __name__ == '__main__':
    main()
