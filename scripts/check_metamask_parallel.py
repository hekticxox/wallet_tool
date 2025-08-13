#!/usr/bin/env python3
"""
Parallel MetaMask Key Checker
Process multiple keys simultaneously for 4x speed improvement
"""

import json
import time
import threading
import queue
from datetime import datetime
from api_manager import APIManager
from eth_keys import keys
from bit import Key
from web3 import Web3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ParallelMetaMaskChecker:
    def __init__(self, num_threads=4):
        """Initialize parallel checker"""
        self.num_threads = num_threads
        self.api_managers = [APIManager() for _ in range(num_threads)]
        self.input_queue = queue.Queue()
        self.results_queue = queue.Queue()
        self.checked_keys = []
        self.funded_wallets = []
        self.processed_count = 0
        self.lock = threading.Lock()
        
    def derive_addresses(self, private_key_hex):
        """Derive ETH and BTC addresses from private key"""
        try:
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
    
    def check_balances(self, eth_address, btc_address, api_manager):
        """Check balances using specified API manager"""
        eth_balance = None
        btc_balance = None
        
        try:
            eth_response = api_manager.get_balance(eth_address, 'ethereum')
            if eth_response and 'balance' in eth_response:
                eth_balance = int(eth_response['balance'])
        except Exception as e:
            logger.warning(f"⚠️ ETH balance check failed: {e}")
        
        try:
            btc_response = api_manager.get_balance(btc_address, 'bitcoin')
            if btc_response and 'balance' in btc_response:
                btc_balance = int(btc_response['balance'])
        except Exception as e:
            logger.warning(f"⚠️ BTC balance check failed: {e}")
        
        return eth_balance, btc_balance
    
    def worker_thread(self, thread_id):
        """Worker thread for processing keys"""
        api_manager = self.api_managers[thread_id]
        
        while True:
            try:
                # Get work from queue (timeout to allow clean shutdown)
                work_item = self.input_queue.get(timeout=1)
                if work_item is None:  # Shutdown signal
                    break
                    
                key_data = work_item
                private_key = key_data['private_key']
                
                # Derive addresses
                eth_address, btc_address = self.derive_addresses(private_key)
                
                if not eth_address or not btc_address:
                    self.results_queue.put({
                        'success': False,
                        'error': 'Address derivation failed',
                        'key_data': key_data
                    })
                    continue
                
                # Check balances
                eth_balance, btc_balance = self.check_balances(
                    eth_address, btc_address, api_manager
                )
                
                # Prepare result
                result = {
                    'success': True,
                    'key_data': key_data,
                    'eth_address': eth_address,
                    'btc_address': btc_address,
                    'eth_balance': eth_balance,
                    'btc_balance': btc_balance,
                    'thread_id': thread_id,
                    'timestamp': datetime.now().isoformat()
                }
                
                self.results_queue.put(result)
                self.input_queue.task_done()
                
            except queue.Empty:
                continue  # Check for more work
            except Exception as e:
                logger.error(f"Worker {thread_id} error: {e}")
                self.input_queue.task_done()
    
    def load_priority_keys(self, start_index=0, count=400):
        """Load priority keys for parallel processing"""
        try:
            with open('PRIORITY_CHECKING_LIST.json', 'r') as f:
                data = json.load(f)
            
            keys_list = data.get('keys', [])
            batch_keys = keys_list[start_index:start_index + count]
            
            logger.info(f"📋 Loaded {len(batch_keys)} keys for parallel processing")
            return batch_keys
            
        except Exception as e:
            logger.error(f"❌ Error loading priority keys: {e}")
            return []
    
    def process_parallel(self, start_index=200, count=400):
        """Process keys in parallel"""
        print("🚀 PARALLEL METAMASK KEY CHECKER")
        print("=" * 60)
        print(f"🧵 Threads: {self.num_threads}")
        print(f"🎯 Processing keys {start_index + 1}-{start_index + count}")
        print(f"⚡ Expected 4x speed improvement")
        print()
        
        # Load keys
        priority_keys = self.load_priority_keys(start_index, count)
        if not priority_keys:
            print("❌ No keys loaded for checking")
            return
        
        # Start worker threads
        threads = []
        for i in range(self.num_threads):
            thread = threading.Thread(target=self.worker_thread, args=(i,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Add work to queue
        for key_data in priority_keys:
            self.input_queue.put(key_data)
        
        start_time = time.time()
        total_keys = len(priority_keys)
        
        # Process results
        while self.processed_count < total_keys:
            try:
                result = self.results_queue.get(timeout=1)
                self.processed_count += 1
                
                with self.lock:
                    if result['success']:
                        key_data = result['key_data']
                        
                        # Display result
                        key_display = f"{key_data['private_key'][:12]}..."
                        index = start_index + self.processed_count
                        
                        print(f"🔍 [{index}/{start_index + total_keys}] {key_data['source_file']}: {key_display}")
                        print(f"    📍 ETH: {result['eth_address']}")
                        print(f"    📍 BTC: {result['btc_address']}")
                        
                        # Check if funded
                        eth_bal = result['eth_balance']
                        btc_bal = result['btc_balance']
                        
                        if (eth_bal and eth_bal > 0) or (btc_bal and btc_bal > 0):
                            print(f"    🎉 FUNDED WALLET FOUND!")
                            print(f"    💰 ETH: {eth_bal} wei | BTC: {btc_bal} sat")
                            self.funded_wallets.append(result)
                        else:
                            print("    ✓ Empty")
                        
                        self.checked_keys.append(result)
                    else:
                        print(f"    ❌ {result['error']}")
                
                # Progress updates
                if self.processed_count % 20 == 0:
                    elapsed = time.time() - start_time
                    rate = self.processed_count / elapsed
                    funded_count = len(self.funded_wallets)
                    
                    print(f"\n📊 Progress: {self.processed_count}/{total_keys} ({100 * self.processed_count / total_keys:.1f}%)")
                    print(f"    ⚡ Rate: {rate:.1f} keys/sec (vs 0.3 sequential)")
                    print(f"    💰 Funded: {funded_count} wallets")
                    print()
                
            except queue.Empty:
                continue
        
        # Shutdown threads
        for _ in range(self.num_threads):
            self.input_queue.put(None)
        
        for thread in threads:
            thread.join(timeout=1)
        
        # Final summary
        total_time = time.time() - start_time
        avg_rate = total_keys / total_time
        
        print("=" * 60)
        print("🏁 PARALLEL METAMASK CHECK COMPLETE")
        print(f"   ⏱️  Time: {total_time / 60:.1f} minutes")
        print(f"   🔍 Checked: {total_keys} keys")
        print(f"   ⚡ Rate: {avg_rate:.1f} keys/sec")
        print(f"   🚀 Speedup: {avg_rate / 0.3:.1f}x vs sequential")
        print(f"   💰 Funded: {len(self.funded_wallets)} wallets")
        print()
        
        if self.funded_wallets:
            print("🎉 FUNDED WALLETS DISCOVERED:")
            for i, wallet in enumerate(self.funded_wallets):
                key_data = wallet['key_data']
                print(f"   🔑 Wallet {i + 1}: {key_data['private_key'][:12]}...")
                print(f"   💰 ETH: {wallet['eth_balance']} wei | BTC: {wallet['btc_balance']} sat")
                print(f"   📍 {wallet['eth_address']} | {wallet['btc_address']}")
                print()
        
        # Save results
        self.save_results(start_index, count)
    
    def save_results(self, start_index, count):
        """Save parallel processing results"""
        try:
            results_file = f'METAMASK_PARALLEL_RESULTS_{start_index}_{start_index + count}.json'
            with open(results_file, 'w') as f:
                json.dump({
                    'processing_info': {
                        'method': 'parallel',
                        'threads': self.num_threads,
                        'start_index': start_index,
                        'count': count,
                        'total_checked': len(self.checked_keys),
                        'funded_found': len(self.funded_wallets),
                        'timestamp': datetime.now().isoformat()
                    },
                    'checked_keys': self.checked_keys,
                    'funded_wallets': self.funded_wallets
                }, f, indent=2)
            
            logger.info(f"✅ Results saved to {results_file}")
            
        except Exception as e:
            logger.error(f"❌ Error saving results: {e}")

def main():
    """Main execution"""
    checker = ParallelMetaMaskChecker(num_threads=4)
    
    # Process keys 201-600 in parallel
    checker.process_parallel(start_index=200, count=400)

if __name__ == "__main__":
    main()
