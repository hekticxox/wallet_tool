#!/usr/bin/env python3
"""
Web3 Balance Checker - Direct blockchain query without API key
"""

from web3 import Web3
import json
import time

def check_balances_web3():
    """Check balances using public RPC endpoints"""
    
    funded_addresses = [
        "0x6e59e2a98d12f45ab5872942fe45a1036b1ea9c9",
        "0x8bd210f4a679eced866b725a85ba75a2c158f651"
    ]
    
    # Try multiple public RPC endpoints
    rpc_endpoints = [
        "https://ethereum.publicnode.com",
        "https://rpc.ankr.com/eth",
        "https://eth.llamarpc.com",
        "https://1rpc.io/eth"
    ]
    
    print("🔍 WEB3 BALANCE CHECK")
    print("=" * 50)
    
    w3 = None
    working_endpoint = None
    
    # Find a working endpoint
    for endpoint in rpc_endpoints:
        try:
            print(f"Trying endpoint: {endpoint}")
            w3 = Web3(Web3.HTTPProvider(endpoint))
            if w3.is_connected():
                working_endpoint = endpoint
                print(f"✅ Connected to: {endpoint}")
                break
        except Exception as e:
            print(f"❌ Failed: {e}")
            continue
    
    if not w3 or not w3.is_connected():
        print("❌ Could not connect to any RPC endpoint")
        return []
    
    print(f"\n📊 Checking balances via: {working_endpoint}")
    print("=" * 50)
    
    results = []
    total_value_wei = 0
    
    for i, address in enumerate(funded_addresses, 1):
        print(f"\n{i}. Checking: {address}")
        
        try:
            # Convert address to checksum format
            checksum_address = Web3.to_checksum_address(address)
            
            # Get balance in wei
            balance_wei = w3.eth.get_balance(checksum_address)
            balance_eth = balance_wei / 1e18
            
            print(f"   💰 Balance: {balance_eth:.8f} ETH")
            print(f"   💰 Wei: {balance_wei}")
            
            if balance_wei > 0:
                total_value_wei += balance_wei
                print(f"   ✅ FUNDED ADDRESS - Contains value!")
                
                # Try to get current block for context
                try:
                    current_block = w3.eth.block_number
                    print(f"   📦 Current block: {current_block}")
                except:
                    pass
            else:
                print(f"   ⚪ Empty address")
            
            results.append({
                'address': address,
                'balance_wei': balance_wei,
                'balance_eth': balance_eth,
                'has_balance': balance_wei > 0,
                'checksum_address': checksum_address
            })
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                'address': address,
                'error': str(e),
                'has_balance': False
            })
        
        # Small delay between requests
        if i < len(funded_addresses):
            time.sleep(0.5)
    
    print(f"\n{'='*50}")
    print("📊 FINAL WEB3 SUMMARY:")
    print(f"{'='*50}")
    
    funded_count = sum(1 for r in results if r.get('has_balance', False))
    total_eth = total_value_wei / 1e18
    
    print(f"RPC Endpoint: {working_endpoint}")
    print(f"Addresses checked: {len(funded_addresses)}")
    print(f"Addresses with funds: {funded_count}")
    print(f"Total ETH value: {total_eth:.8f} ETH")
    print(f"Total Wei value: {total_value_wei}")
    
    if funded_count > 0:
        print(f"\n🎯 RECOVERY STATUS: ACTIVE")
        print(f"   Found {funded_count} address(es) with funds!")
        print(f"   Total value: {total_eth:.8f} ETH")
        print(f"   ⚠️  URGENT: Continue private key search immediately")
    else:
        print(f"\n⚠️  RECOVERY STATUS: EMPTY")
        print(f"   No funds detected in target addresses")
        print(f"   May have been moved or never funded")
    
    # Save results
    web3_data = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'rpc_endpoint': working_endpoint,
        'addresses': results,
        'total_eth': total_eth,
        'total_wei': total_value_wei,
        'funded_count': funded_count
    }
    
    with open('web3_balance_check.json', 'w') as f:
        json.dump(web3_data, f, indent=2)
    
    print(f"\n💾 Results saved to: web3_balance_check.json")
    
    return results

if __name__ == "__main__":
    results = check_balances_web3()
