#!/usr/bin/env python3
"""
Final Ethereum Focus - Check the 10 Ethereum addresses we found
==============================================================
Specifically targets the small number of Ethereum addresses for balance checking.
"""

import json
import requests
import time
import re

def is_valid_ethereum_address(address):
    """Check if address is a valid Ethereum address."""
    return bool(re.match(r'^0x[a-fA-F0-9]{40}$', address))

def check_ethereum_balance_etherscan(address, api_key=None):
    """Check Ethereum balance using Etherscan API."""
    try:
        url = "https://api.etherscan.io/api"
        params = {
            'module': 'account',
            'action': 'balance',
            'address': address,
            'tag': 'latest'
        }
        
        if api_key:
            params['apikey'] = api_key
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get('status') == '1' and data.get('result'):
            balance_wei = int(data['result'])
            balance_eth = balance_wei / 10**18
            
            return {
                'success': True,
                'balance_wei': balance_wei,
                'balance_eth': balance_eth,
                'has_balance': balance_wei > 0,
                'api': 'etherscan'
            }
        else:
            return {'success': False, 'error': data.get('message', 'Unknown error')}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

def extract_ethereum_addresses():
    """Extract all Ethereum addresses from accessible wallets."""
    try:
        with open('accessible_wallets_report.json', 'r') as f:
            data = json.load(f)
        wallets = data['accessible_wallets']
    except Exception as e:
        print(f"❌ Error loading wallets: {e}")
        return {}
    
    ethereum_addresses = {}
    
    for wallet in wallets:
        for addr in wallet.get('addresses', []):
            if is_valid_ethereum_address(addr):
                ethereum_addresses[addr] = {
                    'source': wallet.get('source', 'unknown'),
                    'private_keys_count': len(wallet.get('private_keys', [])),
                    'has_mnemonic': bool(wallet.get('mnemonic'))
                }
    
    return ethereum_addresses

def main():
    """Check Ethereum addresses for balances."""
    print("💎 ETHEREUM FOCUS - FINAL CHECK")
    print("=" * 50)
    
    # Extract Ethereum addresses
    eth_addresses = extract_ethereum_addresses()
    
    print(f"🔍 Found {len(eth_addresses)} Ethereum addresses to check:")
    for addr, info in eth_addresses.items():
        print(f"   • {addr} (from {info['source']})")
    
    if not eth_addresses:
        print("❌ No Ethereum addresses found")
        return
    
    print(f"\n💰 Checking balances...")
    
    results = []
    
    for i, (address, info) in enumerate(eth_addresses.items(), 1):
        print(f"   [{i}/{len(eth_addresses)}] Checking {address}...")
        
        # Check balance
        result = check_ethereum_balance_etherscan(address)
        
        if result['success']:
            balance_eth = result['balance_eth']
            print(f"      Balance: {balance_eth:.6f} ETH")
            
            if result['has_balance']:
                print(f"      💎 FUNDED! {balance_eth:.6f} ETH")
                results.append({
                    'address': address,
                    'balance_eth': balance_eth,
                    'balance_wei': result['balance_wei'],
                    'source': info['source'],
                    'private_keys_count': info['private_keys_count'],
                    'has_mnemonic': info['has_mnemonic'],
                    'status': 'FUNDED'
                })
            else:
                results.append({
                    'address': address,
                    'balance_eth': 0,
                    'source': info['source'],
                    'status': 'EMPTY'
                })
        else:
            print(f"      ❌ Error: {result['error']}")
            results.append({
                'address': address,
                'error': result['error'],
                'source': info['source'],
                'status': 'ERROR'
            })
        
        # Rate limiting
        time.sleep(0.5)
    
    # Summary
    print(f"\n📊 FINAL ETHEREUM RESULTS")
    print("=" * 50)
    
    funded_count = len([r for r in results if r['status'] == 'FUNDED'])
    empty_count = len([r for r in results if r['status'] == 'EMPTY'])
    error_count = len([r for r in results if r['status'] == 'ERROR'])
    
    print(f"• Total Ethereum addresses checked: {len(results)}")
    print(f"• Funded addresses: {funded_count}")
    print(f"• Empty addresses: {empty_count}")
    print(f"• Errors: {error_count}")
    
    if funded_count > 0:
        print(f"\n💎 FUNDED ETHEREUM ADDRESSES:")
        total_eth = 0
        for result in results:
            if result['status'] == 'FUNDED':
                print(f"   • {result['address']}")
                print(f"     Balance: {result['balance_eth']:.6f} ETH")
                print(f"     Source: {result['source']}")
                print(f"     Private keys available: {result['private_keys_count']}")
                print(f"     Has mnemonic: {result['has_mnemonic']}")
                print()
                total_eth += result['balance_eth']
        
        print(f"   🎯 TOTAL RECOVERABLE: {total_eth:.6f} ETH")
        
        # Now find the private keys for these addresses
        print(f"\n🔑 FINDING PRIVATE KEYS FOR FUNDED ADDRESSES:")
        
        # This would require matching the addresses to their private keys
        # which would need the original wallet data
        
    else:
        print(f"\n😔 No funded Ethereum addresses found")
        print(f"💡 All Ethereum addresses appear to be empty")
    
    # Save results
    final_results = {
        'summary': {
            'total_checked': len(results),
            'funded_count': funded_count,
            'empty_count': empty_count,
            'error_count': error_count,
            'total_eth_found': sum(r.get('balance_eth', 0) for r in results)
        },
        'addresses': results
    }
    
    with open('final_ethereum_check.json', 'w') as f:
        json.dump(final_results, f, indent=2)
    
    print(f"\n📁 Results saved to final_ethereum_check.json")
    print("=" * 50)

if __name__ == '__main__':
    main()
