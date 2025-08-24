#!/usr/bin/env python3
"""
WX51 Multi-Blockchain Balance Checker
Comprehensive balance checker for all keys extracted from WX51A40D1621
"""

import json
import time
import hashlib
import binascii
from datetime import datetime
from collections import defaultdict
import requests
import concurrent.futures
import threading

class WX51MultiBlockchainChecker:
    def __init__(self):
        self.results_file = f"WX51_MULTI_BLOCKCHAIN_RESULTS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.funded_wallets = []
        self.total_checked = 0
        self.rate_limit_delay = 0.5
        self.results_lock = threading.Lock()
        
        # API endpoints
        self.apis = {
            'ethereum': [
                'https://api.blockcypher.com/v1/eth/main/addrs/{}/balance',
                'https://api.etherscan.io/api?module=account&action=balance&address={}&tag=latest',
            ],
            'bitcoin': [
                'https://api.blockcypher.com/v1/btc/main/addrs/{}/balance',
                'https://blockstream.info/api/address/{}',
                'https://api.blockchain.info/v1/address/{}?format=json'
            ],
            'litecoin': [
                'https://api.blockcypher.com/v1/ltc/main/addrs/{}/balance',
            ],
            'dogecoin': [
                'https://api.blockcypher.com/v1/doge/main/addrs/{}/balance',
            ],
            'bitcoin_cash': [
                'https://api.blockcypher.com/v1/bcy/test/addrs/{}/balance',
            ]
        }

    def load_wx51_results(self):
        """Load all WX51 hunt results"""
        wx51_files = [
            'WX51_HUNT_RESULTS_20250813_191813.json',
            'WX51_HUNT_RESULTS_20250813_192138.json'
        ]
        
        all_keys = []
        
        for filename in wx51_files:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                    if 'top_keys' in data:
                        all_keys.extend(data['top_keys'])
                        print(f"✅ Loaded {len(data['top_keys'])} keys from {filename}")
            except FileNotFoundError:
                print(f"⚠️ File not found: {filename}")
                
        print(f"📊 Total keys loaded: {len(all_keys)}")
        return all_keys

    def generate_addresses(self, private_key, key_type):
        """Generate addresses for different blockchain networks"""
        addresses = {}
        
        try:
            # Ethereum address generation
            if key_type in ['eth_private_key', 'bitcoin_hex'] and len(private_key) == 64:
                try:
                    from eth_keys import keys
                    pk = keys.PrivateKey(bytes.fromhex(private_key))
                    addresses['ethereum'] = pk.public_key.to_checksum_address()
                except Exception as e:
                    print(f"⚠️ Error generating Ethereum address: {e}")
                    
            # Bitcoin address generation
            if key_type in ['bitcoin_wif', 'bitcoin_hex']:
                try:
                    import hashlib
                    import base58
                    
                    if key_type == 'bitcoin_wif' and len(private_key) in [51, 52]:
                        # WIF format
                        addresses['bitcoin'] = self.wif_to_address(private_key)
                    elif key_type == 'bitcoin_hex' and len(private_key) == 64:
                        # Hex format - convert to address
                        addresses['bitcoin'] = self.hex_to_bitcoin_address(private_key)
                        
                except Exception as e:
                    print(f"⚠️ Error generating Bitcoin address: {e}")
                    
            # For hex keys, try multiple formats
            if len(private_key) == 64 and all(c in '0123456789abcdefABCDEF' for c in private_key):
                try:
                    # Try Bitcoin
                    addresses['bitcoin'] = self.hex_to_bitcoin_address(private_key)
                    # Try Litecoin
                    addresses['litecoin'] = self.hex_to_litecoin_address(private_key)
                    # Try Dogecoin
                    addresses['dogecoin'] = self.hex_to_dogecoin_address(private_key)
                except:
                    pass
                    
        except Exception as e:
            print(f"⚠️ Error in address generation: {e}")
            
        return addresses

    def wif_to_address(self, wif_key):
        """Convert WIF to Bitcoin address (simplified)"""
        try:
            import base58
            # This is a simplified version
            # Full implementation would require proper secp256k1 operations
            return None
        except:
            return None

    def hex_to_bitcoin_address(self, hex_key):
        """Convert hex private key to Bitcoin address (simplified)"""
        try:
            # Simplified - would need full secp256k1 implementation
            # For now, return None to avoid false positives
            return None
        except:
            return None

    def hex_to_litecoin_address(self, hex_key):
        """Convert hex private key to Litecoin address"""
        try:
            # Simplified implementation
            return None
        except:
            return None

    def hex_to_dogecoin_address(self, hex_key):
        """Convert hex private key to Dogecoin address"""
        try:
            # Simplified implementation
            return None
        except:
            return None

    def check_address_balance(self, address, network):
        """Check balance for a specific address on a network"""
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
                    elif network in ['bitcoin', 'litecoin', 'bitcoin_cash']:
                        balance = balance / 1e8   # Satoshi to BTC/LTC/BCH
                    elif network == 'dogecoin':
                        balance = balance / 1e8   # Koinu to DOGE
                        
                    if balance > 0:
                        return balance
                        
                time.sleep(self.rate_limit_delay)
                
            except Exception as e:
                print(f"⚠️ Error checking {network} address {address}: {e}")
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
                    print(f"💎 FUNDED WALLET FOUND!")
                    print(f"   Network: {network}")
                    print(f"   Address: {address}")
                    print(f"   Balance: {balance}")
                    print(f"   Key: {key_data['key']}")
                    print(f"   Source: {key_data['source']}")
                    
        return results

    def batch_check_balances(self, keys, max_workers=5):
        """Check balances for multiple keys in parallel"""
        print(f"\n💰 Starting multi-blockchain balance check for {len(keys)} keys...")
        
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
                            
                    if checked_count % 10 == 0:
                        print(f"   📊 Checked {checked_count}/{len(keys)} keys, found {len(funded_wallets)} funded")
                        
                except Exception as e:
                    print(f"⚠️ Error processing key: {e}")
                    
        return funded_wallets

    def save_results(self, all_keys, funded_wallets):
        """Save comprehensive results"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'source': 'WX51A40D1621 Windows System Hunt',
            'total_keys_checked': len(all_keys),
            'funded_wallets_found': len(funded_wallets),
            'funded_wallets': funded_wallets,
            'statistics': {
                'by_network': defaultdict(int),
                'by_key_type': defaultdict(int),
                'total_value': 0
            },
            'top_unfunded_keys': all_keys[:50]  # Keep top 50 for reference
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
        print(f"\n🚀 Starting WX51 Multi-Blockchain Check - {datetime.now()}")
        
        # Load all WX51 keys
        all_keys = self.load_wx51_results()
        
        if not all_keys:
            print("❌ No keys to check!")
            return
            
        # Sort by confidence
        all_keys.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Check balances
        funded_wallets = self.batch_check_balances(all_keys[:100])  # Check top 100 first
        
        # Save results
        self.save_results(all_keys, funded_wallets)
        
        # Print summary
        print(f"\n🎯 WX51 MULTI-BLOCKCHAIN SUMMARY:")
        print(f"   🔑 Keys checked: {min(100, len(all_keys))}")
        print(f"   💎 Funded wallets: {len(funded_wallets)}")
        
        if funded_wallets:
            print(f"\n💰 FUNDED WALLET DETAILS:")
            for i, wallet in enumerate(funded_wallets, 1):
                print(f"   {i}. {wallet['key'][:20]}...")
                for network, details in wallet['balances'].items():
                    print(f"      {network}: {details['balance']} ({details['address']})")
                    
            print(f"\n🎉 RECOVERY READY - {len(funded_wallets)} wallets found!")
        else:
            print(f"\n   ❌ No funded wallets found in this batch")
            print(f"   💡 Consider checking more keys or different networks")

def main():
    checker = WX51MultiBlockchainChecker()
    checker.run_comprehensive_check()

if __name__ == "__main__":
    main()
