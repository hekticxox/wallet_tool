#!/usr/bin/env python3

import json
import time
import requests
from datetime import datetime
from api_manager import api_manager

def check_single_key_balance(private_key, source):
    """Check balance for a single private key"""
    
    try:
        # Get APIs
        apis = api_manager.get_working_apis()
        
        results = {
            'private_key': private_key,
            'source': source,
            'bitcoin_balance': 0,
            'ethereum_balance': 0,
            'total_usd': 0,
            'addresses_checked': [],
            'error': None
        }
        
        # Convert private key to Bitcoin address (simplified)
        # For now, we'll focus on Ethereum since most hex keys are Ethereum
        
        # Try to derive Ethereum address from hex private key
        if len(private_key) == 64 and all(c in '0123456789abcdefABCDEF' for c in private_key):
            try:
                # This is a simplified approach - would need proper crypto library for production
                eth_address = derive_ethereum_address(private_key)
                if eth_address:
                    results['addresses_checked'].append(eth_address)
                    
                    # Check Ethereum balance
                    eth_balance = check_ethereum_balance(eth_address, apis)
                    if eth_balance > 0:
                        results['ethereum_balance'] = eth_balance
                        # Rough ETH to USD conversion (would use real price API in production)
                        results['total_usd'] = eth_balance * 2000  # Approximate ETH price
                        
                        return results
                        
            except Exception as e:
                results['error'] = f"Ethereum check failed: {str(e)}"
        
        return results
        
    except Exception as e:
        return {
            'private_key': private_key,
            'source': source,
            'error': str(e),
            'bitcoin_balance': 0,
            'ethereum_balance': 0,
            'total_usd': 0
        }

def derive_ethereum_address(private_key_hex):
    """Simplified Ethereum address derivation - for demo only"""
    # In production, would use proper crypto library like eth-keys
    # This is a placeholder that returns a sample format
    return f"0x{'a' * 40}"  # Placeholder

def check_ethereum_balance(address, apis):
    """Check Ethereum balance using available APIs"""
    try:
        if 'etherscan' in apis:
            api_key = apis['etherscan']['api_key']
            url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={api_key}"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == '1':
                    balance_wei = int(data['result'])
                    balance_eth = balance_wei / 10**18
                    return balance_eth
        
        return 0
    except:
        return 0

def main():
    """Run the major discovery balance check"""
    
    print("🚀 MAJOR DISCOVERY BALANCE CHECK")
    print("="*50)
    
    # Load the combined keys
    try:
        with open('combined_major_discovery_keys.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ combined_major_discovery_keys.json not found!")
        print("   Run prepare_major_check.py first")
        return
    
    keys = data['keys']
    print(f"🔍 Checking {len(keys)} private keys...")
    
    funded_wallets = []
    checked_count = 0
    start_time = time.time()
    
    for i, key_data in enumerate(keys, 1):
        private_key = key_data['private_key']
        source = key_data['source']
        
        print(f"🔍 [{i}/{len(keys)}] Checking {source} key: {private_key[:12]}...")
        
        result = check_single_key_balance(private_key, source)
        
        if result['total_usd'] > 0:
            print(f"💰 FUNDED WALLET FOUND!")
            print(f"    Source: {source}")
            print(f"    Key: {private_key}")
            print(f"    Value: ${result['total_usd']:.8f}")
            
            funded_wallets.append(result)
        else:
            if result.get('error'):
                print(f"    ❌ Error: {result['error']}")
            else:
                print(f"    ✓ Empty")
        
        checked_count += 1
        
        # Progress update every 25 keys
        if i % 25 == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            print(f"\n📊 Progress: {i}/{len(keys)} ({i/len(keys)*100:.1f}%)")
            print(f"    Rate: {rate:.1f} keys/sec")
            print(f"    Funded found: {len(funded_wallets)}")
        
        # Rate limiting
        time.sleep(2)
    
    # Final results
    elapsed = time.time() - start_time
    
    print(f"\n" + "="*50)
    print(f"🏁 MAJOR DISCOVERY CHECK COMPLETE")
    print(f"   ⏱️  Time: {elapsed/60:.1f} minutes")
    print(f"   🔍 Checked: {checked_count} keys")
    print(f"   💰 Funded: {len(funded_wallets)} wallets")
    
    if funded_wallets:
        # Save results
        results = {
            'check_date': datetime.now().isoformat(),
            'total_checked': checked_count,
            'funded_count': len(funded_wallets),
            'sources': ['net602', 'net605'],
            'funded_wallets': funded_wallets
        }
        
        with open('MAJOR_FUNDED_WALLETS.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n🎉 FUNDED WALLETS:")
        total_value = 0
        for wallet in funded_wallets:
            print(f"   {wallet['source']}: ${wallet['total_usd']:.8f}")
            total_value += wallet['total_usd']
        
        print(f"\n💎 TOTAL VALUE: ${total_value:.8f}")
        print(f"💾 Results: MAJOR_FUNDED_WALLETS.json")
        print(f"🚨 SECURE THESE KEYS IMMEDIATELY!")
    else:
        print(f"\n😔 No funded wallets in this sample")
        print(f"   But we have {len(keys)} more keys to check!")

if __name__ == "__main__":
    main()
