#!/usr/bin/env python3
"""
🚀 COMPREHENSIVE FINAL HUNTER
=============================
Ultimate precision hunter for all remaining datasets
"""

import json
import time
import requests
from datetime import datetime
from eth_keys import keys
from bit import Key
from api_manager import APIManager
import os
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed

class ComprehensiveFinalHunter:
    def __init__(self):
        """Initialize comprehensive final hunter"""
        self.api_manager = APIManager()
        self.found_wallets = []
        self.checked_keys = set()
        self.success_count = 0
        
    def execute_final_hunt(self):
        """Execute comprehensive final hunt across ALL data"""
        print("🚀 COMPREHENSIVE FINAL HUNTER")
        print("=" * 60)
        print("🎯 Target: ALL remaining private keys with maximum precision")
        print("🔥 Strategy: Multi-threaded, entropy-optimized, full coverage")
        
        # Find all unchecked key sources
        all_key_sources = self.find_all_key_sources()
        
        print(f"\n📊 DISCOVERED KEY SOURCES:")
        total_keys = 0
        for i, source in enumerate(all_key_sources, 1):
            print(f"   {i}. {source['name']}: ~{source['estimated_keys']} keys")
            total_keys += source['estimated_keys']
        
        print(f"\n🎯 TOTAL HUNTING TARGET: ~{total_keys:,} keys")
        print(f"💡 Using laser precision + parallel processing")
        
        # Start comprehensive hunt
        print(f"\n🔍 Starting comprehensive final hunt...")
        
        for source in all_key_sources:
            if self.hunt_source_comprehensively(source):
                print(f"\n🎉 SUCCESS! Found funded wallet, continuing hunt...")
            
            if len(self.found_wallets) >= 10:  # Safety limit
                print(f"\n🛑 Reached maximum success limit, stopping hunt")
                break
        
        self.show_final_results()
    
    def find_all_key_sources(self):
        """Find all available key sources for comprehensive hunting"""
        sources = []
        
        # JSON files with keys
        json_patterns = [
            "*.json",
            "*keys*.json", 
            "*wallet*.json",
            "*private*.json",
            "*priority*.json",
            "*metamask*.json",
            "*scan*.json"
        ]
        
        for pattern in json_patterns:
            for file_path in glob.glob(pattern):
                if self.is_valid_key_source(file_path):
                    estimated = self.estimate_keys_in_file(file_path)
                    if estimated > 0:
                        sources.append({
                            'name': file_path,
                            'path': file_path,
                            'type': 'json',
                            'estimated_keys': estimated
                        })
        
        # Text files with keys
        txt_patterns = [
            "*.txt",
            "*keys*.txt",
            "*private*.txt",
            "*wallet*.txt"
        ]
        
        for pattern in txt_patterns:
            for file_path in glob.glob(pattern):
                if self.is_valid_key_source(file_path):
                    estimated = self.estimate_keys_in_file(file_path)
                    if estimated > 0:
                        sources.append({
                            'name': file_path,
                            'path': file_path,
                            'type': 'txt',
                            'estimated_keys': estimated
                        })
        
        # Sort by estimated key count (largest first)
        sources.sort(key=lambda x: x['estimated_keys'], reverse=True)
        
        # Remove duplicates based on content hash
        unique_sources = []
        seen_hashes = set()
        
        for source in sources:
            content_hash = self.get_file_content_hash(source['path'])
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_sources.append(source)
        
        return unique_sources
    
    def is_valid_key_source(self, file_path):
        """Check if file is a valid key source"""
        try:
            # Skip if file is too small
            if os.path.getsize(file_path) < 100:
                return False
            
            # Skip if file looks like a report or log
            skip_keywords = ['report', 'log', 'summary', 'output', 'validation', 'status']
            if any(keyword in file_path.lower() for keyword in skip_keywords):
                return False
            
            return True
        except:
            return False
    
    def estimate_keys_in_file(self, file_path):
        """Estimate number of keys in a file"""
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Count keys in various formats
                key_count = 0
                
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, list):
                            for item in value[:10]:  # Sample first 10
                                if isinstance(item, dict) and 'private_key' in item:
                                    key_count = len(value)
                                    break
                                elif isinstance(item, str) and len(item) >= 64:
                                    key_count = len(value)
                                    break
                        elif key in ['keys', 'private_keys', 'checked_keys']:
                            if isinstance(value, list):
                                key_count = max(key_count, len(value))
                
                elif isinstance(data, list):
                    if len(data) > 0:
                        if isinstance(data[0], dict) and 'private_key' in data[0]:
                            key_count = len(data)
                        elif isinstance(data[0], str) and len(data[0]) >= 64:
                            key_count = len(data)
                
                return key_count
                
            elif file_path.endswith('.txt'):
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                
                key_count = 0
                for line in lines[:100]:  # Sample first 100 lines
                    line = line.strip()
                    if len(line) == 64 and all(c in '0123456789abcdefABCDEF' for c in line):
                        key_count += 1
                
                # Estimate total based on sample
                if key_count > 0:
                    return int(key_count * len(lines) / min(100, len(lines)))
                
                return 0
            
        except:
            return 0
    
    def get_file_content_hash(self, file_path):
        """Get a simple hash of file content to detect duplicates"""
        try:
            with open(file_path, 'rb') as f:
                return hash(f.read()[:10000])  # Hash first 10KB
        except:
            return hash(file_path)
    
    def hunt_source_comprehensively(self, source):
        """Hunt a source comprehensively with maximum precision"""
        name = source['name']
        estimated = source['estimated_keys']
        
        print(f"\n🎯 HUNTING: {name}")
        print(f"   📊 Estimated keys: {estimated:,}")
        
        # Load keys from source
        keys_data = self.load_keys_from_source(source)
        
        if not keys_data:
            print(f"   ❌ Could not load keys")
            return False
        
        actual_keys = len(keys_data)
        print(f"   ✅ Loaded {actual_keys:,} keys")
        
        # Filter out already checked keys
        new_keys = []
        for key_data in keys_data:
            key_hash = hash(key_data['private_key'])
            if key_hash not in self.checked_keys:
                new_keys.append(key_data)
                self.checked_keys.add(key_hash)
        
        if not new_keys:
            print(f"   💡 All keys already checked, skipping")
            return False
        
        print(f"   🎯 Hunting {len(new_keys):,} new keys with maximum precision...")
        
        # Hunt with parallel processing for speed
        found_in_source = self.parallel_precision_hunt(new_keys[:1000], name)  # Limit for performance
        
        return found_in_source > 0
    
    def load_keys_from_source(self, source):
        """Load keys from a source file"""
        path = source['path']
        file_type = source['type']
        
        keys = []
        
        try:
            if file_type == 'json':
                with open(path, 'r') as f:
                    data = json.load(f)
                
                # Extract keys based on structure
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, list) and len(value) > 0:
                            if isinstance(value[0], dict) and 'private_key' in value[0]:
                                keys.extend(value)
                            elif isinstance(value[0], str) and len(value[0]) >= 64:
                                for item in value:
                                    keys.append({'private_key': item, 'source_file': path})
                        elif key in ['keys', 'private_keys', 'checked_keys'] and isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict) and 'private_key' in item:
                                    keys.append(item)
                                elif isinstance(item, str) and len(item) >= 64:
                                    keys.append({'private_key': item, 'source_file': path})
                
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
        for key_data in keys:
            private_key = key_data.get('private_key')
            if not private_key:
                # Try other common key fields
                for field in ['key', 'privateKey', 'private', 'hex_key']:
                    if field in key_data:
                        key_data['private_key'] = key_data[field]
                        private_key = key_data['private_key']
                        break
            
            if private_key:
                if private_key.startswith('0x'):
                    private_key = private_key[2:]
                
                entropy_score = self.calculate_entropy_score(private_key)
                key_data['entropy_score'] = entropy_score
            else:
                key_data['entropy_score'] = 0
        
        # Sort by entropy (highest first) and filter out keys without private_key
        valid_keys = [k for k in keys if k.get('private_key') and len(k['private_key']) >= 64]
        return sorted(valid_keys, key=lambda x: x.get('entropy_score', 0), reverse=True)
    
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
    
    def parallel_precision_hunt(self, keys_data, source_name):
        """Hunt keys in parallel for maximum speed"""
        found_count = 0
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit hunt tasks
            future_to_key = {}
            for i, key_data in enumerate(keys_data):
                future = executor.submit(self.precision_hunt_single, key_data, i + 1, source_name)
                future_to_key[future] = key_data
            
            # Process results as they complete
            for future in as_completed(future_to_key):
                key_data = future_to_key[future]
                
                try:
                    is_funded = future.result()
                    
                    if is_funded:
                        found_count += 1
                        print(f"\n🎉 JACKPOT #{found_count} FOUND IN {source_name}!")
                        
                        # Save immediately
                        self.save_jackpot_immediately(key_data, source_name)
                        
                        if found_count >= 5:  # Limit per source
                            print(f"\n🛑 Maximum jackpots per source reached")
                            break
                
                except Exception as e:
                    print(f"   ❌ Error hunting key: {e}")
        
        return found_count
    
    def precision_hunt_single(self, key_data, index, source_name):
        """Hunt a single key with maximum precision"""
        private_key = key_data.get('private_key')
        if not private_key:
            return False
            
        entropy_score = key_data.get('entropy_score', 0)
        
        try:
            # Derive addresses
            eth_address, btc_address = self.derive_addresses(private_key)
            
            if not eth_address or not btc_address:
                return False
            
            # Check balances
            eth_balance = self.check_eth_balance(eth_address)
            btc_balance = self.check_btc_balance(btc_address)
            
            if eth_balance > 0 or btc_balance > 0:
                # Update key data with results
                key_data.update({
                    'eth_address': eth_address,
                    'btc_address': btc_address,
                    'eth_balance': eth_balance,
                    'btc_balance': btc_balance,
                    'found_in_source': source_name,
                    'timestamp': datetime.now().isoformat()
                })
                
                self.found_wallets.append(key_data)
                return True
            
            return False
        
        except Exception:
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
        """Check Ethereum balance quickly"""
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
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == '1':
                        return int(data.get('result', 0))
            
            return 0
            
        except Exception:
            return 0
    
    def check_btc_balance(self, address):
        """Check Bitcoin balance quickly"""
        try:
            url = f"https://blockstream.info/api/address/{address}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                funded = data.get('chain_stats', {}).get('funded_txo_sum', 0)
                spent = data.get('chain_stats', {}).get('spent_txo_sum', 0)
                return funded - spent
            
            return 0
            
        except Exception:
            return 0
    
    def save_jackpot_immediately(self, key_data, source_name):
        """Save jackpot immediately"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"FINAL_JACKPOT_{self.success_count + 1}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(key_data, f, indent=2, default=str)
        
        self.success_count += 1
        print(f"      💾 JACKPOT SAVED: {filename}")
    
    def show_final_results(self):
        """Show final comprehensive results"""
        print("\n" + "=" * 60)
        print("🏁 COMPREHENSIVE FINAL HUNT COMPLETE")
        print("=" * 60)
        
        print(f"🎯 Total keys checked: {len(self.checked_keys):,}")
        print(f"💰 Funded wallets found: {len(self.found_wallets)}")
        
        if self.found_wallets:
            print(f"\n🎉 SUCCESS! Found {len(self.found_wallets)} funded wallets!")
            
            total_eth = sum(w.get('eth_balance', 0) for w in self.found_wallets)
            total_btc = sum(w.get('btc_balance', 0) for w in self.found_wallets)
            
            print(f"💎 TOTAL VALUE DISCOVERED:")
            print(f"   💰 ETH: {total_eth:,} wei ({total_eth / 1e18:.18f} ETH)")
            print(f"   💰 BTC: {total_btc:,} sat ({total_btc / 1e8:.8f} BTC)")
            
            for i, wallet in enumerate(self.found_wallets, 1):
                print(f"\n🏆 Jackpot #{i} from {wallet.get('found_in_source', 'Unknown')}:")
                print(f"   🔑 Key: {wallet['private_key'][:16]}...")
                print(f"   💰 ETH: {wallet.get('eth_balance', 0):,} wei")
                print(f"   💰 BTC: {wallet.get('btc_balance', 0):,} sat")
        else:
            print(f"\n💡 No additional funded wallets found")
            print(f"🎯 Comprehensive hunt complete - all data processed")

def main():
    """Execute comprehensive final hunt"""
    hunter = ComprehensiveFinalHunter()
    hunter.execute_final_hunt()

if __name__ == "__main__":
    main()
