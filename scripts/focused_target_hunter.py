#!/usr/bin/env python3
"""
🎯 FOCUSED TARGET HUNTER
========================
Hunt only the highest-probability remaining keys with maximum efficiency
"""

import json
import time
import requests
from datetime import datetime
from eth_keys import keys
from bit import Key
from api_manager import APIManager
import os

class FocusedTargetHunter:
    def __init__(self):
        """Initialize focused target hunter"""
        self.api_manager = APIManager()
        self.found_wallets = []
        self.checked_count = 0
        
    def execute_focused_hunt(self):
        """Execute focused hunt on highest-probability targets"""
        print("🎯 FOCUSED TARGET HUNTER")
        print("=" * 60)
        print("🔥 Strategy: Hunt only the highest-probability keys for maximum efficiency")
        
        # Load all previously created high-priority key lists
        priority_sources = self.find_priority_sources()
        
        print(f"\n📊 HIGH-PRIORITY SOURCES FOUND:")
        for i, source in enumerate(priority_sources, 1):
            print(f"   {i}. {source['name']}: {source['count']} keys")
        
        total_targets = sum(s['count'] for s in priority_sources)
        print(f"\n🎯 TOTAL HIGH-PRIORITY TARGETS: {total_targets}")
        
        # Hunt each priority source
        for source in priority_sources:
            print(f"\n🔍 HUNTING: {source['name']}")
            
            found_in_source = self.hunt_priority_source(source)
            
            if found_in_source:
                print(f"🎉 Found {found_in_source} funded wallets in {source['name']}!")
        
        self.show_focused_results()
        
        # If no more found, continue with next priority datasets
        if not self.found_wallets:
            print(f"\n🎯 No funded wallets in high-priority sources")
            print(f"🔥 Expanding search to next-tier sources...")
            self.hunt_next_tier_sources()
    
    def find_priority_sources(self):
        """Find all high-priority key sources"""
        sources = []
        
        # Priority files (manually created lists of high-probability keys)
        priority_files = [
            'SMART_HUNTING_TARGETS_20250813_095455.json',
            'PRIORITY_CHECKING_LIST.json', 
            'validated_candidates.json',
            'net599_FUNDED_keys.txt',  # Already found one here
            'METAMASK_BATCH2_RESULTS.json',
            'zelcore_balance_check.json',
            'combined_major_discovery_keys.json',
            'major_discovery_keys_list.txt',
            'net501_sample_keys.txt',
            'extracted_keys_172_58_122_84.txt'
        ]
        
        for filename in priority_files:
            if os.path.exists(filename):
                count = self.count_keys_in_file(filename)
                if count > 0:
                    sources.append({
                        'name': filename,
                        'path': filename,
                        'count': count,
                        'type': 'priority'
                    })
        
        return sources
    
    def count_keys_in_file(self, filename):
        """Count keys in a file"""
        try:
            if filename.endswith('.json'):
                with open(filename, 'r') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    return len(data)
                elif isinstance(data, dict):
                    if 'keys' in data:
                        return len(data['keys'])
                    else:
                        return len([v for v in data.values() if isinstance(v, list)][:1])
                return 0
                
            elif filename.endswith('.txt'):
                with open(filename, 'r') as f:
                    lines = f.readlines()
                return len([line for line in lines if len(line.strip()) == 64])
            
        except:
            return 0
        
        return 0
    
    def hunt_priority_source(self, source):
        """Hunt a priority source with laser precision"""
        keys_data = self.load_keys_from_source(source)
        
        if not keys_data:
            print(f"   ❌ Could not load keys")
            return 0
        
        print(f"   ✅ Loaded {len(keys_data)} keys")
        print(f"   🎯 Hunting with laser precision...")
        
        found_count = 0
        
        for i, key_data in enumerate(keys_data):
            private_key = key_data.get('private_key')
            if not private_key:
                continue
            
            # Quick balance check
            result = self.quick_balance_check(private_key, i + 1, source['name'])
            
            if result:
                found_count += 1
                print(f"\n🎉 JACKPOT #{len(self.found_wallets) + 1} FOUND!")
                print(f"   🔑 Key: {private_key[:16]}...")
                print(f"   💰 ETH: {result['eth_balance']:,} wei")
                print(f"   💰 BTC: {result['btc_balance']:,} sat")
                
                # Save immediately
                self.save_jackpot_immediately(result, source['name'])
                self.found_wallets.append(result)
            
            self.checked_count += 1
            
            # Small delay for API rate limiting
            time.sleep(0.05)
        
        print(f"   ✅ Checked {len(keys_data)} keys from {source['name']}")
        return found_count
    
    def load_keys_from_source(self, source):
        """Load keys from a source"""
        path = source['path']
        keys = []
        
        try:
            if path.endswith('.json'):
                with open(path, 'r') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            # Handle different key field names
                            private_key = None
                            for field in ['private_key', 'privateKey', 'key', 'hex_key']:
                                if field in item:
                                    private_key = item[field]
                                    break
                            
                            if private_key:
                                keys.append({'private_key': private_key, 'source_file': path})
                        elif isinstance(item, str) and len(item) >= 64:
                            keys.append({'private_key': item, 'source_file': path})
                
                elif isinstance(data, dict):
                    if 'keys' in data and isinstance(data['keys'], list):
                        for item in data['keys']:
                            if isinstance(item, dict) and 'private_key' in item:
                                keys.append(item)
                            elif isinstance(item, str) and len(item) >= 64:
                                keys.append({'private_key': item, 'source_file': path})
            
            elif path.endswith('.txt'):
                with open(path, 'r') as f:
                    lines = f.readlines()
                
                for line in lines:
                    line = line.strip()
                    if len(line) == 64 and all(c in '0123456789abcdefABCDEF' for c in line):
                        keys.append({'private_key': line, 'source_file': path})
        
        except Exception as e:
            print(f"   ❌ Error loading {path}: {e}")
            return []
        
        return keys
    
    def quick_balance_check(self, private_key, index, source_name):
        """Quick balance check for a single key"""
        try:
            # Derive addresses
            eth_address, btc_address = self.derive_addresses(private_key)
            
            if not eth_address or not btc_address:
                return None
            
            # Check balances
            eth_balance = self.check_eth_balance(eth_address)
            btc_balance = self.check_btc_balance(btc_address)
            
            if eth_balance > 0 or btc_balance > 0:
                return {
                    'private_key': private_key,
                    'eth_address': eth_address,
                    'btc_address': btc_address,
                    'eth_balance': eth_balance,
                    'btc_balance': btc_balance,
                    'found_in_source': source_name,
                    'timestamp': datetime.now().isoformat()
                }
            
            return None
        
        except Exception:
            return None
    
    def derive_addresses(self, private_key_hex):
        """Derive addresses from private key"""
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
        """Check Ethereum balance"""
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
        """Check Bitcoin balance"""
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
    
    def save_jackpot_immediately(self, result, source_name):
        """Save jackpot immediately"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"FOCUSED_JACKPOT_{len(self.found_wallets) + 1}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"      💾 JACKPOT SAVED: {filename}")
    
    def hunt_next_tier_sources(self):
        """Hunt next-tier sources if no success in priority sources"""
        print(f"\n🎯 HUNTING NEXT-TIER SOURCES")
        print("=" * 40)
        
        # Next tier: Smaller but potentially valuable sources
        next_tier_files = [
            'net602_direct_keys.json',
            'net605_direct_keys.json',
            'net599_cache_keys.txt',
            'critical_findings_data.json',
            'funded_addresses_consolidated.json'
        ]
        
        for filename in next_tier_files:
            if os.path.exists(filename):
                print(f"\n🔍 Hunting: {filename}")
                
                source = {
                    'name': filename,
                    'path': filename,
                    'count': self.count_keys_in_file(filename),
                    'type': 'next_tier'
                }
                
                if source['count'] > 0:
                    found = self.hunt_priority_source(source)
                    if found:
                        print(f"🎉 Found {found} funded wallets in {filename}!")
                        break
    
    def show_focused_results(self):
        """Show focused hunt results"""
        print("\n" + "=" * 60)
        print("🏁 FOCUSED TARGET HUNT COMPLETE")
        print("=" * 60)
        
        print(f"🎯 Total keys checked: {self.checked_count:,}")
        print(f"💰 Funded wallets found: {len(self.found_wallets)}")
        
        if self.found_wallets:
            total_eth = sum(w.get('eth_balance', 0) for w in self.found_wallets)
            total_btc = sum(w.get('btc_balance', 0) for w in self.found_wallets)
            
            print(f"\n🎉 SUCCESS! Total value discovered:")
            print(f"   💰 ETH: {total_eth:,} wei ({total_eth / 1e18:.18f} ETH)")
            print(f"   💰 BTC: {total_btc:,} sat ({total_btc / 1e8:.8f} BTC)")
            
            for i, wallet in enumerate(self.found_wallets, 1):
                print(f"\n🏆 Jackpot #{i}:")
                print(f"   🔑 Key: {wallet['private_key'][:16]}...")
                print(f"   📍 ETH: {wallet['eth_address']}")
                print(f"   📍 BTC: {wallet['btc_address']}")
                print(f"   💰 ETH: {wallet['eth_balance']:,} wei")
                print(f"   💰 BTC: {wallet['btc_balance']:,} sat")
                print(f"   📂 Source: {wallet['found_in_source']}")
        else:
            print(f"\n💡 No additional funded wallets found in focused hunt")
            print(f"🎯 Consider expanding to larger datasets with targeted sampling")

def main():
    """Execute focused target hunt"""
    hunter = FocusedTargetHunter()
    hunter.execute_focused_hunt()

if __name__ == "__main__":
    main()
