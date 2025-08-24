#!/usr/bin/env python3
"""
🔥 MULTI-DATASET PRECISION HUNTER
=================================
Hunt across ALL available datasets with laser precision
"""

import json
import time
import requests
from datetime import datetime
from eth_keys import keys
from bit import Key
import sys
import os

# Add the current directory to Python path to import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api_manager import APIManager
import os
import glob

class MultiDatasetHunter:
    def __init__(self):
        """Initialize multi-dataset hunter"""
        self.api_manager = APIManager()
        self.found_wallets = []
        self.datasets_checked = []
        
    def scan_all_available_datasets(self):
        """Scan all available key datasets for precision hunting"""
        print("🔥 MULTI-DATASET PRECISION HUNTER")
        print("=" * 60)
        print("🔍 Scanning all available datasets...")
        
        # Find all key files in the workspace
        key_files = self.find_all_key_files()
        
        print(f"📊 Found {len(key_files)} datasets to hunt:")
        for i, file_info in enumerate(key_files, 1):
            print(f"   {i}. {file_info['name']}: {file_info['estimated_keys']} keys")
        
        print("\n🎯 Starting multi-dataset precision hunt...")
        
        # Hunt each dataset
        total_hunted = 0
        for dataset in key_files:
            hunted = self.hunt_dataset(dataset)
            total_hunted += hunted
            
            if self.found_wallets:
                print(f"\n🎉 JACKPOT FOUND! Stopping hunt to report findings...")
                break
        
        self.show_multi_dataset_results(total_hunted)
        
    def find_all_key_files(self):
        """Find all available key datasets"""
        datasets = []
        
        # Check for JSON files with keys
        json_files = glob.glob("*.json")
        
        for json_file in json_files:
            if any(keyword in json_file.lower() for keyword in ['key', 'private', 'wallet', 'priority']):
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    
                    # Count keys in different formats
                    key_count = 0
                    
                    if isinstance(data, dict):
                        if 'keys' in data:
                            key_count = len(data['keys'])
                        elif 'private_keys' in data:
                            key_count = len(data['private_keys'])
                        elif 'checked_keys' in data:
                            key_count = len(data['checked_keys'])
                        
                        # Check for nested key structures
                        for value in data.values():
                            if isinstance(value, list) and len(value) > 0:
                                if isinstance(value[0], dict) and 'private_key' in value[0]:
                                    key_count = max(key_count, len(value))
                    
                    elif isinstance(data, list):
                        if len(data) > 0 and isinstance(data[0], dict):
                            if 'private_key' in data[0]:
                                key_count = len(data)
                    
                    if key_count > 0:
                        datasets.append({
                            'name': json_file,
                            'path': json_file,
                            'type': 'json',
                            'estimated_keys': key_count
                        })
                        
                except:
                    pass
        
        # Check for TXT files with keys
        txt_files = glob.glob("*.txt")
        
        for txt_file in txt_files:
            if any(keyword in txt_file.lower() for keyword in ['key', 'private', 'wallet']):
                try:
                    with open(txt_file, 'r') as f:
                        lines = f.readlines()
                    
                    # Count lines that look like private keys
                    key_count = 0
                    for line in lines:
                        line = line.strip()
                        if len(line) == 64 and all(c in '0123456789abcdefABCDEF' for c in line):
                            key_count += 1
                    
                    if key_count > 0:
                        datasets.append({
                            'name': txt_file,
                            'path': txt_file,
                            'type': 'txt',
                            'estimated_keys': key_count
                        })
                        
                except:
                    pass
        
        # Sort by estimated key count (largest first)
        datasets.sort(key=lambda x: x['estimated_keys'], reverse=True)
        
        return datasets
    
    def hunt_dataset(self, dataset_info):
        """Hunt a specific dataset with precision"""
        name = dataset_info['name']
        path = dataset_info['path']
        estimated = dataset_info['estimated_keys']
        
        print(f"\n🎯 HUNTING DATASET: {name}")
        print(f"   📊 Estimated keys: {estimated}")
        
        # Load keys from dataset
        keys_to_hunt = self.load_keys_from_dataset(dataset_info)
        
        if not keys_to_hunt:
            print(f"   ❌ Could not load keys from {name}")
            return 0
        
        actual_keys = len(keys_to_hunt)
        print(f"   ✅ Loaded {actual_keys} keys")
        
        # Hunt with precision (limit to top 50 per dataset for speed)
        hunt_limit = min(50, actual_keys)
        
        print(f"   🔍 Hunting top {hunt_limit} keys with laser precision...")
        
        hunted_count = 0
        
        for i, key_data in enumerate(keys_to_hunt[:hunt_limit]):
            if self.precision_hunt_single(key_data, i + 1, name):
                # Found a funded wallet, return immediately
                return hunted_count + 1
            
            hunted_count += 1
            
            # Small delay for API rate limiting
            time.sleep(0.1)
        
        self.datasets_checked.append({
            'name': name,
            'keys_hunted': hunted_count,
            'found': 0
        })
        
        return hunted_count
    
    def load_keys_from_dataset(self, dataset_info):
        """Load keys from a dataset file"""
        path = dataset_info['path']
        file_type = dataset_info['type']
        
        keys = []
        
        try:
            if file_type == 'json':
                with open(path, 'r') as f:
                    data = json.load(f)
                
                # Extract keys based on structure
                if isinstance(data, dict):
                    if 'keys' in data and isinstance(data['keys'], list):
                        for item in data['keys']:
                            if isinstance(item, dict) and 'private_key' in item:
                                keys.append(item)
                            elif isinstance(item, str) and len(item) >= 64:
                                keys.append({'private_key': item, 'source_file': path})
                    
                    elif 'private_keys' in data:
                        for key in data['private_keys']:
                            keys.append({'private_key': key, 'source_file': path})
                    
                    elif 'checked_keys' in data:
                        for item in data['checked_keys']:
                            if isinstance(item, dict) and 'private_key' in item:
                                keys.append(item)
                    
                    # Check all values for key lists
                    for key, value in data.items():
                        if isinstance(value, list) and len(value) > 0:
                            if isinstance(value[0], dict) and 'private_key' in value[0]:
                                keys.extend(value[:50])  # Limit per dataset
                
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and 'private_key' in item:
                            keys.append(item)
                        elif isinstance(item, str) and len(item) >= 64:
                            keys.append({'private_key': item, 'source_file': path})
            
            elif file_type == 'txt':
                with open(path, 'r') as f:
                    lines = f.readlines()
                
                for line in lines:
                    line = line.strip()
                    if len(line) == 64 and all(c in '0123456789abcdefABCDEF' for c in line):
                        keys.append({'private_key': line, 'source_file': path})
        
        except Exception as e:
            print(f"   ❌ Error loading {path}: {e}")
            return []
        
        # Prioritize by entropy
        prioritized_keys = self.prioritize_keys_by_entropy(keys)
        
        return prioritized_keys
    
    def prioritize_keys_by_entropy(self, keys):
        """Prioritize keys by entropy score"""
        for key_data in keys:
            private_key = key_data['private_key']
            if private_key.startswith('0x'):
                private_key = private_key[2:]
            
            entropy_score = self.calculate_entropy_score(private_key)
            key_data['entropy_score'] = entropy_score
        
        # Sort by entropy (highest first)
        return sorted(keys, key=lambda x: x.get('entropy_score', 0), reverse=True)
    
    def calculate_entropy_score(self, hex_key):
        """Calculate entropy score for precision targeting"""
        if not hex_key or len(hex_key) < 64:
            return 0
        
        # Count unique characters
        unique_chars = len(set(hex_key.lower()))
        base_entropy = unique_chars / 16.0
        
        # Check for patterns that reduce entropy
        penalties = 0
        
        # Repeating characters
        if any(char * 4 in hex_key for char in '0123456789abcdef'):
            penalties += 0.2
        
        # Sequential patterns
        sequential_patterns = ['0123', '1234', '2345', '3456', '4567', '5678', '6789', '789a', '89ab', '9abc', 'abcd', 'bcde', 'cdef']
        if any(pattern in hex_key.lower() for pattern in sequential_patterns):
            penalties += 0.2
        
        final_score = max(0, base_entropy - penalties)
        return final_score
    
    def precision_hunt_single(self, key_data, index, dataset_name):
        """Hunt a single key with maximum precision"""
        private_key = key_data['private_key']
        entropy_score = key_data.get('entropy_score', 0)
        
        print(f"   🎯 [{index}] {private_key[:12]}... (entropy: {entropy_score:.3f})")
        
        try:
            # Derive addresses
            eth_address, btc_address = self.derive_addresses(private_key)
            
            if not eth_address or not btc_address:
                print(f"      ❌ Address derivation failed")
                return False
            
            print(f"      📍 ETH: {eth_address}")
            print(f"      📍 BTC: {btc_address}")
            
            # Check balances with precision
            eth_balance = self.check_eth_balance(eth_address)
            btc_balance = self.check_btc_balance(btc_address)
            
            if eth_balance > 0 or btc_balance > 0:
                print(f"      🎉 JACKPOT FOUND IN {dataset_name}!")
                print(f"      💰 ETH: {eth_balance} wei")
                print(f"      💰 BTC: {btc_balance} sat")
                
                # Save the jackpot immediately
                jackpot = {
                    'private_key': private_key,
                    'dataset': dataset_name,
                    'eth_address': eth_address,
                    'btc_address': btc_address,
                    'eth_balance': eth_balance,
                    'btc_balance': btc_balance,
                    'entropy_score': entropy_score,
                    'timestamp': datetime.now().isoformat()
                }
                
                self.found_wallets.append(jackpot)
                self.save_jackpot_immediately(jackpot)
                
                return True
            else:
                print(f"      ✓ Empty")
                return False
        
        except Exception as e:
            print(f"      ❌ Error: {e}")
            return False
    
    def derive_addresses(self, private_key_hex):
        """Derive addresses with validation"""
        try:
            if private_key_hex.startswith('0x'):
                private_key_hex = private_key_hex[2:]
            
            # Ethereum
            private_key_bytes = bytes.fromhex(private_key_hex)
            eth_key = keys.PrivateKey(private_key_bytes)
            eth_address = eth_key.public_key.to_checksum_address()
            
            # Bitcoin
            btc_key = Key.from_hex(private_key_hex)
            btc_address = btc_key.address
            
            return eth_address, btc_address
            
        except Exception:
            return None, None
    
    def check_eth_balance(self, address):
        """Check Ethereum balance with precision"""
        try:
            eth_apis = self.api_manager.get_ethereum_apis()
            
            if eth_apis.get('etherscan'):
                url = "https://api.etherscan.io/api"
                params = {
                    'module': 'account',
                    'action': 'balance',
                    'address': address,
                    'tag': 'latest',
                    'apikey': eth_apis['etherscan']
                }
                
                response = requests.get(url, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == '1':
                        return int(data.get('result', 0))
            
            return 0
            
        except Exception:
            return 0
    
    def check_btc_balance(self, address):
        """Check Bitcoin balance with precision"""
        try:
            url = f"https://blockstream.info/api/address/{address}"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                funded = data.get('chain_stats', {}).get('funded_txo_sum', 0)
                spent = data.get('chain_stats', {}).get('spent_txo_sum', 0)
                return funded - spent
            
            return 0
            
        except Exception:
            return 0
    
    def save_jackpot_immediately(self, jackpot):
        """Save jackpot immediately"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"MULTI_DATASET_JACKPOT_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(jackpot, f, indent=2)
        
        print(f"      💾 JACKPOT SAVED: {filename}")
    
    def show_multi_dataset_results(self, total_hunted):
        """Show final multi-dataset results"""
        print("\n" + "=" * 60)
        print("🏁 MULTI-DATASET PRECISION HUNT COMPLETE")
        print("=" * 60)
        
        print(f"📊 Datasets checked: {len(self.datasets_checked)}")
        print(f"🎯 Total keys hunted: {total_hunted}")
        print(f"💰 Funded wallets found: {len(self.found_wallets)}")
        
        if self.found_wallets:
            print(f"\n🎉 SUCCESS! Found {len(self.found_wallets)} funded wallets!")
            
            for i, wallet in enumerate(self.found_wallets, 1):
                print(f"\n🏆 Jackpot #{i} from {wallet['dataset']}:")
                print(f"   🔑 Key: {wallet['private_key'][:16]}...")
                print(f"   💰 ETH: {wallet['eth_balance']} wei")
                print(f"   💰 BTC: {wallet['btc_balance']} sat")
                print(f"   🎲 Entropy: {wallet['entropy_score']:.3f}")
        else:
            print(f"\n💡 No funded wallets found across all datasets")
            print(f"🎯 Laser precision hunt complete - ready for next strategy")
        
        print(f"\n📋 Dataset Summary:")
        for dataset in self.datasets_checked:
            print(f"   • {dataset['name']}: {dataset['keys_hunted']} keys hunted")

def main():
    """Execute multi-dataset precision hunt"""
    hunter = MultiDatasetHunter()
    hunter.scan_all_available_datasets()

if __name__ == "__main__":
    main()
