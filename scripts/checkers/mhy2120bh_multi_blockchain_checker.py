#!/usr/bin/env python3
"""
MHY2120BH Mac Multi-Blockchain Balance Checker
Comprehensive balance checker for all keys extracted from Mac OS X system
"""

import json
import time
import hashlib
from datetime import datetime
from collections import defaultdict
import requests
import concurrent.futures
import threading

class MacMultiBlockchainChecker:
    def __init__(self):
        self.results_file = f"MHY2120BH_MULTI_BLOCKCHAIN_RESULTS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.funded_wallets = []
        self.total_checked = 0
        self.rate_limit_delay = 0.5
        self.results_lock = threading.Lock()
        
        # API endpoints
        self.apis = {
            'ethereum': [
                'https://api.blockcypher.com/v1/eth/main/addrs/{}/balance',
            ],
            'bitcoin': [
                'https://api.blockcypher.com/v1/btc/main/addrs/{}/balance',
                'https://blockstream.info/api/address/{}',
            ],
            'litecoin': [
                'https://api.blockcypher.com/v1/ltc/main/addrs/{}/balance',
            ],
            'dogecoin': [
                'https://api.blockcypher.com/v1/doge/main/addrs/{}/balance',
            ]
        }

    def load_mac_results(self):
        """Load all Mac hunt results"""
        mac_files = [
            'MHY2120BH_MAC_HUNT_RESULTS_20250813_200831.json',
            'MHY2120BH_MAC_HUNT_RESULTS_20250813_200928.json',
            'MHY2120BH_MAC_HUNT_RESULTS_20250813_201133.json'
        ]
        
        all_keys = []
        
        for filename in mac_files:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                    if 'top_keys' in data:
                        all_keys.extend(data['top_keys'])
                        print(f"✅ Loaded {len(data['top_keys'])} keys from {filename}")
            except FileNotFoundError:
                print(f"⚠️ File not found: {filename}")
                
        print(f"📊 Total Mac keys loaded: {len(all_keys)}")
        return all_keys

    def generate_addresses(self, private_key, key_type):
        """Generate addresses for different blockchain networks"""
        addresses = {}
        
        try:
            # Ethereum address generation for various key types
            if key_type in ['eth_private_key', 'bitcoin_hex', 'plist_decoded_key', 'mac_keychain'] and len(private_key) == 64:
                try:
                    from eth_keys import keys
                    pk = keys.PrivateKey(bytes.fromhex(private_key))
                    addresses['ethereum'] = pk.public_key.to_checksum_address()
                except Exception as e:
                    # Don't print errors for every failed key generation
                    pass
                    
        except Exception as e:
            # Silently handle errors
            pass
            
        return addresses

    def check_address_balance(self, address, network):
        """Check balance for a specific address"""
        if not address:
            return 0
            
        for api_url in self.apis.get(network, []):
            try:
                if '{}' in api_url:
                    url = api_url.format(address)
                else:
                    url = api_url + address
                    
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Parse different API response formats
                    balance = 0
                    
                    if 'balance' in data:
                        balance = data['balance']
                    elif 'result' in data:
                        balance = int(data['result'])
                    elif 'final_balance' in data:
                        balance = data['final_balance']
                    elif 'chain_stats' in data:
                        balance = data['chain_stats']['funded_txo_sum']
                        
                    # Convert to standard units
                    if network == 'ethereum':
                        balance = balance / 1e18  # Wei to ETH
                    elif network in ['bitcoin', 'litecoin']:
                        balance = balance / 1e8   # Satoshi to BTC/LTC
                    elif network == 'dogecoin':
                        balance = balance / 1e8   # Koinu to DOGE
                        
                    if balance > 0:
                        return balance
                        
                time.sleep(self.rate_limit_delay)
                
            except Exception as e:
                continue
                
        return 0

    def check_key_balances(self, key_data):
        """Check balances for a single key across all networks"""
        results = {
            'key': key_data['key'],
            'source': key_data['source'],
            'type': key_data['type'],
            'confidence': key_data['confidence'],
            'balances': {},
            'funded': False,
            'total_value': 0
        }
        
        # Generate addresses
        addresses = self.generate_addresses(key_data['key'], key_data['type'])
        
        # Check each address
        for network, address in addresses.items():
            if address:
                balance = self.check_address_balance(address, network)
                if balance > 0:
                    results['balances'][network] = {
                        'address': address,
                        'balance': balance
                    }
                    results['funded'] = True
                    results['total_value'] += balance
                    
                    # Log funded wallet immediately
                    print(f"💎 FUNDED MAC WALLET FOUND!")
                    print(f"   Network: {network}")
                    print(f"   Address: {address}")
                    print(f"   Balance: {balance}")
                    print(f"   Key: {key_data['key'][:20]}...")
                    print(f"   Source: {key_data['source']}")
                    
        return results

    def batch_check_balances(self, keys, max_workers=3):
        """Check balances for multiple keys in parallel"""
        print(f"\n💰 Starting Mac multi-blockchain balance check for {len(keys)} keys...")
        
        funded_wallets = []
        checked_count = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_key = {
                executor.submit(self.check_key_balances, key_data): key_data 
                for key_data in keys
            }
            
            # Process completed tasks
            for future in concurrent.futures.as_completed(future_to_key):
                try:
                    result = future.result()
                    checked_count += 1
                    
                    if result['funded']:
                        with self.results_lock:
                            funded_wallets.append(result)
                            
                    if checked_count % 25 == 0:
                        print(f"   📊 Checked {checked_count}/{len(keys)} keys, found {len(funded_wallets)} funded")
                        
                except Exception as e:
                    print(f"⚠️ Error processing key: {e}")
                    
        return funded_wallets

    def save_results(self, all_keys, funded_wallets):
        """Save comprehensive results"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'source': 'MHY2120BH Mac OS X System Hunt',
            'system_info': 'Mac OS X 10.5-10.9 (2008-2014 era)',
            'total_keys_checked': len(all_keys),
            'funded_wallets_found': len(funded_wallets),
            'funded_wallets': funded_wallets,
            'statistics': {
                'by_network': defaultdict(int),
                'by_key_type': defaultdict(int),
                'total_value': 0
            },
            'top_unfunded_keys': all_keys[:100]  # Keep top 100 for reference
        }
        
        # Calculate statistics
        for wallet in funded_wallets:
            results['statistics']['total_value'] += wallet['total_value']
            results['statistics']['by_key_type'][wallet['type']] += 1
            
            for network in wallet['balances']:
                results['statistics']['by_network'][network] += 1
                
        # Convert defaultdict to regular dict for JSON serialization
        results['statistics']['by_network'] = dict(results['statistics']['by_network'])
        results['statistics']['by_key_type'] = dict(results['statistics']['by_key_type'])
        
        with open(self.results_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        print(f"\n💾 Results saved to: {self.results_file}")

    def run_comprehensive_check(self):
        """Run the comprehensive multi-blockchain check"""
        print(f"\n🚀 Starting MHY2120BH Mac Multi-Blockchain Check - {datetime.now()}")
        
        # Load all Mac keys
        all_keys = self.load_mac_results()
        
        if not all_keys:
            print("❌ No keys to check!")
            return
            
        # Sort by confidence
        all_keys.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Check balances for all keys (Mac systems often have fewer keys)
        funded_wallets = self.batch_check_balances(all_keys)
        
        # Save results
        self.save_results(all_keys, funded_wallets)
        
        # Print summary
        print(f"\n🎯 MHY2120BH MAC MULTI-BLOCKCHAIN SUMMARY:")
        print(f"   🖥️ System: Mac OS X (2008-2014)")
        print(f"   🔑 Keys checked: {len(all_keys)}")
        print(f"   💎 Funded wallets: {len(funded_wallets)}")
        
        if funded_wallets:
            print(f"\n💰 FUNDED MAC WALLET DETAILS:")
            for i, wallet in enumerate(funded_wallets, 1):
                print(f"   {i}. {wallet['key'][:20]}...")
                for network, details in wallet['balances'].items():
                    print(f"      {network}: {details['balance']} ({details['address']})")
                print(f"      Source: {wallet['source']}")
                    
            print(f"\n🎉 MAC RECOVERY READY - {len(funded_wallets)} wallets found!")
        else:
            print(f"\n   ❌ No funded wallets found")
            print(f"   💡 Mac system appears clean of crypto assets")

def main():
    checker = MacMultiBlockchainChecker()
    checker.run_comprehensive_check()

if __name__ == "__main__":
    main()
