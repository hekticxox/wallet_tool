#!/usr/bin/env python3
"""
Check balances for our top likelihood addresses
"""

import json
from enhanced_balance_checker import EnhancedBalanceChecker

def main():
    print("🔍 CHECKING TOP LIKELIHOOD ADDRESSES")
    print("=" * 50)
    
    # Load top addresses
    with open('test_top_addresses.json', 'r') as f:
        addresses = json.load(f)
    
    # Extract just the address strings
    address_list = []
    for addr in addresses:
        if isinstance(addr, dict):
            address_list.append(addr.get('address', addr))
        else:
            address_list.append(addr)
    
    print(f"📊 Checking {len(address_list)} top likelihood addresses...")
    
    checker = EnhancedBalanceChecker()
    results = checker.check_multiple_addresses(address_list)
    
    funded = []
    for result in results:
        if result['success'] and result.get('balance', 0) > 0:
            funded.append(result)
            print(f"💎 FUNDED: {result['address']} = {result['balance']} {result['chain'].upper()}")
    
    print(f"\n📊 RESULTS:")
    print(f"Addresses checked: {len(address_list)}")
    print(f"Funded addresses: {len(funded)}")
    
    if funded:
        print(f"\n💰 FUNDED ADDRESSES:")
        for addr in funded:
            print(f"  {addr['address']}: {addr['balance']} {addr['chain'].upper()}")
        
        # Save results
        with open('funded_top_addresses.json', 'w') as f:
            json.dump(funded, f, indent=2)
        print(f"\n💾 Saved to: funded_top_addresses.json")
    
if __name__ == '__main__':
    main()
