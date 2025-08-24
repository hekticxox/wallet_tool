#!/usr/bin/env python3
"""
Final Balance Verification for Funded Addresses
Double-check current balances before concluding the analysis
"""

import requests
import json
import time
import os

def check_final_balances():
    """Check final balances of the funded addresses"""
    
    # Get API key from environment
    api_key = os.getenv('ETHERSCAN_API_KEY')
    if not api_key:
        print("⚠️  No ETHERSCAN_API_KEY found in environment")
        print("Using public API with rate limits...")
        api_key = ""
    
    funded_addresses = [
        "0x6e59e2a98d12f45ab5872942fe45a1036b1ea9c9",
        "0x8bd210f4a679eced866b725a85ba75a2c158f651"
    ]
    
    print("🔍 FINAL BALANCE VERIFICATION")
    print("=" * 50)
    
    results = []
    total_value_wei = 0
    
    for i, address in enumerate(funded_addresses, 1):
        print(f"\n{i}. Checking: {address}")
        
        try:
            # Check ETH balance
            url = f"https://api.etherscan.io/api"
            params = {
                'module': 'account',
                'action': 'balance',
                'address': address,
                'tag': 'latest',
                'apikey': api_key
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data['status'] == '1':
                balance_wei = int(data['result'])
                balance_eth = balance_wei / 1e18
                
                print(f"   💰 Balance: {balance_eth:.6f} ETH ({balance_wei} wei)")
                
                if balance_wei > 0:
                    total_value_wei += balance_wei
                    
                    # Get current ETH price
                    try:
                        price_url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
                        price_response = requests.get(price_url)
                        price_data = price_response.json()
                        eth_price = price_data['ethereum']['usd']
                        value_usd = balance_eth * eth_price
                        
                        print(f"   💵 USD Value: ${value_usd:.2f} (ETH @ ${eth_price:.2f})")
                        
                    except Exception as e:
                        print(f"   ❌ Could not get USD value: {e}")
                
                results.append({
                    'address': address,
                    'balance_wei': balance_wei,
                    'balance_eth': balance_eth,
                    'has_balance': balance_wei > 0
                })
                
            else:
                print(f"   ❌ Error: {data.get('message', 'Unknown error')}")
                results.append({
                    'address': address,
                    'error': data.get('message', 'API error'),
                    'has_balance': False
                })
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            results.append({
                'address': address,
                'error': str(e),
                'has_balance': False
            })
        
        # Rate limiting
        if i < len(funded_addresses):
            time.sleep(0.2)  # 200ms delay between requests
    
    print(f"\n{'='*50}")
    print("📊 FINAL SUMMARY:")
    print(f"{'='*50}")
    
    funded_count = sum(1 for r in results if r.get('has_balance', False))
    total_eth = total_value_wei / 1e18
    
    print(f"Addresses checked: {len(funded_addresses)}")
    print(f"Addresses with funds: {funded_count}")
    print(f"Total ETH value: {total_eth:.6f} ETH")
    
    if total_value_wei > 0:
        print(f"Total Wei value: {total_value_wei}")
        print("\n🎯 RECOVERY PRIORITY: HIGH")
        print("   These addresses contain actual value and warrant continued recovery efforts.")
    else:
        print("\n⚠️  RECOVERY PRIORITY: LOW") 
        print("   No current balance found - addresses may have been emptied.")
    
    print("\n📝 NEXT STEPS RECOMMENDATION:")
    if funded_count > 0:
        print("1. Continue extended search for private keys")
        print("2. Search for mnemonic phrases in additional data files")  
        print("3. Check for wallet backup files or keystore data")
        print("4. Monitor addresses for any new activity")
    else:
        print("1. Verify addresses were previously funded (transaction history)")
        print("2. Check if funds were recently moved")
        print("3. Consider if recovery effort is still worthwhile")
    
    # Save final verification results
    verification_data = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'addresses': results,
        'total_eth': total_eth,
        'total_wei': total_value_wei,
        'funded_count': funded_count,
        'recommendation': 'HIGH_PRIORITY' if funded_count > 0 else 'LOW_PRIORITY'
    }
    
    with open('final_balance_verification.json', 'w') as f:
        json.dump(verification_data, f, indent=2)
    
    print(f"\n💾 Verification saved to: final_balance_verification.json")
    
    return results

if __name__ == "__main__":
    results = check_final_balances()
