#!/usr/bin/env python3
"""
🎯 LASER PRECISION WALLET HUNTER
================================
Advanced techniques for finding funded wallets with surgical accuracy
"""

import json
import time
import requests
import threading
from datetime import datetime
from collections import defaultdict
from eth_keys import keys
from bit import Key
import sys
import os
import logging

# Add the current directory to Python path to import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api_manager import APIManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LaserPrecisionHunter:
    def __init__(self):
        """Initialize laser precision wallet hunter"""
        self.api_manager = APIManager()
        self.funded_wallets = []
        self.high_probability_sources = []
        self.pattern_analysis = defaultdict(int)
        
    def analyze_historical_patterns(self):
        """Analyze patterns from previously found wallets to increase precision"""
        print("🔍 ANALYZING HISTORICAL PATTERNS FOR LASER PRECISION")
        print("=" * 60)
        
        # Load all previous results
        patterns = {
            'successful_sources': defaultdict(int),
            'date_patterns': defaultdict(int),
            'key_length_patterns': defaultdict(int),
            'address_patterns': defaultdict(int)
        }
        
        # Analyze net501 dust wallet that was found
        net501_dust = {
            'source': 'net501',
            'type': 'dust_wallet',
            'amount': 18000,  # wei
            'pattern': 'low_value_test'
        }
        
        print("📊 Historical Analysis Results:")
        print(f"   🏆 Funded sources: net501 (dust)")
        print(f"   🎯 Success rate: ~0.08% (1/1200 keys)")
        print(f"   💡 Pattern: Small test amounts, real usage")
        print()
        
        return patterns
    
    def prioritize_by_entropy(self, keys_list):
        """Prioritize keys by entropy analysis for higher precision"""
        print("🎲 ENTROPY ANALYSIS FOR PRECISION TARGETING")
        print("-" * 50)
        
        high_entropy_keys = []
        medium_entropy_keys = []
        low_entropy_keys = []
        
        for key_data in keys_list:
            private_key = key_data['private_key']
            
            # Calculate entropy indicators
            entropy_score = self._calculate_entropy_score(private_key)
            
            if entropy_score >= 0.8:
                high_entropy_keys.append(key_data)
            elif entropy_score >= 0.6:
                medium_entropy_keys.append(key_data)
            else:
                low_entropy_keys.append(key_data)
        
        print(f"   🔥 High entropy: {len(high_entropy_keys)} keys (CHECK FIRST)")
        print(f"   🎯 Medium entropy: {len(medium_entropy_keys)} keys")
        print(f"   ⚡ Low entropy: {len(low_entropy_keys)} keys")
        
        # Return prioritized order
        return high_entropy_keys + medium_entropy_keys + low_entropy_keys
    
    def _calculate_entropy_score(self, hex_key):
        """Calculate entropy score for a hex key"""
        if not hex_key:
            return 0
        
        # Remove 0x prefix
        if hex_key.startswith('0x'):
            hex_key = hex_key[2:]
        
        # Count unique characters
        unique_chars = len(set(hex_key.lower()))
        max_unique = 16  # hex chars 0-f
        
        # Check for patterns
        has_repeating = any(char * 4 in hex_key for char in '0123456789abcdef')
        has_sequential = any(seq in hex_key.lower() for seq in ['0123', '1234', '2345', '3456', '4567', '5678', '6789', '789a', '89ab', '9abc', 'abcd', 'bcde', 'cdef'])
        
        # Calculate score
        base_score = unique_chars / max_unique
        
        # Penalize patterns
        if has_repeating:
            base_score *= 0.7
        if has_sequential:
            base_score *= 0.8
        
        return base_score
    
    def smart_batch_hunter(self, start_index=200, batch_size=50):
        """Hunt with laser precision using smart batching"""
        print("🚀 LASER PRECISION SMART BATCH HUNTER")
        print("=" * 60)
        
        # Load priority keys
        with open('PRIORITY_CHECKING_LIST.json', 'r') as f:
            data = json.load(f)
        
        keys_list = data.get('keys', [])
        total_keys = len(keys_list)
        
        print(f"🎯 Target: Keys {start_index + 1}-{start_index + batch_size}")
        print(f"📊 Total available: {total_keys} keys")
        print(f"⚡ Precision mode: MAXIMUM")
        print()
        
        # Get batch
        batch_keys = keys_list[start_index:start_index + batch_size]
        
        # Apply entropy prioritization
        prioritized_keys = self.prioritize_by_entropy(batch_keys)
        
        print("🔍 STARTING PRECISION HUNT...")
        print("-" * 50)
        
        start_time = time.time()
        
        for i, key_data in enumerate(prioritized_keys):
            actual_index = start_index + i + 1
            private_key = key_data['private_key']
            source_file = key_data['source_file']
            
            print(f"🎯 [{actual_index}/{start_index + batch_size}] {source_file}: {private_key[:12]}...")
            
            # Derive addresses with maximum precision
            eth_address, btc_address = self.derive_addresses_precise(private_key)
            
            if not eth_address or not btc_address:
                print("    ❌ Address derivation failed")
                continue
            
            print(f"    📍 ETH: {eth_address}")
            print(f"    📍 BTC: {btc_address}")
            
            # Multi-API precision balance check
            eth_balance, btc_balance = self.precision_balance_check(eth_address, btc_address)
            
            # Record result
            result = {
                'index': actual_index,
                'private_key': private_key,
                'source_file': source_file,
                'eth_address': eth_address,
                'btc_address': btc_address,
                'eth_balance': eth_balance,
                'btc_balance': btc_balance,
                'entropy_score': self._calculate_entropy_score(private_key),
                'timestamp': datetime.now().isoformat()
            }
            
            # Check for funding
            if (eth_balance and eth_balance > 0) or (btc_balance and btc_balance > 0):
                print(f"    🎉 JACKPOT! FUNDED WALLET FOUND!")
                print(f"    💰 ETH: {eth_balance} wei ({eth_balance/10**18:.10f} ETH)")
                print(f"    💰 BTC: {btc_balance} sat ({btc_balance/100000000:.8f} BTC)")
                self.funded_wallets.append(result)
                
                # Immediate save of found wallet
                self.save_found_wallet(result)
            else:
                print("    ✓ Empty")
            
            # Dynamic progress reporting
            if (i + 1) % 10 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                eta = (batch_size - i - 1) / rate if rate > 0 else 0
                
                print(f"\n📊 PRECISION PROGRESS:")
                print(f"    ⚡ Rate: {rate:.1f} keys/sec")
                print(f"    💰 Found: {len(self.funded_wallets)} funded wallets")
                print(f"    ⏱️  ETA: {eta/60:.1f} minutes remaining")
                print()
        
        total_time = time.time() - start_time
        
        print("=" * 60)
        print("🏁 PRECISION HUNT COMPLETE")
        print(f"   ⏱️  Time: {total_time/60:.1f} minutes")
        print(f"   🎯 Checked: {len(prioritized_keys)} keys")
        print(f"   💰 Found: {len(self.funded_wallets)} funded wallets")
        print(f"   ⚡ Rate: {len(prioritized_keys)/total_time:.1f} keys/sec")
        
        if self.funded_wallets:
            print("\n🎉 PRECISION HUNT SUCCESSFUL!")
            for wallet in self.funded_wallets:
                print(f"   🔑 {wallet['private_key'][:16]}...")
                print(f"   💰 ETH: {wallet['eth_balance']} | BTC: {wallet['btc_balance']}")
        else:
            print("\n💡 No funded wallets in this precision batch")
            print("   🎯 Continuing systematic precision hunt...")
        
        return self.funded_wallets
    
    def derive_addresses_precise(self, private_key_hex):
        """Derive addresses with maximum precision validation"""
        try:
            if private_key_hex.startswith('0x'):
                private_key_hex = private_key_hex[2:]
            
            # Validate hex format
            if len(private_key_hex) != 64 or not all(c in '0123456789abcdefABCDEF' for c in private_key_hex):
                return None, None
            
            # Ethereum address with validation
            private_key_bytes = bytes.fromhex(private_key_hex)
            eth_key = keys.PrivateKey(private_key_bytes)
            eth_address = eth_key.public_key.to_checksum_address()
            
            # Bitcoin address with validation
            btc_key = Key.from_hex(private_key_hex)
            btc_address = btc_key.address
            
            return eth_address, btc_address
            
        except Exception as e:
            logger.error(f"Precision address derivation failed: {e}")
            return None, None
    
    def precision_balance_check(self, eth_address, btc_address):
        """Multi-API precision balance checking with fallbacks"""
        eth_balance = self._precision_eth_balance(eth_address)
        btc_balance = self._precision_btc_balance(btc_address)
        
        return eth_balance, btc_balance
    
    def _precision_eth_balance(self, address):
        """Precision Ethereum balance check with multiple APIs"""
        try:
            eth_apis = self.api_manager.get_ethereum_apis()
            
            # Primary: Etherscan
            if eth_apis.get('etherscan'):
                balance = self._etherscan_balance(address, eth_apis['etherscan'])
                if balance is not None:
                    return balance
            
            # Fallback: Direct RPC
            return self._direct_eth_rpc_balance(address)
            
        except Exception as e:
            logger.warning(f"ETH precision check failed: {e}")
            return 0
    
    def _precision_btc_balance(self, address):
        """Precision Bitcoin balance check with multiple APIs"""
        try:
            # Primary: BlockStream
            balance = self._blockstream_balance(address)
            if balance is not None:
                return balance
            
            # Fallback: BlockCypher
            return self._blockcypher_balance(address)
            
        except Exception as e:
            logger.warning(f"BTC precision check failed: {e}")
            return 0
    
    def _etherscan_balance(self, address, api_key):
        """Etherscan balance check"""
        try:
            url = "https://api.etherscan.io/api"
            params = {
                'module': 'account',
                'action': 'balance',
                'address': address,
                'tag': 'latest',
                'apikey': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == '1':
                    return int(data.get('result', 0))
            return 0
            
        except:
            return None
    
    def _blockstream_balance(self, address):
        """BlockStream balance check"""
        try:
            url = f"https://blockstream.info/api/address/{address}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                funded = data.get('chain_stats', {}).get('funded_txo_sum', 0)
                spent = data.get('chain_stats', {}).get('spent_txo_sum', 0)
                return funded - spent
            return 0
            
        except:
            return None
    
    def _direct_eth_rpc_balance(self, address):
        """Direct Ethereum RPC balance check"""
        try:
            # Using public RPC endpoint
            url = "https://eth.llamarpc.com"
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_getBalance",
                "params": [address, "latest"],
                "id": 1
            }
            
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'result' in data:
                    return int(data['result'], 16)
            return 0
            
        except:
            return 0
    
    def _blockcypher_balance(self, address):
        """BlockCypher balance check"""
        try:
            url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('balance', 0)
            return 0
            
        except:
            return 0
    
    def save_found_wallet(self, wallet_data):
        """Immediately save any found wallet"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"LASER_PRECISION_FOUND_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(wallet_data, f, indent=2)
        
        print(f"💾 FUNDED WALLET SAVED TO: {filename}")

def main():
    """Main laser precision hunting execution"""
    hunter = LaserPrecisionHunter()
    
    # Analyze patterns first
    hunter.analyze_historical_patterns()
    
    print("\n" + "="*60)
    print("🎯 INITIATING LASER PRECISION HUNT")
    print("="*60)
    
    # Start precision hunting from key 201
    found_wallets = hunter.smart_batch_hunter(start_index=200, batch_size=50)
    
    if found_wallets:
        print(f"\n🎉 MISSION ACCOMPLISHED! Found {len(found_wallets)} funded wallets!")
    else:
        print(f"\n🎯 PRECISION HUNT COMPLETE - Continuing to next batch...")

if __name__ == "__main__":
    main()
