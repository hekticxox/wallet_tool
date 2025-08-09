#!/usr/bin/env python3
"""
Advanced Balance Checker with Rate Limit Avoidance
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
        
        # Rate limiting settings
        self.eth_delay = 2.0  # seconds between ETH API calls
        self.btc_delay = 3.0  # seconds between BTC API calls
        self.sol_delay = 1.0  # seconds between SOL API calls
        self.max_retries = 3
        self.backoff_multiplier = 2
        
        # Multiple API endpoints for redundancy
        self.eth_apis = [
            "https://api.etherscan.io/api",
            "https://api.blockchair.com/ethereum/dashboards/address/",
            "https://eth-mainnet.g.alchemy.com/v2/demo"  # Free tier
        ]
        
        self.btc_apis = [
            "https://blockstream.info/api/address/",
            "https://api.blockchair.com/bitcoin/dashboards/address/",
            "https://blockchain.info/rawaddr/"
        ]
        
        self.sol_apis = [
            "https://api.mainnet-beta.solana.com",
            "https://solana-api.projectserum.com"
        ]

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

    def check_ethereum_balance_multi(self, address: str) -> Optional[Dict]:
        """Check ETH balance using multiple APIs with fallback"""
        cache_key = f"eth_{self.get_address_hash(address)}"
        
        if cache_key in self.cache:
            print(f"ETH {address[:10]}... (cached)")
            return self.cache[cache_key]
        
        # Try Blockchair first (more generous rate limits)
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
        except Exception as e:
            print(f"Blockchair ETH API error for {address[:10]}...: {e}")
        
        # Fallback to Etherscan with more delays
        try:
            time.sleep(self.eth_delay * 2)  # Double delay for etherscan
            url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey=YourApiKeyToken"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == '1':
                    balance_wei = int(data['result'])
                    balance_eth = balance_wei / 1e18
                    result = {
                        'address': address,
                        'balance_wei': balance_wei,
                        'balance_eth': balance_eth,
                        'api_used': 'etherscan',
                        'has_balance': balance_eth > 0
                    }
                    self.cache[cache_key] = result
                    print(f"ETH {address[:10]}... = {balance_eth:.6f} ETH")
                    return result
                else:
                    print(f"Etherscan error for {address[:10]}...: {data.get('message', 'Unknown')}")
        except Exception as e:
            print(f"Etherscan API error for {address[:10]}...: {e}")
        
        return None

    def check_bitcoin_balance_multi(self, address: str) -> Optional[Dict]:
        """Check BTC balance using multiple APIs with fallback"""
        cache_key = f"btc_{self.get_address_hash(address)}"
        
        if cache_key in self.cache:
            print(f"BTC {address[:10]}... (cached)")
            return self.cache[cache_key]
        
        # Try Blockstream first (most reliable)
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
        except Exception as e:
            print(f"Blockstream API error for {address[:10]}...: {e}")
        
        # Fallback to Blockchair
        try:
            time.sleep(self.btc_delay * 2)
            url = f"https://api.blockchair.com/bitcoin/dashboards/address/{address}"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and address in data['data']:
                    balance_sat = data['data'][address]['address']['balance']
                    balance_btc = balance_sat / 1e8
                    result = {
                        'address': address,
                        'balance_sat': balance_sat,
                        'balance_btc': balance_btc,
                        'api_used': 'blockchair',
                        'has_balance': balance_btc > 0
                    }
                    self.cache[cache_key] = result
                    print(f"BTC {address[:10]}... = {balance_btc:.8f} BTC")
                    return result
        except Exception as e:
            print(f"Blockchair BTC API error for {address[:10]}...: {e}")
        
        return None

    def check_solana_balance(self, address: str) -> Optional[Dict]:
        """Check SOL balance using RPC"""
        cache_key = f"sol_{self.get_address_hash(address)}"
        
        if cache_key in self.cache:
            print(f"SOL {address[:10]}... (cached)")
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
        except Exception as e:
            print(f"Solana RPC error for {address[:10]}...: {e}")
        
        return None

    def process_batch(self, addresses: List[Dict], blockchain: str, batch_size: int = 10) -> List[Dict]:
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
            for addr_info in batch:
                address = addr_info['address']
                
                if blockchain == 'ethereum':
                    result = self.check_ethereum_balance_multi(address)
                elif blockchain == 'bitcoin':
                    result = self.check_bitcoin_balance_multi(address)
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
        
        # Process each blockchain
        for blockchain in ['ethereum', 'bitcoin', 'solana']:
            if blockchain in wallet_data:
                addresses = wallet_data[blockchain][:max_addresses]
                if addresses:
                    checked = self.process_batch(addresses, blockchain)
                    funded = [addr for addr in checked if addr.get('has_balance', False)]
                    
                    results[blockchain]['checked'] = checked
                    results[blockchain]['funded'] = funded
                    
                    print(f"\n✅ {blockchain.upper()} Summary:")
                    print(f"   Checked: {len(checked)}")
                    print(f"   With Funds: {len(funded)}")
                    
                    if funded:
                        print("   💰 FUNDED ADDRESSES FOUND:")
                        for addr in funded:
                            if blockchain == 'ethereum':
                                print(f"     {addr['address']} = {addr['balance_eth']:.6f} ETH")
                            elif blockchain == 'bitcoin':
                                print(f"     {addr['address']} = {addr['balance_btc']:.8f} BTC")
                            elif blockchain == 'solana':
                                print(f"     {addr['address']} = {addr['balance_sol']:.6f} SOL")
        
        # Save final results
        self.save_cache()
        return results

def main():
    parser = argparse.ArgumentParser(description='Advanced Balance Checker with Rate Limit Protection')
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
    if total_funded > 0:
        print(f"\n🎉 SUCCESS: Found {total_funded} funded addresses!")
    else:
        print(f"\n❌ No funded addresses found in this batch.")

if __name__ == "__main__":
    main()
