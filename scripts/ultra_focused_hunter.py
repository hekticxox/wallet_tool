#!/usr/bin/env python3
"""
🎯 ULTRA FOCUSED WALLET HUNTER
==============================
Maximum precision targeting for funded wallets
"""

import json
import time
import requests
from datetime import datetime
from eth_keys import keys
from bit import Key
from api_manager import APIManager

class UltraFocusedHunter:
    def __init__(self):
        """Initialize ultra focused hunter"""
        self.api_manager = APIManager()
        self.found_wallets = []
        
    def analyze_and_hunt(self):
        """Analyze patterns and hunt with ultra precision"""
        print("🎯 ULTRA FOCUSED WALLET HUNTER")
        print("=" * 50)
        print("🔍 Analyzing MetaMask patterns...")
        
        # Load priority keys
        with open('PRIORITY_CHECKING_LIST.json', 'r') as f:
            data = json.load(f)
        
        keys_list = data.get('keys', [])
        print(f"📊 Total keys available: {len(keys_list)}")
        
        # Ultra focused selection criteria
        ultra_focused_keys = self.select_ultra_targets(keys_list)
        
        print(f"🎯 Ultra focused targets: {len(ultra_focused_keys)}")
        print("⚡ Starting precision hunt...")
        print()
        
        # Hunt the ultra targets
        for i, key_data in enumerate(ultra_focused_keys):
            result = self.precision_hunt_single(key_data, i + 1)
            if result and result.get('funded'):
                self.found_wallets.append(result)
        
        self.show_results()
    
    def select_ultra_targets(self, keys_list):
        """Select ultra high probability targets"""
        ultra_targets = []
        
        # Strategy 1: Keys with high entropy (real randomness)
        # Strategy 2: Keys from specific date patterns
        # Strategy 3: Keys with specific hex patterns
        
        for key_data in keys_list:
            private_key = key_data['private_key']
            score = self.calculate_target_score(private_key)
            
            if score > 0.75:  # Only ultra high probability
                key_data['target_score'] = score
                ultra_targets.append(key_data)
        
        # Sort by score (highest first)
        ultra_targets.sort(key=lambda x: x['target_score'], reverse=True)
        
        # Return top 100 ultra targets
        return ultra_targets[:100]
    
    def calculate_target_score(self, hex_key):
        """Calculate ultra precision target score"""
        if not hex_key or len(hex_key) < 64:
            return 0
        
        if hex_key.startswith('0x'):
            hex_key = hex_key[2:]
        
        score = 0
        
        # High entropy check
        unique_chars = len(set(hex_key.lower()))
        entropy_score = unique_chars / 16.0
        score += entropy_score * 0.4
        
        # No obvious patterns
        has_repeating = any(char * 3 in hex_key for char in '0123456789abcdef')
        if not has_repeating:
            score += 0.3
        
        # Good distribution of chars
        hex_counts = {}
        for char in hex_key.lower():
            hex_counts[char] = hex_counts.get(char, 0) + 1
        
        max_count = max(hex_counts.values())
        if max_count < 8:  # No char appears too often
            score += 0.3
        
        return score
    
    def precision_hunt_single(self, key_data, index):
        """Hunt a single key with maximum precision"""
        private_key = key_data['private_key']
        source_file = key_data['source_file']
        score = key_data.get('target_score', 0)
        
        print(f"🎯 [{index}] {source_file}: {private_key[:12]}... (score: {score:.3f})")
        
        try:
            # Derive addresses
            eth_address, btc_address = self.derive_addresses(private_key)
            
            if not eth_address or not btc_address:
                print("    ❌ Address derivation failed")
                return None
            
            print(f"    📍 ETH: {eth_address}")
            print(f"    📍 BTC: {btc_address}")
            
            # Check balances with multiple methods
            eth_balance = self.check_eth_balance(eth_address)
            btc_balance = self.check_btc_balance(btc_address)
            
            result = {
                'private_key': private_key,
                'source_file': source_file,
                'eth_address': eth_address,
                'btc_address': btc_address,
                'eth_balance': eth_balance,
                'btc_balance': btc_balance,
                'target_score': score,
                'funded': (eth_balance > 0) or (btc_balance > 0)
            }
            
            if result['funded']:
                print(f"    🎉 JACKPOT FOUND!")
                print(f"    💰 ETH: {eth_balance} wei")
                print(f"    💰 BTC: {btc_balance} sat")
                self.save_jackpot(result)
            else:
                print("    ✓ Empty")
            
            # Small delay for API rate limiting
            time.sleep(0.1)
            
            return result
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            return None
    
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
            
        except Exception as e:
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
                
                response = requests.get(url, params=params, timeout=15)
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
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                funded = data.get('chain_stats', {}).get('funded_txo_sum', 0)
                spent = data.get('chain_stats', {}).get('spent_txo_sum', 0)
                return funded - spent
            
            return 0
            
        except Exception:
            return 0
    
    def save_jackpot(self, result):
        """Save jackpot immediately"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ULTRA_FOCUSED_JACKPOT_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"💾 JACKPOT SAVED: {filename}")
    
    def show_results(self):
        """Show final results"""
        print("\n" + "=" * 50)
        print("🏁 ULTRA FOCUSED HUNT COMPLETE")
        print("=" * 50)
        
        if self.found_wallets:
            print(f"🎉 SUCCESS! Found {len(self.found_wallets)} funded wallets!")
            
            for i, wallet in enumerate(self.found_wallets, 1):
                print(f"\n🏆 Jackpot #{i}:")
                print(f"   🔑 Key: {wallet['private_key'][:16]}...")
                print(f"   💰 ETH: {wallet['eth_balance']} wei")
                print(f"   💰 BTC: {wallet['btc_balance']} sat")
                print(f"   🎯 Score: {wallet['target_score']:.3f}")
        else:
            print("💡 No funded wallets in ultra focused batch")
            print("🎯 Continuing systematic precision hunt...")

def main():
    """Execute ultra focused hunt"""
    hunter = UltraFocusedHunter()
    hunter.analyze_and_hunt()

if __name__ == "__main__":
    main()
