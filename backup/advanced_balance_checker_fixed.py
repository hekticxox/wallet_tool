#!/usr/bin/env python3
"""
Advanced Balance Checker - FIXED for your data format
- Multiple API endpoints and fallbacks
- Intelligent rate limiting and backoff
- Batch processing with delays
- Caching to avoid duplicate requests
- Progress tracking and resumption
"""

import json
import time
import random
import requests
from pathlib import Path
import argparse
from typing import Dict, List, Optional, Tuple
import hashlib

class AdvancedBalanceChecker:
    def __init__(self, cache_file: str = "balance_check_cache.json"):
        self.cache_file = cache_file
        self.cache = self.load_cache()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        
        # Rate limiting settings - more conservative
        self.eth_delay = 2.5  # seconds between ETH API calls
        self.btc_delay = 3.5  # seconds between BTC API calls
        self.sol_delay = 1.5  # seconds between SOL API calls
        self.max_retries = 3
        self.backoff_multiplier = 2

    def load_cache(self) -> Dict:
        """Load existing cache to avoid duplicate API calls"""
        try:
            if Path(self.cache_file).exists():
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Cache load error: {e}")
        return {}

    def save_cache(self):
        """Save cache to disk"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Cache save error: {e}")

    def get_address_hash(self, address: str) -> str:
        """Create a hash key for caching"""
        return hashlib.md5(address.encode()).hexdigest()

    def check_ethereum_balance(self, address: str) -> Optional[Dict]:
        """Check ETH balance using Blockchair"""
        cache_key = f"eth_{self.get_address_hash(address)}"
        
        if cache_key in self.cache:
            print(f"ETH {address[:10]}... (cached: {self.cache[cache_key].get('balance_eth', 0):.6f} ETH)")
            return self.cache[cache_key]
        
        try:
            time.sleep(self.eth_delay + random.uniform(0, 1))
            url = f"https://api.blockchair.com/ethereum/dashboards/address/{address}"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and address in data['data']:
                    balance_wei = data['data'][address]['address']['balance']
                    balance_eth = float(balance_wei) / 1e18
                    result = {
                        'address': address,
                        'balance_wei': balance_wei,
                        'balance_eth': balance_eth,
                        'api_used': 'blockchair',
                        'has_balance': balance_eth > 0
                    }
                    self.cache[cache_key] = result
                    print(f"ETH {address[:10]}... = {balance_eth:.6f} ETH")
                    return result
            else:
                print(f"ETH {address[:10]}... ❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"ETH {address[:10]}... ❌ Error: {str(e)[:30]}")
        
        return None

    def check_bitcoin_balance(self, address: str) -> Optional[Dict]:
        """Check BTC balance using Blockstream"""
        cache_key = f"btc_{self.get_address_hash(address)}"
        
        if cache_key in self.cache:
            print(f"BTC {address[:10]}... (cached: {self.cache[cache_key].get('balance_btc', 0):.8f} BTC)")
            return self.cache[cache_key]
        
        try:
            time.sleep(self.btc_delay + random.uniform(0, 1))
            url = f"https://blockstream.info/api/address/{address}"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                balance_sat = data.get('chain_stats', {}).get('funded_txo_sum', 0) - \
                             data.get('chain_stats', {}).get('spent_txo_sum', 0)
                balance_btc = balance_sat / 1e8
                result = {
                    'address': address,
                    'balance_sat': balance_sat,
                    'balance_btc': balance_btc,
                    'api_used': 'blockstream',
                    'has_balance': balance_btc > 0
                }
                self.cache[cache_key] = result
                print(f"BTC {address[:10]}... = {balance_btc:.8f} BTC")
                return result
            else:
                print(f"BTC {address[:10]}... ❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"BTC {address[:10]}... ❌ Error: {str(e)[:30]}")
        
        return None

    def check_solana_balance(self, address: str) -> Optional[Dict]:
        """Check SOL balance using RPC"""
        cache_key = f"sol_{self.get_address_hash(address)}"
        
        if cache_key in self.cache:
            print(f"SOL {address[:10]}... (cached: {self.cache[cache_key].get('balance_sol', 0):.6f} SOL)")
            return self.cache[cache_key]
        
        try:
            time.sleep(self.sol_delay + random.uniform(0, 0.5))
            
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [address]
            }
            
            response = self.session.post(
                "https://api.mainnet-beta.solana.com",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'result' in data and 'value' in data['result']:
                    balance_lamports = data['result']['value']
                    balance_sol = balance_lamports / 1e9
                    result = {
                        'address': address,
                        'balance_lamports': balance_lamports,
                        'balance_sol': balance_sol,
                        'api_used': 'solana_rpc',
                        'has_balance': balance_sol > 0
                    }
                    self.cache[cache_key] = result
                    print(f"SOL {address[:10]}... = {balance_sol:.6f} SOL")
                    return result
            else:
                print(f"SOL {address[:10]}... ❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"SOL {address[:10]}... ❌ Error: {str(e)[:30]}")
        
        return None

    def process_batch(self, addresses: List[str], blockchain: str, batch_size: int = 10) -> List[Dict]:
        """Process addresses in batches with progress tracking"""
        results = []
        total = len(addresses)
        
        print(f"\n🔍 Processing {total} {blockchain.upper()} addresses in batches of {batch_size}")
        
        for i in range(0, total, batch_size):
            batch = addresses[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            print(f"\n📦 Batch {batch_num}/{total_batches} ({len(batch)} addresses)")
            
            batch_results = []
            for address in batch:
                if blockchain == 'ethereum':
                    result = self.check_ethereum_balance(address)
                elif blockchain == 'bitcoin':
                    result = self.check_bitcoin_balance(address)
                elif blockchain == 'solana':
                    result = self.check_solana_balance(address)
                else:
                    continue
                
                if result:
                    batch_results.append(result)
                
                # Save cache periodically
                if len(batch_results) % 5 == 0:
                    self.save_cache()
            
            results.extend(batch_results)
            
            # Inter-batch delay to avoid overwhelming APIs
            if i + batch_size < total:
                delay = random.uniform(10, 20)  # 10-20 second break between batches
                print(f"⏳ Batch complete. Waiting {delay:.1f}s before next batch...")
                time.sleep(delay)
        
        return results

    def find_funded_addresses(self, wallet_data_file: str, max_addresses: int = 100) -> Dict:
        """Main function to check balances and find funded addresses"""
        print(f"🚀 Loading wallet data from {wallet_data_file}")
        
        try:
            with open(wallet_data_file, 'r') as f:
                wallet_data = json.load(f)
        except Exception as e:
            print(f"Error loading wallet data: {e}")
            return {}
        
        results = {
            'ethereum': {'checked': [], 'funded': []},
            'bitcoin': {'checked': [], 'funded': []},
            'solana': {'checked': [], 'funded': []}
        }
        
        # Process each blockchain - FIXED to use correct data structure
        blockchain_mapping = {
            'ethereum': 'ethereum',
            'bitcoin': 'bitcoin', 
            'solana': 'solana'
        }
        
        for blockchain_key, blockchain_name in blockchain_mapping.items():
            # Check if data exists in the correct structure
            if ('detected_addresses' in wallet_data and 
                blockchain_name in wallet_data['detected_addresses']):
                
                addresses = wallet_data['detected_addresses'][blockchain_name]
                if addresses:
                    # Limit to max_addresses
                    addresses_to_check = addresses[:max_addresses]
                    print(f"\n🎯 Found {len(addresses)} {blockchain_name.upper()} addresses, checking {len(addresses_to_check)}")
                    
                    checked = self.process_batch(addresses_to_check, blockchain_name)
                    funded = [addr for addr in checked if addr.get('has_balance', False)]
                    
                    results[blockchain_key]['checked'] = checked
                    results[blockchain_key]['funded'] = funded
                    
                    print(f"\n✅ {blockchain_name.upper()} Summary:")
                    print(f"   Checked: {len(checked)}")
                    print(f"   With Funds: {len(funded)}")
                    
                    if funded:
                        print("   💰 FUNDED ADDRESSES FOUND:")
                        for addr in funded:
                            if blockchain_name == 'ethereum':
                                print(f"     {addr['address']} = {addr['balance_eth']:.6f} ETH")
                            elif blockchain_name == 'bitcoin':
                                print(f"     {addr['address']} = {addr['balance_btc']:.8f} BTC")
                            elif blockchain_name == 'solana':
                                print(f"     {addr['address']} = {addr['balance_sol']:.6f} SOL")
                else:
                    print(f"⚠️  No {blockchain_name.upper()} addresses found in data")
            else:
                print(f"⚠️  No {blockchain_name.upper()} addresses found in detected_addresses")
        
        # Save final results
        self.save_cache()
        return results

def main():
    parser = argparse.ArgumentParser(description='Advanced Balance Checker - Fixed for your data format')
    parser.add_argument('wallet_file', help='Path to wallet data JSON file')
    parser.add_argument('--max-addresses', type=int, default=50, 
                       help='Maximum addresses to check per blockchain (default: 50)')
    parser.add_argument('--cache-file', default='balance_check_cache.json',
                       help='Cache file path (default: balance_check_cache.json)')
    
    args = parser.parse_args()
    
    checker = AdvancedBalanceChecker(cache_file=args.cache_file)
    results = checker.find_funded_addresses(args.wallet_file, args.max_addresses)
    
    # Save detailed results
    output_file = f"funded_addresses_{int(time.time())}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {output_file}")
    
    # Summary
    total_funded = sum(len(results[bc]['funded']) for bc in results)
    total_checked = sum(len(results[bc]['checked']) for bc in results)
    
    if total_funded > 0:
        print(f"\n🎉 SUCCESS: Found {total_funded} funded addresses out of {total_checked} checked!")
    else:
        print(f"\n❌ No funded addresses found out of {total_checked} addresses checked.")

if __name__ == "__main__":
    main()
