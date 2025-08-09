#!/usr/bin/env python3
"""
Smart Balance Checker - Optimized for Rate Limit Avoidance
- Uses free APIs with generous limits
- Smart delays and caching
- Focus on finding funded addresses quickly
"""

import json
import time
import random
import requests
from pathlib import Path
import sys

def check_sample_addresses(wallet_file: str = "detected_wallet_data_summary.json", sample_size: int = 20):
    """Check a small sample of addresses to find any with funds"""
    
    print("🔍 Smart Balance Checker - Rate Limit Safe")
    print("=" * 50)
    
    # Load wallet data
    try:
        with open(wallet_file, 'r') as f:
            data = json.load(f)
        print(f"✅ Loaded wallet data from {wallet_file}")
    except Exception as e:
        print(f"❌ Error loading {wallet_file}: {e}")
        return
    
    # Sample addresses from each blockchain
    results = {'found_funds': [], 'checked': 0, 'errors': 0}
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    })
    
    # Check Ethereum addresses (using Blockchair - more generous limits)
    if 'detected_addresses' in data and 'ethereum' in data['detected_addresses']:
        eth_addresses = data['detected_addresses']['ethereum']
        if eth_addresses:
            eth_sample = random.sample(eth_addresses, min(sample_size, len(eth_addresses)))
            print(f"\n🔸 Checking {len(eth_sample)} Ethereum addresses...")
            
            for i, address in enumerate(eth_sample, 1):
                print(f"   {i:2d}/{len(eth_sample)} ETH {address[:12]}...", end=' ')
            print(f"   {i:2d}/{len(eth_sample)} ETH {address[:12]}...", end=' ')
            
            try:
                # Use Blockchair (no API key required, generous limits)
                time.sleep(1.5 + random.uniform(0, 1))  # Random delay 1.5-2.5s
                url = f"https://api.blockchair.com/ethereum/dashboards/address/{address}"
                response = session.get(url, timeout=30)
                
                if response.status_code == 200:
                    api_data = response.json()
                    if 'data' in api_data and address in api_data['data']:
                        balance_wei = api_data['data'][address]['address']['balance']
                        balance_eth = float(balance_wei) / 1e18
                        
                        if balance_eth > 0:
                            print(f"💰 {balance_eth:.6f} ETH")
                            results['found_funds'].append({
                                'blockchain': 'ethereum',
                                'address': address,
                                'balance': f"{balance_eth:.6f} ETH",
                                'balance_raw': balance_wei,
                                'private_key': 'Check private_keys array'
                            })
                        else:
                            print("💸 0 ETH")
                    else:
                        print("❓ No data")
                        results['errors'] += 1
                else:
                    print(f"❌ HTTP {response.status_code}")
                    results['errors'] += 1
                    
                results['checked'] += 1
                
            except Exception as e:
                print(f"❌ Error: {str(e)[:30]}")
                results['errors'] += 1
    
    # Check Bitcoin addresses
    if 'detected_addresses' in data and 'bitcoin' in data['detected_addresses']:
        btc_addresses = data['detected_addresses']['bitcoin']
        if btc_addresses:
            btc_sample = random.sample(btc_addresses, min(sample_size, len(btc_addresses)))
            print(f"\n🔸 Checking {len(btc_sample)} Bitcoin addresses...")
            
            for i, address in enumerate(btc_sample, 1):
                print(f"   {i:2d}/{len(btc_sample)} BTC {address[:12]}...", end=' ')
            print(f"   {i:2d}/{len(btc_sample)} BTC {address[:12]}...", end=' ')
            
            try:
                # Use Blockstream API (free, reliable)
                time.sleep(2 + random.uniform(0, 1))  # Random delay 2-3s
                url = f"https://blockstream.info/api/address/{address}"
                response = session.get(url, timeout=30)
                
                if response.status_code == 200:
                    api_data = response.json()
                    funded = api_data.get('chain_stats', {}).get('funded_txo_sum', 0)
                    spent = api_data.get('chain_stats', {}).get('spent_txo_sum', 0)
                    balance_sat = funded - spent
                    balance_btc = balance_sat / 1e8
                    
                    if balance_btc > 0:
                        print(f"💰 {balance_btc:.8f} BTC")
                        results['found_funds'].append({
                            'blockchain': 'bitcoin',
                            'address': address,
                            'balance': f"{balance_btc:.8f} BTC",
                            'balance_raw': balance_sat,
                            'private_key': 'Check private_keys array'
                        })
                    else:
                        print("💸 0 BTC")
                else:
                    print(f"❌ HTTP {response.status_code}")
                    results['errors'] += 1
                    
                results['checked'] += 1
                
            except Exception as e:
                print(f"❌ Error: {str(e)[:30]}")
                results['errors'] += 1
    
    # Quick Solana check (if available)
    if 'detected_addresses' in data and 'solana' in data['detected_addresses']:
        sol_addresses = data['detected_addresses']['solana']
        if sol_addresses:
            sol_sample = random.sample(sol_addresses, min(10, len(sol_addresses)))  # Smaller sample
            print(f"\n🔸 Checking {len(sol_sample)} Solana addresses...")
            
            for i, address in enumerate(sol_sample, 1):
                print(f"   {i:2d}/{len(sol_sample)} SOL {address[:12]}...", end=' ')
            print(f"   {i:2d}/{len(sol_sample)} SOL {address[:12]}...", end=' ')
            
            try:
                time.sleep(1 + random.uniform(0, 0.5))
                
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getBalance",
                    "params": [address]
                }
                
                response = session.post(
                    "https://api.mainnet-beta.solana.com",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    api_data = response.json()
                    if 'result' in api_data and 'value' in api_data['result']:
                        balance_lamports = api_data['result']['value']
                        balance_sol = balance_lamports / 1e9
                        
                        if balance_sol > 0:
                            print(f"💰 {balance_sol:.6f} SOL")
                            results['found_funds'].append({
                                'blockchain': 'solana',
                                'address': address,
                                'balance': f"{balance_sol:.6f} SOL",
                                'balance_raw': balance_lamports,
                                'private_key': 'Check private_keys array'
                            })
                        else:
                            print("💸 0 SOL")
                    else:
                        print("❓ No data")
                        results['errors'] += 1
                else:
                    print(f"❌ HTTP {response.status_code}")
                    results['errors'] += 1
                    
                results['checked'] += 1
                
            except Exception as e:
                print(f"❌ Error: {str(e)[:30]}")
                results['errors'] += 1
    
    # Final summary
    print("\n" + "=" * 50)
    print("📊 BALANCE CHECK SUMMARY")
    print("=" * 50)
    print(f"✅ Total Addresses Checked: {results['checked']}")
    print(f"❌ Errors Encountered: {results['errors']}")
    print(f"💰 Funded Addresses Found: {len(results['found_funds'])}")
    
    if results['found_funds']:
        print("\n🎉 FUNDED ADDRESSES DISCOVERED:")
        print("-" * 40)
        for fund in results['found_funds']:
            print(f"💎 {fund['blockchain'].upper()}: {fund['address']}")
            print(f"   Balance: {fund['balance']}")
            print(f"   Private Key: Check the private_keys array in your JSON file")
            print()
        
        # Save results
        output_file = f"funded_wallets_{int(time.time())}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"💾 Results saved to: {output_file}")
        
    else:
        print("\n💸 No funded addresses found in this sample.")
        print("🔄 Try running again to check different random addresses.")

if __name__ == "__main__":
    wallet_file = "detected_wallet_data_summary.json"
    sample_size = 15  # Conservative sample size
    
    if len(sys.argv) > 1:
        wallet_file = sys.argv[1]
    if len(sys.argv) > 2:
        sample_size = int(sys.argv[2])
    
    check_sample_addresses(wallet_file, sample_size)
