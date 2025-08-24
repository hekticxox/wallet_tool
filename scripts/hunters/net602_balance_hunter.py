#!/usr/bin/env python3
"""
🎯 NET602 BALANCE HUNTER
========================
Check extracted private keys from net602 for funded wallets
"""

import json
import time
import requests
from datetime import datetime
from eth_keys import keys
from bit import Key
import sys
import os

class Net602BalanceHunter:
    def __init__(self):
        self.found_jackpots = []
        self.checked_count = 0
        
    def generate_addresses(self, private_key_hex):
        """Generate ETH and BTC addresses from private key"""
        try:
            # ETH address
            private_key_bytes = bytes.fromhex(private_key_hex)
            private_key = keys.PrivateKey(private_key_bytes)
            eth_address = private_key.public_key.to_checksum_address()
            
            # BTC address
            btc_key = Key.from_hex(private_key_hex)
            btc_address = btc_key.address
            
            return eth_address, btc_address
        except Exception as e:
            print(f"❌ Address generation error: {e}")
            return None, None
    
    def check_eth_balance(self, address):
        """Check Ethereum balance using free API"""
        try:
            url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey=YourApiKeyToken"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == '1':
                    return int(data.get('result', 0))
        except:
            pass
        return 0
    
    def check_btc_balance(self, address):
        """Check Bitcoin balance using free API"""
        try:
            url = f"https://blockstream.info/api/address/{address}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                funded = data.get('chain_stats', {}).get('funded_txo_sum', 0)
                spent = data.get('chain_stats', {}).get('spent_txo_sum', 0)
                return max(0, funded - spent)
        except:
            pass
        return 0
    
    def hunt_sample(self, keys_file, sample_size=1000):
        """Hunt through a sample of extracted keys"""
        print("🎯 NET602 BALANCE HUNTER")
        print("=" * 50)
        
        # Load extracted keys
        try:
            with open(keys_file, 'r') as f:
                data = json.load(f)
            private_keys = data['private_keys']
        except Exception as e:
            print(f"❌ Error loading keys: {e}")
            return
        
        total_keys = len(private_keys)
        print(f"📊 Total keys available: {total_keys}")
        
        # Take a sample for checking
        sample_keys = private_keys[:sample_size]
        print(f"🎯 Checking sample: {len(sample_keys)} keys")
        print()
        
        start_time = time.time()
        
        for i, key_data in enumerate(sample_keys, 1):
            private_key_hex = key_data['private_key']
            source_file = key_data.get('source_file', 'Unknown')
            
            print(f"🔍 [{i}/{len(sample_keys)}] {private_key_hex[:12]}...")
            
            # Generate addresses
            eth_address, btc_address = self.generate_addresses(private_key_hex)
            if not eth_address or not btc_address:
                print("    ❌ Address generation failed")
                continue
                
            print(f"    📍 ETH: {eth_address}")
            print(f"    📍 BTC: {btc_address}")
            
            # Check balances
            eth_balance = self.check_eth_balance(eth_address)
            btc_balance = self.check_btc_balance(btc_address)
            
            self.checked_count += 1
            
            if eth_balance > 0 or btc_balance > 0:
                print(f"    🎉 JACKPOT FOUND!")
                print(f"    💰 ETH: {eth_balance} wei")
                print(f"    ₿  BTC: {btc_balance} satoshis")
                
                jackpot_data = {
                    'private_key': private_key_hex,
                    'eth_address': eth_address,
                    'btc_address': btc_address,
                    'eth_balance': eth_balance,
                    'btc_balance': btc_balance,
                    'source_file': source_file,
                    'discovered': datetime.now().isoformat()
                }
                self.found_jackpots.append(jackpot_data)
                
                # Save immediately
                jackpot_file = f'NET602_JACKPOT_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                with open(jackpot_file, 'w') as f:
                    json.dump(jackpot_data, f, indent=2)
                print(f"    💾 Saved to: {jackpot_file}")
            else:
                print("    ✓ Empty")
            
            # Progress update
            if i % 50 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                print()
                print(f"📊 PROGRESS: {i}/{len(sample_keys)} ({i/len(sample_keys)*100:.1f}%)")
                print(f"    ⚡ Rate: {rate:.1f} keys/sec")
                print(f"    🎉 Jackpots: {len(self.found_jackpots)}")
                print(f"    ⏱️ Elapsed: {elapsed/60:.1f} min")
                print()
            
            time.sleep(0.3)  # Rate limiting
        
        # Final report
        elapsed = time.time() - start_time
        print()
        print("=" * 50)
        print("🏆 NET602 HUNT COMPLETE")
        print("=" * 50)
        print(f"⏱️  Total Time: {elapsed/60:.1f} minutes")
        print(f"🔍 Keys Checked: {self.checked_count}")
        print(f"⚡ Average Rate: {self.checked_count/elapsed:.1f} keys/sec")
        print(f"🎉 JACKPOTS FOUND: {len(self.found_jackpots)}")
        print("=" * 50)
        
        if self.found_jackpots:
            summary_file = f'NET602_HUNT_SUMMARY_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(summary_file, 'w') as f:
                json.dump({
                    'hunt_summary': {
                        'keys_checked': self.checked_count,
                        'jackpots_found': len(self.found_jackpots),
                        'success_rate': len(self.found_jackpots) / self.checked_count * 100,
                        'hunt_date': datetime.now().isoformat()
                    },
                    'jackpots': self.found_jackpots
                }, f, indent=2)
            print(f"📄 Hunt summary saved to: {summary_file}")

def main():
    """Hunt NET602 extracted keys for funded wallets"""
    keys_file = "NET602_EXTRACTED_KEYS_20250813_130504.json"
    
    if not os.path.exists(keys_file):
        print(f"❌ Keys file not found: {keys_file}")
        return
    
    hunter = Net602BalanceHunter()
    hunter.hunt_sample(keys_file, sample_size=2000)  # Check first 2000 keys

if __name__ == "__main__":
    main()
