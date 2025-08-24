#!/usr/bin/env python3
"""
🎯 SMART TARGET HUNTER
=====================
Hunt the 40 smartest targets from pattern analysis
"""

import json
import requests
import time
from datetime import datetime
from eth_keys import keys
from bit import Key

class SmartTargetHunter:
    def __init__(self):
        self.results = []
        
    def get_eth_balance(self, address):
        """Get Ethereum balance using free API"""
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
    
    def get_btc_balance(self, address):
        """Get Bitcoin balance using free API"""
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
    
    def hunt_targets(self, targets_file):
        """Hunt through smart targets"""
        print("🎯 SMART TARGET HUNTER")
        print("=" * 50)
        
        # Load targets
        try:
            with open(targets_file, 'r') as f:
                targets = json.load(f)
        except Exception as e:
            print(f"❌ Error loading targets: {e}")
            return
        
        print(f"📊 Loaded {len(targets)} smart targets...")
        print()
        
        jackpots = 0
        start_time = time.time()
        
        for i, target in enumerate(targets, 1):
            private_key_hex = target['private_key']
            score = target.get('combined_score', 0)
            
            print(f"🎯 [{i}/{len(targets)}] {private_key_hex[:12]}... (score: {score:.3f})")
            
            # Generate addresses
            eth_address, btc_address = self.generate_addresses(private_key_hex)
            if not eth_address or not btc_address:
                print("    ❌ Address generation failed")
                continue
                
            print(f"    📍 ETH: {eth_address}")
            print(f"    📍 BTC: {btc_address}")
            
            # Check balances
            eth_balance = self.get_eth_balance(eth_address)
            btc_balance = self.get_btc_balance(btc_address)
            
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
                    'score': score,
                    'discovered': datetime.now().isoformat()
                }
                self.results.append(jackpot_data)
                jackpots += 1
                
                # Save immediately
                with open(f'SMART_TARGET_JACKPOT_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
                    json.dump(jackpot_data, f, indent=2)
            else:
                print("    ✓ Empty")
            
            # Progress update
            if i % 10 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                print()
                print(f"📊 PROGRESS: {i}/{len(targets)} ({i/len(targets)*100:.1f}%)")
                print(f"    ⚡ Rate: {rate:.1f} targets/sec")
                print(f"    🎉 Jackpots: {jackpots}")
                print(f"    ⏱️ Elapsed: {elapsed/60:.1f} min")
                print()
            
            time.sleep(0.5)  # Rate limiting
        
        # Final report
        elapsed = time.time() - start_time
        print()
        print("=" * 50)
        print("🏆 SMART TARGET HUNT COMPLETE")
        print("=" * 50)
        print(f"⏱️  Total Time: {elapsed/60:.1f} minutes")
        print(f"🔍 Targets Checked: {len(targets)}")
        print(f"⚡ Average Rate: {len(targets)/elapsed:.1f} targets/sec")
        print(f"🎉 JACKPOTS FOUND: {jackpots}")
        print("=" * 50)
        
        if self.results:
            summary_file = f'SMART_TARGET_SUMMARY_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(summary_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"📄 Results saved to: {summary_file}")

if __name__ == "__main__":
    import sys
    targets_file = sys.argv[1] if len(sys.argv) > 1 else "SMART_HUNTING_TARGETS_20250813_124818.json"
    
    hunter = SmartTargetHunter()
    hunter.hunt_targets(targets_file)
