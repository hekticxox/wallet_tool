#!/usr/bin/env python3
"""
⚡ PARALLEL LASER PRECISION HUNTER
==================================
Multi-threaded precision wallet hunting with 4x speed and surgical accuracy
"""

import json
import time
import requests
import threading
import queue
from datetime import datetime
from collections import defaultdict
from eth_keys import keys
from bit import Key
import sys
import os

# Add the current directory to Python path to import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api_manager import APIManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ParallelLaserHunter:
    def __init__(self, num_threads=4):
        """Initialize parallel laser precision hunter"""
        self.num_threads = num_threads
        self.api_managers = [APIManager() for _ in range(num_threads)]
        self.input_queue = queue.Queue()
        self.results_queue = queue.Queue()
        self.funded_wallets = []
        self.processed_count = 0
        self.lock = threading.Lock()
        
    def parallel_precision_hunt(self, start_index=200, count=200):
        """Execute parallel precision hunt with laser accuracy"""
        print("⚡ PARALLEL LASER PRECISION HUNTER")
        print("=" * 60)
        print(f"🧵 Threads: {self.num_threads}")
        print(f"🎯 Target: Keys {start_index + 1}-{start_index + count}")
        print(f"⚡ Expected 4x speed with surgical precision")
        print()
        
        # Load and prioritize keys
        with open('PRIORITY_CHECKING_LIST.json', 'r') as f:
            data = json.load(f)
        
        keys_list = data.get('keys', [])
        batch_keys = keys_list[start_index:start_index + count]
        
        if not batch_keys:
            print("❌ No keys available for hunting")
            return []
        
        # Apply entropy analysis for precision
        prioritized_keys = self._prioritize_by_entropy(batch_keys)
        
        print(f"📊 Entropy Analysis Applied:")
        high_entropy = sum(1 for k in prioritized_keys if self._calculate_entropy_score(k['private_key']) >= 0.8)
        print(f"   🔥 High entropy targets: {high_entropy}")
        print(f"   🎯 Total precision targets: {len(prioritized_keys)}")
        print()
        
        # Start worker threads
        threads = []
        for i in range(self.num_threads):
            thread = threading.Thread(target=self._precision_worker, args=(i,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Queue work
        for i, key_data in enumerate(prioritized_keys):
            key_data['batch_index'] = start_index + i + 1
            self.input_queue.put(key_data)
        
        start_time = time.time()
        total_keys = len(prioritized_keys)
        
        # Process results with real-time monitoring
        while self.processed_count < total_keys:
            try:
                result = self.results_queue.get(timeout=1)
                self.processed_count += 1
                
                with self.lock:
                    self._process_result(result, start_index)
                    
                    # Progress updates every 20 keys
                    if self.processed_count % 20 == 0:
                        self._show_precision_progress(start_time, total_keys)
                
            except queue.Empty:
                continue
        
        # Shutdown threads
        for _ in range(self.num_threads):
            self.input_queue.put(None)
        
        for thread in threads:
            thread.join(timeout=1)
        
        # Final results
        total_time = time.time() - start_time
        self._show_final_results(total_time, total_keys)
        
        return self.funded_wallets
    
    def _precision_worker(self, thread_id):
        """Worker thread for precision hunting"""
        api_manager = self.api_managers[thread_id]
        
        while True:
            try:
                work_item = self.input_queue.get(timeout=1)
                if work_item is None:  # Shutdown signal
                    break
                
                result = self._hunt_single_key(work_item, api_manager, thread_id)
                self.results_queue.put(result)
                self.input_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker {thread_id} error: {e}")
                self.input_queue.task_done()
    
    def _hunt_single_key(self, key_data, api_manager, thread_id):
        """Hunt a single key with maximum precision"""
        private_key = key_data['private_key']
        
        try:
            # Precision address derivation
            eth_address, btc_address = self._derive_addresses_precise(private_key)
            
            if not eth_address or not btc_address:
                return {
                    'success': False,
                    'error': 'Address derivation failed',
                    'key_data': key_data,
                    'thread_id': thread_id
                }
            
            # Multi-API precision balance check
            eth_balance = self._precision_eth_balance(eth_address, api_manager)
            btc_balance = self._precision_btc_balance(btc_address, api_manager)
            
            return {
                'success': True,
                'key_data': key_data,
                'eth_address': eth_address,
                'btc_address': btc_address,
                'eth_balance': eth_balance,
                'btc_balance': btc_balance,
                'entropy_score': self._calculate_entropy_score(private_key),
                'thread_id': thread_id,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'key_data': key_data,
                'thread_id': thread_id
            }
    
    def _process_result(self, result, base_index):
        """Process a hunting result with precision analysis"""
        if not result['success']:
            key_data = result['key_data']
            index = key_data.get('batch_index', 0)
            print(f"🔍 [{index}] ❌ {result['error']}")
            return
        
        key_data = result['key_data']
        index = key_data.get('batch_index', 0)
        private_key = key_data['private_key']
        source_file = key_data['source_file']
        
        print(f"🎯 [{index}] {source_file}: {private_key[:12]}... [T{result['thread_id']}]")
        print(f"    📍 ETH: {result['eth_address']}")
        print(f"    📍 BTC: {result['btc_address']}")
        
        # Check for funding
        eth_bal = result['eth_balance']
        btc_bal = result['btc_balance']
        
        if (eth_bal and eth_bal > 0) or (btc_bal and btc_bal > 0):
            print(f"    🎉 JACKPOT! LASER PRECISION SUCCESSFUL!")
            print(f"    💰 ETH: {eth_bal} wei ({eth_bal/10**18:.10f} ETH)")
            print(f"    💰 BTC: {btc_bal} sat ({btc_bal/100000000:.8f} BTC)")
            print(f"    🎲 Entropy: {result['entropy_score']:.3f}")
            
            self.funded_wallets.append(result)
            self._save_precision_find(result)
        else:
            entropy_indicator = "🔥" if result['entropy_score'] >= 0.8 else "🎯" if result['entropy_score'] >= 0.6 else "⚡"
            print(f"    ✓ Empty {entropy_indicator}")
    
    def _show_precision_progress(self, start_time, total_keys):
        """Show precision hunting progress"""
        elapsed = time.time() - start_time
        rate = self.processed_count / elapsed
        eta = (total_keys - self.processed_count) / rate if rate > 0 else 0
        
        print(f"\n📊 PRECISION HUNTING PROGRESS:")
        print(f"    ⚡ Rate: {rate:.1f} keys/sec ({rate*3600:.0f}/hour)")
        print(f"    🎯 Progress: {self.processed_count}/{total_keys} ({100*self.processed_count/total_keys:.1f}%)")
        print(f"    💰 Precision finds: {len(self.funded_wallets)}")
        print(f"    ⏱️  ETA: {eta/60:.1f} minutes")
        print()
    
    def _show_final_results(self, total_time, total_keys):
        """Show final precision hunting results"""
        avg_rate = total_keys / total_time
        
        print("=" * 60)
        print("🏁 PARALLEL LASER PRECISION HUNT COMPLETE")
        print(f"   ⏱️  Time: {total_time/60:.1f} minutes")
        print(f"   🎯 Keys hunted: {total_keys}")
        print(f"   ⚡ Average rate: {avg_rate:.1f} keys/sec")
        print(f"   🚀 Parallel speedup: {avg_rate/0.3:.1f}x vs sequential")
        print(f"   💰 Precision finds: {len(self.funded_wallets)} wallets")
        print(f"   🎲 Success rate: {len(self.funded_wallets)/total_keys*100:.4f}%")
        print()
        
        if self.funded_wallets:
            print("🎉 LASER PRECISION SUCCESSFUL - FUNDED WALLETS:")
            for i, wallet in enumerate(self.funded_wallets, 1):
                key_data = wallet['key_data']
                print(f"   🏆 Find #{i}: {key_data['private_key'][:16]}...")
                print(f"   💰 ETH: {wallet['eth_balance']} wei | BTC: {wallet['btc_balance']} sat")
                print(f"   🎲 Entropy: {wallet['entropy_score']:.3f}")
                print()
        else:
            print("💡 No funded wallets in this precision batch")
            print("   🎯 Laser precision analysis complete")
            print("   ⚡ Ready for next precision target batch")
    
    def _prioritize_by_entropy(self, keys_list):
        """Prioritize keys by entropy for laser precision"""
        high_entropy = []
        medium_entropy = []
        low_entropy = []
        
        for key_data in keys_list:
            entropy = self._calculate_entropy_score(key_data['private_key'])
            
            if entropy >= 0.8:
                high_entropy.append(key_data)
            elif entropy >= 0.6:
                medium_entropy.append(key_data)
            else:
                low_entropy.append(key_data)
        
        return high_entropy + medium_entropy + low_entropy
    
    def _calculate_entropy_score(self, hex_key):
        """Calculate entropy score for precision targeting"""
        if not hex_key:
            return 0
        
        if hex_key.startswith('0x'):
            hex_key = hex_key[2:]
        
        unique_chars = len(set(hex_key.lower()))
        max_unique = 16
        
        has_repeating = any(char * 4 in hex_key for char in '0123456789abcdef')
        has_sequential = any(seq in hex_key.lower() for seq in ['0123', '1234', '2345', '3456', '4567', '5678', '6789', '789a', '89ab', '9abc', 'abcd', 'bcde', 'cdef'])
        
        base_score = unique_chars / max_unique
        
        if has_repeating:
            base_score *= 0.7
        if has_sequential:
            base_score *= 0.8
        
        return base_score
    
    def _derive_addresses_precise(self, private_key_hex):
        """Precision address derivation with validation"""
        try:
            if private_key_hex.startswith('0x'):
                private_key_hex = private_key_hex[2:]
            
            if len(private_key_hex) != 64 or not all(c in '0123456789abcdefABCDEF' for c in private_key_hex):
                return None, None
            
            private_key_bytes = bytes.fromhex(private_key_hex)
            eth_key = keys.PrivateKey(private_key_bytes)
            eth_address = eth_key.public_key.to_checksum_address()
            
            btc_key = Key.from_hex(private_key_hex)
            btc_address = btc_key.address
            
            return eth_address, btc_address
            
        except Exception:
            return None, None
    
    def _precision_eth_balance(self, address, api_manager):
        """Precision Ethereum balance check"""
        try:
            eth_apis = api_manager.get_ethereum_apis()
            
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
    
    def _precision_btc_balance(self, address, api_manager):
        """Precision Bitcoin balance check"""
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
    
    def _save_precision_find(self, wallet_result):
        """Immediately save precision find"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"PARALLEL_PRECISION_FIND_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(wallet_result, f, indent=2)
        
        print(f"💾 PRECISION FIND SAVED: {filename}")

def main():
    """Execute parallel laser precision hunt"""
    hunter = ParallelLaserHunter(num_threads=4)
    
    print("⚡ INITIALIZING PARALLEL LASER PRECISION HUNT")
    print("=" * 60)
    print("🎯 Mission: Find funded wallets with surgical accuracy")
    print("⚡ Method: 4x parallel processing with entropy analysis")
    print("🔍 Target: MetaMask priority keys 201-400")
    print()
    
    # Execute precision hunt
    found_wallets = hunter.parallel_precision_hunt(start_index=200, count=200)
    
    if found_wallets:
        print(f"🎉 MISSION ACCOMPLISHED! {len(found_wallets)} funded wallets found!")
    else:
        print("🎯 Precision hunt complete - Ready for next batch")

if __name__ == "__main__":
    main()
