#!/usr/bin/env python3
"""
🎯 ULTIMATE JACKPOT HUNTER 
========================
MAXIMUM PRECISION - LASER FOCUS ON FUNDED WALLETS
Using advanced filtering, pattern analysis, and real-time validation
"""

import json
import time
import requests
import os
import glob
import re
from datetime import datetime
from pathlib import Path
from eth_keys import keys
from bit import Key
from api_manager import APIManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UltimateJackpotHunter:
    def __init__(self):
        """Initialize the ultimate hunter"""
        self.api_manager = APIManager()
        self.found_jackpots = []
        self.checked_count = 0
        self.start_time = time.time()
        
    def calculate_entropy(self, hex_string):
        """Calculate entropy score for key quality"""
        if not hex_string:
            return 0
        
        # Remove common patterns
        patterns_to_avoid = [
            '000000', '111111', '222222', '333333', '444444', 
            '555555', '666666', '777777', '888888', '999999',
            'aaaaaa', 'bbbbbb', 'cccccc', 'dddddd', 'eeeeee', 'ffffff',
            '123456', 'abcdef', '1234567890'
        ]
        
        for pattern in patterns_to_avoid:
            if pattern in hex_string.lower():
                return 0.1
        
        # Check for reasonable entropy
        unique_chars = len(set(hex_string.lower()))
        if unique_chars < 8:
            return 0.2
        
        # High entropy keys get priority
        return min(unique_chars / 16.0, 1.0)
    
    def is_high_quality_key(self, key_hex):
        """Advanced key quality filter"""
        if not key_hex or len(key_hex) < 60:
            return False
        
        # Remove 0x prefix
        clean_key = key_hex.replace('0x', '').lower()
        
        # Must be valid hex
        try:
            int(clean_key, 16)
        except ValueError:
            return False
        
        # High entropy requirement
        entropy = self.calculate_entropy(clean_key)
        if entropy < 0.7:
            return False
        
        # Must not be sequential or repeated
        if any(clean_key[i:i+8] == clean_key[i+8:i+16] for i in range(len(clean_key)-16)):
            return False
        
        return True
    
    def derive_addresses_precise(self, private_key_hex):
        """Ultra-precise address derivation"""
        try:
            clean_key = private_key_hex.replace('0x', '')
            if len(clean_key) != 64:
                return None, None
            
            # Ethereum address
            private_key_bytes = bytes.fromhex(clean_key)
            eth_key = keys.PrivateKey(private_key_bytes)
            eth_address = eth_key.public_key.to_checksum_address()
            
            # Bitcoin address
            btc_key = Key.from_hex(clean_key)
            btc_address = btc_key.address
            
            return eth_address, btc_address
            
        except Exception as e:
            logger.debug(f"Address derivation failed: {e}")
            return None, None
    
    def check_ethereum_balance_ultra(self, address):
        """Ultra-precise Ethereum balance check"""
        try:
            eth_apis = self.api_manager.get_ethereum_apis()
            
            if eth_apis.get('etherscan'):
                api_key = eth_apis['etherscan']
                url = f"https://api.etherscan.io/api"
                
                params = {
                    'module': 'account',
                    'action': 'balance',
                    'address': address,
                    'tag': 'latest',
                    'apikey': api_key
                }
                
                response = requests.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == '1':
                        balance_wei = int(data.get('result', 0))
                        return balance_wei
            
            return 0
            
        except Exception as e:
            logger.warning(f"ETH balance check failed: {e}")
            return 0

    def check_bitcoin_balance_ultra(self, address):
        """Ultra-precise Bitcoin balance check"""
        try:
            # Multiple API attempts for maximum accuracy
            apis_to_try = [
                f"https://blockstream.info/api/address/{address}",
                f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance"
            ]
            
            for api_url in apis_to_try:
                try:
                    response = requests.get(api_url, timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'blockstream.info' in api_url:
                            balance_sat = data.get('chain_stats', {}).get('funded_txo_sum', 0) - \
                                        data.get('chain_stats', {}).get('spent_txo_sum', 0)
                            return balance_sat
                        elif 'blockcypher.com' in api_url:
                            return data.get('balance', 0)
                            
                except Exception as e:
                    continue
            
            return 0
            
        except Exception as e:
            logger.warning(f"BTC balance check failed: {e}")
            return 0
    
    def load_all_private_keys(self):
        """Load ALL private keys from ALL datasets with precision filtering"""
        print("🔍 LOADING ALL PRIVATE KEYS WITH PRECISION FILTERING...")
        
        all_keys = []
        key_sources = [
            'PRIORITY_CHECKING_LIST.json',
            'net599_private_keys.txt',
            'net599_FUNDED_keys.txt', 
            'net501_sample_keys.txt',
            'net602_direct_keys.json',
            'net605_direct_keys.json',
            'combined_major_discovery_keys.json'
        ]
        
        for source_file in key_sources:
            if os.path.exists(source_file):
                try:
                    print(f"📂 Loading {source_file}...")
                    
                    if source_file.endswith('.json'):
                        with open(source_file, 'r') as f:
                            data = json.load(f)
                            
                        if isinstance(data, dict):
                            if 'keys' in data:
                                keys_data = data['keys']
                            else:
                                keys_data = [data]
                        else:
                            keys_data = data
                        
                        for item in keys_data:
                            if isinstance(item, dict):
                                key = item.get('private_key', '')
                            else:
                                key = str(item)
                            
                            if self.is_high_quality_key(key):
                                all_keys.append({
                                    'private_key': key,
                                    'source': source_file,
                                    'entropy': self.calculate_entropy(key)
                                })
                    
                    elif source_file.endswith('.txt'):
                        with open(source_file, 'r') as f:
                            for line in f:
                                key = line.strip()
                                if self.is_high_quality_key(key):
                                    all_keys.append({
                                        'private_key': key,
                                        'source': source_file,
                                        'entropy': self.calculate_entropy(key)
                                    })
                    
                    print(f"✅ Loaded high-quality keys from {source_file}")
                    
                except Exception as e:
                    print(f"⚠️ Error loading {source_file}: {e}")
        
        # Sort by entropy (highest quality first)
        all_keys.sort(key=lambda x: x['entropy'], reverse=True)
        
        print(f"🎯 TOTAL HIGH-QUALITY KEYS LOADED: {len(all_keys)}")
        return all_keys
    
    def hunt_jackpots(self, max_keys=500):
        """Hunt for jackpots with maximum precision"""
        print("🚀 ULTIMATE JACKPOT HUNT INITIATED")
        print("=" * 60)
        print(f"🎯 Target: {max_keys} highest-quality keys")
        print(f"⚡ Mode: ULTRA PRECISION")
        print()
        
        # Load all high-quality keys
        all_keys = self.load_all_private_keys()
        
        if not all_keys:
            print("❌ No high-quality keys found!")
            return
        
        # Hunt the best keys
        keys_to_check = all_keys[:max_keys]
        
        print(f"🔍 HUNTING {len(keys_to_check)} PREMIUM KEYS...")
        print()
        
        for i, key_data in enumerate(keys_to_check):
            private_key = key_data['private_key']
            source = key_data['source']
            entropy = key_data['entropy']
            
            print(f"🎯 [{i+1}/{len(keys_to_check)}] {private_key[:12]}... (entropy: {entropy:.2f})")
            
            # Derive addresses
            eth_addr, btc_addr = self.derive_addresses_precise(private_key)
            
            if not eth_addr or not btc_addr:
                print("    ❌ Address derivation failed")
                continue
            
            print(f"    📍 ETH: {eth_addr}")
            print(f"    📍 BTC: {btc_addr}")
            
            # Check balances with maximum precision
            eth_balance = self.check_ethereum_balance_ultra(eth_addr)
            btc_balance = self.check_bitcoin_balance_ultra(btc_addr)
            
            self.checked_count += 1
            
            # JACKPOT DETECTION
            if eth_balance > 0 or btc_balance > 0:
                jackpot = {
                    'private_key': private_key,
                    'source': source,
                    'eth_address': eth_addr,
                    'btc_address': btc_addr,
                    'eth_balance': eth_balance,
                    'btc_balance': btc_balance,
                    'entropy_score': entropy,
                    'timestamp': datetime.now().isoformat()
                }
                
                self.found_jackpots.append(jackpot)
                
                print(f"    🎉 **JACKPOT FOUND!**")
                print(f"    💰 ETH: {eth_balance} wei ({eth_balance/1e18:.10f} ETH)")
                print(f"    💰 BTC: {btc_balance} sat ({btc_balance/1e8:.8f} BTC)")
                print(f"    🔥 ENTROPY: {entropy:.3f}")
                
                # Save immediately
                self.save_jackpot(jackpot)
                
            else:
                print("    ✓ Empty")
            
            # Progress updates
            if (i + 1) % 25 == 0:
                elapsed = time.time() - self.start_time
                rate = self.checked_count / elapsed
                
                print(f"\n📊 PROGRESS: {i+1}/{len(keys_to_check)} ({100*(i+1)/len(keys_to_check):.1f}%)")
                print(f"    ⚡ Rate: {rate:.1f} keys/sec")
                print(f"    🎉 Jackpots: {len(self.found_jackpots)}")
                print(f"    ⏱️ Elapsed: {elapsed/60:.1f} min")
                print()
        
        # Final summary
        self.print_final_summary()
    
    def save_jackpot(self, jackpot):
        """Save jackpot immediately"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ULTIMATE_JACKPOT_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(jackpot, f, indent=2)
        
        print(f"    💾 Jackpot saved to {filename}")
    
    def print_final_summary(self):
        """Print comprehensive hunt summary"""
        total_time = time.time() - self.start_time
        
        print("\n" + "=" * 60)
        print("🏆 ULTIMATE JACKPOT HUNT COMPLETE")
        print("=" * 60)
        print(f"⏱️  Total Time: {total_time/60:.1f} minutes")
        print(f"🔍 Keys Checked: {self.checked_count}")
        print(f"⚡ Average Rate: {self.checked_count/total_time:.1f} keys/sec")
        print(f"🎉 JACKPOTS FOUND: {len(self.found_jackpots)}")
        print()
        
        if self.found_jackpots:
            print("💰 JACKPOT SUMMARY:")
            total_eth_wei = 0
            total_btc_sat = 0
            
            for i, jackpot in enumerate(self.found_jackpots):
                total_eth_wei += jackpot['eth_balance']
                total_btc_sat += jackpot['btc_balance']
                
                print(f"   🏆 Jackpot {i+1}:")
                print(f"      🔑 Key: {jackpot['private_key'][:12]}...")
                print(f"      💰 ETH: {jackpot['eth_balance']} wei ({jackpot['eth_balance']/1e18:.10f} ETH)")
                print(f"      💰 BTC: {jackpot['btc_balance']} sat ({jackpot['btc_balance']/1e8:.8f} BTC)")
                print(f"      📍 ETH Addr: {jackpot['eth_address']}")
                print(f"      📍 BTC Addr: {jackpot['btc_address']}")
                print()
            
            print(f"💎 TOTAL VALUE FOUND:")
            print(f"   ETH: {total_eth_wei} wei ({total_eth_wei/1e18:.10f} ETH)")
            print(f"   BTC: {total_btc_sat} sat ({total_btc_sat/1e8:.8f} BTC)")
        else:
            print("💡 No jackpots found in this batch")
            print("   🎯 Consider expanding search or trying different datasets")
        
        print("=" * 60)

def main():
    """Execute the ultimate hunt"""
    hunter = UltimateJackpotHunter()
    hunter.hunt_jackpots(max_keys=500)  # Hunt top 500 highest-entropy keys

if __name__ == "__main__":
    main()
