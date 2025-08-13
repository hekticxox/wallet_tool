#!/usr/bin/env python3
"""
MetaMask Priority Key Checker - Batch 2 (Keys 101-200)
Continues checking from where batch 1 left off
"""

import json
import time
from datetime import datetime
from api_manager import APIManager
from eth_keys import keys
from bit import Key
from web3 import Web3
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetaMaskBatch2Checker:
    def __init__(self):
        """Initialize the batch 2 checker"""
        self.api_manager = APIManager()
        self.checked_keys = []
        self.funded_wallets = []
        self.start_index = 100  # Start from key 101 (0-indexed = 100)
        self.end_index = 200    # End at key 200 (0-indexed = 199)
        
    def load_priority_keys(self):
        """Load priority keys from file"""
        try:
            with open('PRIORITY_CHECKING_LIST.json', 'r') as f:
                data = json.load(f)
            
            keys_list = data.get('keys', [])
            batch_keys = keys_list[self.start_index:self.end_index]
            
            logger.info(f"📋 Loaded {len(batch_keys)} keys for batch 2")
            logger.info(f"🎯 Processing keys {self.start_index + 1}-{min(self.end_index, len(keys_list))}")
            
            return batch_keys
            
        except Exception as e:
            logger.error(f"❌ Error loading priority keys: {e}")
            return []
    
    def derive_addresses(self, private_key_hex):
        """Derive ETH and BTC addresses from private key"""
        try:
            # Remove 0x prefix if present
            if private_key_hex.startswith('0x'):
                private_key_hex = private_key_hex[2:]
            
            # Ethereum address
            private_key_bytes = bytes.fromhex(private_key_hex)
            eth_key = keys.PrivateKey(private_key_bytes)
            eth_address = eth_key.public_key.to_checksum_address()
            
            # Bitcoin address
            btc_key = Key.from_hex(private_key_hex)
            btc_address = btc_key.address
            
            return eth_address, btc_address
            
        except Exception as e:
            logger.error(f"❌ Error deriving addresses: {e}")
            return None, None
    
    def check_ethereum_balance(self, address):
        """Check real Ethereum balance using our APIs"""
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
                
                import requests
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == '1':
                        balance_wei = int(data.get('result', 0))
                        return balance_wei
            
            return 0
            
        except Exception as e:
            logger.warning(f"⚠️ ETH balance check failed: {e}")
            return 0

    def check_bitcoin_balance(self, address):
        """Check real Bitcoin balance using our APIs"""
        try:
            # Try BlockStream API (no key required)
            import requests
            url = f"https://blockstream.info/api/address/{address}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                balance_sat = data.get('chain_stats', {}).get('funded_txo_sum', 0) - \
                            data.get('chain_stats', {}).get('spent_txo_sum', 0)
                return balance_sat
                
            return 0
            
        except Exception as e:
            logger.warning(f"⚠️ BTC balance check failed: {e}")
            return 0
    
    def check_balances(self, eth_address, btc_address):
        """Check balances for both addresses"""
        eth_balance = self.check_ethereum_balance(eth_address)
        btc_balance = self.check_bitcoin_balance(btc_address)
        
        return eth_balance, btc_balance
    
    def process_batch(self):
        """Process the batch of priority keys"""
        print("🔥 METAMASK PRIORITY KEY CHECKER - BATCH 2")
        print("=" * 60)
        
        # Load keys
        priority_keys = self.load_priority_keys()
        if not priority_keys:
            print("❌ No keys loaded for checking")
            return
        
        print(f"🎯 Checking keys {self.start_index + 1}-{self.start_index + len(priority_keys)}")
        print(f"⏱️  Estimated time: {len(priority_keys) * 0.3 / 60:.1f} minutes")
        print()
        
        start_time = time.time()
        
        for i, key_data in enumerate(priority_keys):
            key_index = self.start_index + i + 1
            private_key = key_data['private_key']
            source_file = key_data['source_file']
            
            # Show abbreviated key
            key_display = f"{private_key[:12]}..."
            
            print(f"🔍 [{key_index}/{self.start_index + len(priority_keys)}] {source_file}: {key_display}")
            
            # Derive addresses
            eth_address, btc_address = self.derive_addresses(private_key)
            
            if not eth_address or not btc_address:
                print("    ❌ Failed to derive addresses")
                continue
                
            print(f"    📍 ETH: {eth_address}")
            print(f"    📍 BTC: {btc_address}")
            
            # Check balances
            eth_balance, btc_balance = self.check_balances(eth_address, btc_address)
            
            # Record results
            result = {
                'index': key_index,
                'private_key': private_key,
                'source_file': source_file,
                'eth_address': eth_address,
                'btc_address': btc_address,
                'eth_balance': eth_balance,
                'btc_balance': btc_balance,
                'timestamp': datetime.now().isoformat()
            }
            
            self.checked_keys.append(result)
            
            # Check if funded
            if (eth_balance and eth_balance > 0) or (btc_balance and btc_balance > 0):
                print(f"    🎉 FUNDED WALLET FOUND!")
                print(f"    💰 ETH: {eth_balance} wei")
                print(f"    💰 BTC: {btc_balance} satoshi")
                self.funded_wallets.append(result)
            else:
                print("    ✓ Empty")
            
            # Progress update every 10 keys
            if (i + 1) % 10 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                funded_count = len(self.funded_wallets)
                
                print(f"\n📊 Progress: {i + 1}/{len(priority_keys)} ({100 * (i + 1) / len(priority_keys):.1f}%)")
                print(f"    Rate: {rate:.1f} keys/sec")
                print(f"    Funded: {funded_count} wallets")
                print()
        
        # Final summary
        total_time = time.time() - start_time
        print("=" * 60)
        print("🏁 BATCH 2 METAMASK CHECK COMPLETE")
        print(f"   ⏱️  Time: {total_time / 60:.1f} minutes")
        print(f"   🔍 Checked: {len(priority_keys)} keys")
        print(f"   💰 Funded: {len(self.funded_wallets)} wallets")
        print()
        
        if self.funded_wallets:
            print("🎉 FUNDED WALLETS DISCOVERED:")
            for wallet in self.funded_wallets:
                print(f"   🔑 Key {wallet['index']}: {wallet['private_key'][:12]}...")
                print(f"   💰 ETH: {wallet['eth_balance']} wei | BTC: {wallet['btc_balance']} sat")
                print(f"   📍 {wallet['eth_address']} | {wallet['btc_address']}")
                print()
        else:
            print("💡 No funded wallets in batch 2")
            print(f"   📊 {1000 - self.end_index} priority keys remaining")
            print("   🎯 Continue with next batch or expand search")
        
        # Save results
        self.save_results()
    
    def save_results(self):
        """Save batch results"""
        try:
            # Save all results
            results_file = f'METAMASK_BATCH2_RESULTS.json'
            with open(results_file, 'w') as f:
                json.dump({
                    'batch_info': {
                        'batch_number': 2,
                        'start_index': self.start_index,
                        'end_index': self.end_index,
                        'total_checked': len(self.checked_keys),
                        'funded_found': len(self.funded_wallets),
                        'timestamp': datetime.now().isoformat()
                    },
                    'checked_keys': self.checked_keys,
                    'funded_wallets': self.funded_wallets
                }, f, indent=2)
            
            logger.info(f"✅ Results saved to {results_file}")
            
            # Save funded wallets separately if any found
            if self.funded_wallets:
                funded_file = f'METAMASK_BATCH2_FUNDED.json'
                with open(funded_file, 'w') as f:
                    json.dump(self.funded_wallets, f, indent=2)
                logger.info(f"🎉 Funded wallets saved to {funded_file}")
                
        except Exception as e:
            logger.error(f"❌ Error saving results: {e}")

def main():
    """Main execution"""
    checker = MetaMaskBatch2Checker()
    checker.process_batch()

if __name__ == "__main__":
    main()
