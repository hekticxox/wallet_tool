#!/usr/bin/env python3
"""
⚡ LIGHTNING PARALLEL JACKPOT HUNTER
===================================
10x SPEED - MULTIPLE THREADS - LASER PRECISION
"""

import json
import time
import requests
import threading
import queue
from datetime import datetime
from eth_keys import keys
from bit import Key
from api_manager import APIManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LightningParallelHunter:
    def __init__(self, num_threads=8):
        """Initialize lightning hunter with multiple threads"""
        self.num_threads = num_threads
        self.api_managers = [APIManager() for _ in range(num_threads)]
        self.work_queue = queue.Queue()
        self.results_queue = queue.Queue()
        self.jackpots = []
        self.checked_count = 0
        self.lock = threading.Lock()
        self.start_time = time.time()
        
    def calculate_entropy(self, hex_string):
        """Lightning-fast entropy calculation"""
        if not hex_string or len(hex_string) < 60:
            return 0
        
        clean = hex_string.replace('0x', '').lower()
        unique_chars = len(set(clean))
        
        # Quick quality checks
        if unique_chars < 10:
            return 0.1
        if any(clean[i:i+6] == clean[i+6:i+12] for i in range(0, len(clean)-12, 6)):
            return 0.2
        
        return min(unique_chars / 16.0, 1.0)
    
    def load_lightning_keys(self):
        """Load keys with lightning speed"""
        print("⚡ LOADING KEYS AT LIGHTNING SPEED...")
        
        all_keys = []
        
        # Target the most promising files first
        priority_files = [
            'net599_FUNDED_keys.txt',     # Already found 1 jackpot here!
            'net599_private_keys.txt',    # Massive dataset
            'net602_direct_keys.json',    # Direct extraction
            'net605_direct_keys.json',    # Large dataset
            'PRIORITY_CHECKING_LIST.json' # MetaMask priority
        ]
        
        for file_path in priority_files:
            try:
                if file_path.endswith('.txt'):
                    with open(file_path, 'r') as f:
                        for line in f:
                            key = line.strip()
                            entropy = self.calculate_entropy(key)
                            if entropy > 0.8:  # Only ultra-high quality
                                all_keys.append({
                                    'private_key': key,
                                    'source': file_path,
                                    'entropy': entropy
                                })
                
                elif file_path.endswith('.json'):
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    if isinstance(data, dict) and 'keys' in data:
                        keys_data = data['keys']
                    else:
                        keys_data = data if isinstance(data, list) else [data]
                    
                    for item in keys_data:
                        key = item.get('private_key', '') if isinstance(item, dict) else str(item)
                        entropy = self.calculate_entropy(key)
                        if entropy > 0.8:
                            all_keys.append({
                                'private_key': key,
                                'source': file_path,
                                'entropy': entropy
                            })
                
                print(f"⚡ Loaded ultra-quality keys from {file_path}")
                
            except Exception as e:
                print(f"⚠️ Skip {file_path}: {e}")
        
        # Sort by entropy (best first)
        all_keys.sort(key=lambda x: x['entropy'], reverse=True)
        
        print(f"🎯 LIGHTNING KEYS LOADED: {len(all_keys)} ultra-quality")
        return all_keys[:1000]  # Top 1000 only for speed
    
    def worker_thread(self, thread_id):
        """Lightning worker thread"""
        api_manager = self.api_managers[thread_id]
        
        while True:
            try:
                work = self.work_queue.get(timeout=2)
                if work is None:  # Shutdown signal
                    break
                
                key_data = work
                private_key = key_data['private_key']
                
                # Lightning address derivation
                try:
                    clean_key = private_key.replace('0x', '')
                    if len(clean_key) != 64:
                        self.work_queue.task_done()
                        continue
                    
                    # ETH address
                    private_key_bytes = bytes.fromhex(clean_key)
                    eth_key = keys.PrivateKey(private_key_bytes)
                    eth_addr = eth_key.public_key.to_checksum_address()
                    
                    # BTC address
                    btc_key = Key.from_hex(clean_key)
                    btc_addr = btc_key.address
                    
                except Exception as e:
                    self.work_queue.task_done()
                    continue
                
                # Lightning balance checks
                eth_balance = 0
                btc_balance = 0
                
                try:
                    # ETH via Etherscan
                    eth_apis = api_manager.get_ethereum_apis()
                    if eth_apis.get('etherscan'):
                        url = f"https://api.etherscan.io/api"
                        params = {
                            'module': 'account',
                            'action': 'balance', 
                            'address': eth_addr,
                            'tag': 'latest',
                            'apikey': eth_apis['etherscan']
                        }
                        
                        response = requests.get(url, params=params, timeout=8)
                        if response.status_code == 200:
                            data = response.json()
                            if data.get('status') == '1':
                                eth_balance = int(data.get('result', 0))
                except:
                    pass
                
                try:
                    # BTC via BlockStream
                    url = f"https://blockstream.info/api/address/{btc_addr}"
                    response = requests.get(url, timeout=8)
                    if response.status_code == 200:
                        data = response.json()
                        btc_balance = data.get('chain_stats', {}).get('funded_txo_sum', 0) - \
                                    data.get('chain_stats', {}).get('spent_txo_sum', 0)
                except:
                    pass
                
                # Result processing
                result = {
                    'key_data': key_data,
                    'eth_address': eth_addr,
                    'btc_address': btc_addr,
                    'eth_balance': eth_balance,
                    'btc_balance': btc_balance,
                    'thread_id': thread_id
                }
                
                self.results_queue.put(result)
                self.work_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker {thread_id} error: {e}")
                self.work_queue.task_done()
    
    def hunt_lightning(self):
        """Execute lightning hunt"""
        print("⚡ LIGHTNING PARALLEL HUNT INITIATED")
        print("=" * 60)
        print(f"🧵 Threads: {self.num_threads}")
        print(f"⚡ Expected Speed: 10x faster")
        print()
        
        # Load ultra-quality keys
        lightning_keys = self.load_lightning_keys()
        
        if not lightning_keys:
            print("❌ No lightning keys found!")
            return
        
        # Start worker threads
        threads = []
        for i in range(self.num_threads):
            thread = threading.Thread(target=self.worker_thread, args=(i,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Add work to queue
        for key_data in lightning_keys:
            self.work_queue.put(key_data)
        
        total_keys = len(lightning_keys)
        
        print(f"🎯 HUNTING {total_keys} ULTRA-QUALITY KEYS...")
        print()
        
        # Process results in real-time
        while self.checked_count < total_keys:
            try:
                result = self.results_queue.get(timeout=1)
                self.checked_count += 1
                
                key_data = result['key_data']
                eth_balance = result['eth_balance']
                btc_balance = result['btc_balance']
                
                # Display key being checked
                key_display = f"{key_data['private_key'][:12]}..."
                entropy = key_data['entropy']
                
                print(f"⚡ [{self.checked_count}/{total_keys}] {key_display} (ent:{entropy:.2f})")
                print(f"    📍 ETH: {result['eth_address']}")
                print(f"    📍 BTC: {result['btc_address']}")
                
                # JACKPOT CHECK
                if eth_balance > 0 or btc_balance > 0:
                    jackpot = {
                        'private_key': key_data['private_key'],
                        'source': key_data['source'],
                        'eth_address': result['eth_address'],
                        'btc_address': result['btc_address'],
                        'eth_balance': eth_balance,
                        'btc_balance': btc_balance,
                        'entropy_score': entropy,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    with self.lock:
                        self.jackpots.append(jackpot)
                    
                    print(f"    🎉 **LIGHTNING JACKPOT FOUND!**")
                    print(f"    💰 ETH: {eth_balance} wei ({eth_balance/1e18:.10f} ETH)")
                    print(f"    💰 BTC: {btc_balance} sat ({btc_balance/1e8:.8f} BTC)")
                    
                    # Save immediately
                    self.save_lightning_jackpot(jackpot)
                    
                else:
                    print("    ✓ Empty")
                
                # Lightning progress
                if self.checked_count % 50 == 0:
                    elapsed = time.time() - self.start_time
                    rate = self.checked_count / elapsed
                    
                    print(f"\n⚡ LIGHTNING PROGRESS: {self.checked_count}/{total_keys} ({100*self.checked_count/total_keys:.1f}%)")
                    print(f"    🚀 Rate: {rate:.1f} keys/sec")
                    print(f"    🎉 Jackpots: {len(self.jackpots)}")
                    print(f"    ⏱️ Elapsed: {elapsed/60:.1f} min")
                    print()
                
            except queue.Empty:
                continue
        
        # Shutdown threads
        for _ in range(self.num_threads):
            self.work_queue.put(None)
        
        for thread in threads:
            thread.join(timeout=1)
        
        # Final summary
        self.print_lightning_summary()
    
    def save_lightning_jackpot(self, jackpot):
        """Save lightning jackpot"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"LIGHTNING_JACKPOT_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(jackpot, f, indent=2)
        
        print(f"    ⚡ Lightning jackpot saved to {filename}")
    
    def print_lightning_summary(self):
        """Print lightning summary"""
        total_time = time.time() - self.start_time
        
        print("\n" + "=" * 60)
        print("⚡ LIGHTNING HUNT COMPLETE")
        print("=" * 60)
        print(f"⏱️  Total Time: {total_time/60:.1f} minutes")
        print(f"🔍 Keys Checked: {self.checked_count}")
        print(f"🚀 Lightning Rate: {self.checked_count/total_time:.1f} keys/sec")
        print(f"⚡ JACKPOTS FOUND: {len(self.jackpots)}")
        
        if self.jackpots:
            print(f"\n⚡ LIGHTNING JACKPOTS:")
            for i, jackpot in enumerate(self.jackpots):
                print(f"   🏆 Lightning Jackpot {i+1}:")
                print(f"      🔑 Key: {jackpot['private_key'][:12]}...")
                print(f"      💰 ETH: {jackpot['eth_balance']} wei")
                print(f"      💰 BTC: {jackpot['btc_balance']} sat")
                print(f"      📊 Entropy: {jackpot['entropy_score']:.3f}")
        
        print("=" * 60)

def main():
    """Execute lightning hunt"""
    hunter = LightningParallelHunter(num_threads=8)
    hunter.hunt_lightning()

if __name__ == "__main__":
    main()
