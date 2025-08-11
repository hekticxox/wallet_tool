#!/usr/bin/env python3
"""
Fast Accessible Wallet Balance Checker
Uses the existing unified scanner for efficient batch processing
"""

import json
import time
from unified_wallet_scanner import UnifiedWalletScanner

def main():
    """Fast balance checking for accessible wallets"""
    
    # Load accessible wallets
    print("🔍 Loading accessible wallets...")
    try:
        with open('accessible_wallets_report.json', 'r') as f:
            data = json.load(f)
        accessible_wallets = data['accessible_wallets']
        print(f"✅ Loaded {len(accessible_wallets)} accessible wallets")
    except Exception as e:
        print(f"❌ Error loading accessible wallets: {e}")
        return
    
    # Extract all unique addresses and private keys
    addresses_to_check = []
    private_key_map = {}  # Map addresses to their private keys
    seen_addresses = set()  # For fast deduplication
    
    print("📝 Extracting addresses and private keys...")
    
    # Limit to top wallets for faster processing
    max_wallets = min(100, len(accessible_wallets))  # Process top 100 wallets
    print(f"   Processing top {max_wallets} accessible wallets for speed")
    
    for i, wallet in enumerate(accessible_wallets[:max_wallets]):
        if i % 25 == 0:
            print(f"   Processing wallet {i+1}/{max_wallets}")
            
        source = wallet['source']
        
        # Add addresses from the wallet
        for addr in wallet.get('addresses', []):
            if addr not in seen_addresses:
                seen_addresses.add(addr)
                addresses_to_check.append({
                    'address': addr,
                    'chain': 'auto',  # Auto-detect
                    'source': source,
                    'type': 'address'
                })
        
        # For private keys, derive addresses if possible (limit to hex keys only)
        for pk in wallet.get('private_keys', []):
            if len(pk) == 64 and all(c in '0123456789abcdefABCDEF' for c in pk):
                try:
                    from eth_keys import keys
                    from eth_utils import to_checksum_address
                    
                    private_key_obj = keys.PrivateKey(bytes.fromhex(pk))
                    eth_address = to_checksum_address(private_key_obj.public_key.to_address())
                    
                    # Add this derived address if not seen
                    if eth_address not in seen_addresses:
                        seen_addresses.add(eth_address)
                        addresses_to_check.append({
                            'address': eth_address,
                            'chain': 'ethereum',
                            'source': f"{source} (derived)",
                            'type': 'private_key_derived'
                        })
                        
                        # Map the private key to this address
                        private_key_map[eth_address] = pk
                    
                except Exception as e:
                    pass  # Skip invalid keys silently for speed
    
    print(f"📊 Total addresses to check: {len(addresses_to_check)}")
    
    # Initialize the unified scanner
    print("🚀 Initializing unified scanner...")
    scanner = UnifiedWalletScanner()
    
    # Check balances using the unified scanner
    print("💰 Checking balances with batch processing...")
    results = []
    
    for i, addr_info in enumerate(addresses_to_check):
        if i % 50 == 0:
            print(f"   Checking addresses {i+1}/{len(addresses_to_check)}")
        
        address = addr_info['address']
        chain = addr_info['chain']
        
        # Use the unified scanner to check balance
        result = scanner.process_address(address, chain)
        
        if result:
            result['source'] = addr_info['source']
            result['type'] = addr_info['type']
            results.append(result)
    
    # Filter for funded addresses
    funded_results = []
    for result in results:
        if result.get('has_balance', False) and result.get('balance', 0) > 0:
            # Add private key info if available
            address = result['address']
            if address in private_key_map:
                result['private_key'] = private_key_map[address]
                result['accessible'] = True
            else:
                result['accessible'] = False
            funded_results.append(result)
    
    # Generate report
    print("\n" + "="*70)
    print("💰 FAST ACCESSIBLE WALLET BALANCE RESULTS")
    print("="*70)
    
    if funded_results:
        print(f"🎉 Found {len(funded_results)} funded addresses!")
        print()
        
        total_value_usd = 0
        
        for i, result in enumerate(funded_results, 1):
            balance = result.get('balance', 0)
            balance_usd = result.get('balance_usd', 0)
            chain = result.get('chain', 'unknown')
            accessible = result.get('accessible', False)
            
            print(f"{i}. {result['address']}")
            print(f"   Chain: {chain.upper()}")
            print(f"   Balance: {balance} {chain.upper()}")
            print(f"   Value: ${balance_usd:.2f}")
            print(f"   Accessible: {'✅ YES' if accessible else '❌ No private key'}")
            if accessible:
                pk = result.get('private_key', '')
                print(f"   Private Key: {pk[:10]}...{pk[-10:] if len(pk) > 20 else pk}")
            print(f"   Source: {result.get('source', 'unknown')}")
            print()
            
            total_value_usd += balance_usd
        
        print(f"💰 Total Value: ${total_value_usd:.2f}")
        
        # Count accessible vs non-accessible
        accessible_count = sum(1 for r in funded_results if r.get('accessible', False))
        print(f"🔑 Accessible wallets: {accessible_count}/{len(funded_results)}")
        
        # Save results
        report_data = {
            'summary': {
                'total_funded': len(funded_results),
                'accessible_funded': accessible_count,
                'total_value_usd': total_value_usd,
                'scan_date': time.strftime('%Y-%m-%d %H:%M:%S')
            },
            'funded_addresses': funded_results
        }
        
        with open('fast_accessible_balance_results.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"💾 Results saved to: fast_accessible_balance_results.json")
        
        if accessible_count > 0:
            print(f"\n🚨 IMMEDIATE ACTION REQUIRED:")
            print(f"   Found {accessible_count} accessible funded wallets!")
            print(f"   These can be accessed immediately with the private keys provided.")
    
    else:
        print("😔 No funded addresses found")
        print("💡 This could mean:")
        print("   • The addresses have been emptied")
        print("   • The private keys don't match the addresses")
        print("   • Network connectivity issues")
    
    print("="*70)

if __name__ == "__main__":
    main()
