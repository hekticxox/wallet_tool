#!/usr/bin/env python3
"""
BATCH BALANCE CHECKER FOR MASSIVE WALLET DISCOVERY
==================================================
Checks balances for a sample of the 361+ private keys found
"""

import json
import requests
import time
import random

def load_wallet_data():
    """Load the massive wallet discovery data"""
    with open('detected_wallet_data_summary.json', 'r') as f:
        return json.load(f)

def check_sample_balances(data, sample_size=20):
    """Check balances for a random sample of addresses"""
    
    print(f"🔍 CHECKING SAMPLE OF {sample_size} ADDRESSES FROM 361+ KEYS")
    print("=" * 60)
    
    # Get random samples
    eth_addrs = random.sample(data['detected_addresses']['ethereum'], 
                            min(sample_size, len(data['detected_addresses']['ethereum'])))
    btc_addrs = random.sample(data['detected_addresses']['bitcoin'],
                            min(sample_size, len(data['detected_addresses']['bitcoin'])))
    
    funds_found = []
    
    print("\n💎 ETHEREUM SAMPLE CHECK:")
    print("-" * 30)
    for i, addr in enumerate(eth_addrs[:10], 1):  # Check first 10
        print(f"Address #{i}: {addr}")
        try:
            # Free Etherscan API call
            url = f"https://api.etherscan.io/api?module=account&action=balance&address={addr}&tag=latest"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == '1':
                    wei = int(result['result'])
                    eth = wei / 1e18
                    print(f"  💰 Balance: {eth:.6f} ETH")
                    if eth > 0:
                        funds_found.append(('ETH', addr, eth))
                        print(f"  🎉 FUNDS FOUND! {eth} ETH")
                else:
                    print(f"  ❓ API Error: {result.get('message', 'Unknown')}")
            time.sleep(0.2)  # Rate limiting
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print(f"\n₿ BITCOIN SAMPLE CHECK:")
    print("-" * 30)
    for i, addr in enumerate(btc_addrs[:10], 1):  # Check first 10  
        print(f"Address #{i}: {addr}")
        try:
            url = f"https://blockchain.info/q/addressbalance/{addr}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                satoshi = int(response.text)
                btc = satoshi / 1e8
                print(f"  💰 Balance: {btc:.8f} BTC")
                if btc > 0:
                    funds_found.append(('BTC', addr, btc))
                    print(f"  🎉 FUNDS FOUND! {btc} BTC")
            elif response.status_code == 429:
                print("  ⏳ Rate limited, skipping...")
                time.sleep(2)
            else:
                print(f"  ❓ HTTP {response.status_code}")
            time.sleep(1)  # Rate limiting for Bitcoin API
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SAMPLE BALANCE CHECK SUMMARY:")
    print("=" * 60)
    
    if funds_found:
        print(f"🎉 FUNDS DISCOVERED! Found {len(funds_found)} addresses with balances:")
        total_value = 0
        for crypto, addr, balance in funds_found:
            print(f"  {crypto}: {addr} = {balance}")
        print(f"\n💰 This is just a sample! You have 361 private keys to check!")
    else:
        print("💡 No funds found in this sample, but you still have 300+ more addresses to check!")
        print("   Try checking more addresses or different samples.")
    
    print(f"\n🔢 STATISTICS:")
    print(f"   Total Private Keys: {len(data['private_keys'])}")
    print(f"   Total Ethereum Addresses: {len(data['detected_addresses']['ethereum'])}")  
    print(f"   Total Bitcoin Addresses: {len(data['detected_addresses']['bitcoin'])}")
    print(f"   Total Solana Addresses: {len(data['detected_addresses']['solana'])}")
    print(f"   Sample Checked: {min(20, len(eth_addrs + btc_addrs))} addresses")
    
    return funds_found

def main():
    print("🎯 MASSIVE WALLET DISCOVERY - BALANCE SAMPLE CHECK")
    print("=" * 60)
    
    try:
        data = load_wallet_data()
        funds = check_sample_balances(data)
        
        # Save results
        sample_results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_keys_available': len(data['private_keys']),
            'sample_checked': 20,
            'funds_found': len(funds),
            'addresses_with_funds': funds
        }
        
        with open('sample_balance_check.json', 'w') as f:
            json.dump(sample_results, f, indent=2)
        
        print(f"\n💾 Results saved to sample_balance_check.json")
        
    except FileNotFoundError:
        print("❌ detected_wallet_data_summary.json not found!")
        print("   Run wallet_analysis.py first!")

if __name__ == "__main__":
    main()
