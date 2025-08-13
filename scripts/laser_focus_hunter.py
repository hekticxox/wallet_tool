#!/usr/bin/env python3
"""
🎯 LASER FOCUS JACKPOT HUNTER v4.0
=====================================

Final precision strike with simplified but ultra-effective targeting.
Uses proven patterns from our previous successful jackpot discovery.
"""

import json
import os
import sys
import math
from collections import Counter
from datetime import datetime
import requests
import time
import traceback

# Cryptography
from bit import Key as BitcoinKey
from eth_keys import keys

# Configuration
RESULTS_DIR = "laser_focus_results"
API_CONFIG_FILE = "api_config.json"
MAX_KEYS_TO_CHECK = 50  # Focus on quality, not quantity
FOCUS_DATASETS = ["net501", "net599", "net605"]  # Our richest sources

class LaserFocusHunter:
    def __init__(self):
        self.load_apis()
        self.setup_results_dir()
        self.jackpots_found = []
        
    def load_apis(self):
        """Load API configurations"""
        try:
            with open(API_CONFIG_FILE, 'r') as f:
                self.api_config = json.load(f)
            print("🔑 APIs loaded successfully")
        except Exception as e:
            print(f"⚠️  Warning: Could not load API config: {e}")
            self.api_config = {}

    def setup_results_dir(self):
        """Create results directory"""
        os.makedirs(RESULTS_DIR, exist_ok=True)
    
    def calculate_simple_entropy(self, hex_string):
        """Simple but effective entropy calculation"""
        try:
            # Count character frequency
            char_counts = Counter(hex_string.lower())
            total_chars = len(hex_string)
            
            # Calculate Shannon entropy
            entropy = 0
            for count in char_counts.values():
                probability = count / total_chars
                if probability > 0:
                    entropy -= probability * math.log2(probability)
            
            # Normalize to 0-1 range (max entropy for hex is 4 bits)
            normalized_entropy = entropy / 4.0
            
            return min(max(normalized_entropy, 0), 1)
            
        except Exception as e:
            print(f"⚠️  Entropy error: {e}")
            return 0.5
    
    def score_key_quality(self, key_hex):
        """Score key quality based on multiple factors"""
        score = 0
        
        # Basic entropy (40% of score)
        entropy = self.calculate_simple_entropy(key_hex)
        score += entropy * 0.4
        
        # Pattern analysis (30% of score)
        pattern_score = 0
        
        # Avoid too many repeated characters
        char_counts = Counter(key_hex.lower())
        max_char_freq = max(char_counts.values()) / len(key_hex)
        if max_char_freq < 0.2:  # Good distribution
            pattern_score += 0.3
        elif max_char_freq < 0.3:  # Acceptable
            pattern_score += 0.15
            
        # Avoid obvious patterns like 000, 111, aaa, etc.
        bad_patterns = ['000', '111', '222', '333', '444', '555', '666', '777', '888', '999', 'aaa', 'bbb', 'ccc', 'ddd', 'eee', 'fff']
        pattern_penalty = 0
        for pattern in bad_patterns:
            pattern_penalty += key_hex.lower().count(pattern) * 0.05
        
        pattern_score = max(0, pattern_score - pattern_penalty)
        score += pattern_score * 0.3
        
        # Mathematical properties (30% of score)
        try:
            key_int = int(key_hex, 16)
            math_score = 0
            
            # Not too small, not too large
            if 10**20 < key_int < 10**75:
                math_score += 0.2
            
            # Not a power of small numbers
            is_simple_power = False
            for base in [2, 3, 5, 7, 10]:
                for exp in range(2, 100):
                    if base ** exp == key_int:
                        is_simple_power = True
                        break
                if is_simple_power:
                    break
            
            if not is_simple_power:
                math_score += 0.1
            
            score += math_score * 0.3
            
        except:
            score += 0.1  # Default if calculation fails
        
        return min(max(score, 0), 1)
    
    def derive_addresses(self, private_key_hex):
        """Derive ETH and BTC addresses from private key"""
        try:
            # Ensure proper key format
            key_hex = private_key_hex.strip().lower()
            if len(key_hex) != 64:
                if len(key_hex) < 64:
                    key_hex = key_hex.zfill(64)
                else:
                    key_hex = key_hex[:64]
            
            # Derive Ethereum address
            private_key_bytes = bytes.fromhex(key_hex)
            eth_private_key = keys.PrivateKey(private_key_bytes)
            eth_address = eth_private_key.public_key.to_checksum_address()
            
            # Derive Bitcoin address
            btc_key = BitcoinKey.from_hex(key_hex)
            btc_address = btc_key.address
            
            return eth_address, btc_address, True
            
        except Exception as e:
            return None, None, False
    
    def check_balance_fast(self, eth_address, btc_address):
        """Fast balance checking with primary APIs only"""
        balances = {'eth': 0, 'btc': 0, 'has_balance': False}
        
        try:
            # Check Ethereum balance
            if 'etherscan' in self.api_config and self.api_config['etherscan'].get('api_key'):
                try:
                    eth_url = f"https://api.etherscan.io/api?module=account&action=balance&address={eth_address}&tag=latest&apikey={self.api_config['etherscan']['api_key']}"
                    response = requests.get(eth_url, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('status') == '1':
                            balances['eth'] = int(data['result'])
                except:
                    pass
            
            # Check Bitcoin balance
            if 'blockchair' in self.api_config and self.api_config['blockchair'].get('api_key'):
                try:
                    btc_url = f"https://api.blockchair.com/bitcoin/dashboards/address/{btc_address}?key={self.api_config['blockchair']['api_key']}"
                    response = requests.get(btc_url, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if 'data' in data and btc_address in data['data']:
                            balances['btc'] = data['data'][btc_address]['address']['balance']
                except:
                    pass
            
            balances['has_balance'] = (balances['eth'] > 0 or balances['btc'] > 0)
            time.sleep(0.1)  # Small delay
            
        except Exception as e:
            print(f"⚠️  Balance check error: {e}")
        
        return balances
    
    def load_highest_quality_keys(self):
        """Load and select the highest quality keys from our richest datasets"""
        print("🎯 Loading highest quality keys from proven successful sources...")
        
        all_keys = []
        
        # Load from specific high-value files
        high_value_files = [
            "net501_sample_keys.json",
            "net599_cache_keys.json", 
            "net605_metamask_keys.json",
            "richest_metamask_keys.json",
            "comprehensive_scan_results.json",
            "SMART_HUNTING_TARGETS_*.json"
        ]
        
        # Also check for any existing result files with keys
        import glob
        all_files = glob.glob("*keys*.json") + glob.glob("*results*.json") + glob.glob("*JACKPOT*.json")
        high_value_files.extend(all_files)
        
        unique_keys = set()
        
        for file_pattern in high_value_files:
            try:
                matching_files = glob.glob(file_pattern)
                for file_path in matching_files:
                    if os.path.exists(file_path):
                        print(f"📂 Loading: {file_path}")
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        
                        # Extract keys from various data structures
                        keys_found = 0
                        if isinstance(data, dict):
                            # Check various key fields
                            key_fields = ['private_keys', 'keys', 'high_quality_keys', 'jackpots', 'results', 'top_keys']
                            for field in key_fields:
                                if field in data:
                                    items = data[field]
                                    if isinstance(items, list):
                                        for item in items:
                                            key_val = None
                                            if isinstance(item, str) and len(item) == 64:
                                                key_val = item
                                            elif isinstance(item, dict):
                                                for key_name in ['private_key', 'key', 'hex', 'privateKey']:
                                                    if key_name in item and len(str(item[key_name])) == 64:
                                                        key_val = str(item[key_name])
                                                        break
                                            
                                            if key_val and len(key_val) == 64:
                                                unique_keys.add(key_val.lower())
                                                keys_found += 1
                        
                        elif isinstance(data, list):
                            for item in data:
                                if isinstance(item, str) and len(item) == 64:
                                    unique_keys.add(item.lower())
                                    keys_found += 1
                                elif isinstance(item, dict):
                                    for key_name in ['private_key', 'key', 'hex', 'privateKey']:
                                        if key_name in item and len(str(item[key_name])) == 64:
                                            unique_keys.add(str(item[key_name]).lower())
                                            keys_found += 1
                                            break
                        
                        print(f"   └─ Found {keys_found} keys")
                        
            except Exception as e:
                print(f"⚠️  Error loading {file_pattern}: {e}")
        
        print(f"🔍 Total unique keys collected: {len(unique_keys)}")
        
        # Score and rank all keys
        scored_keys = []
        for key_hex in unique_keys:
            if len(key_hex) == 64:
                try:
                    quality_score = self.score_key_quality(key_hex)
                    entropy_score = self.calculate_simple_entropy(key_hex)
                    
                    scored_keys.append({
                        'private_key': key_hex,
                        'quality_score': quality_score,
                        'entropy': entropy_score
                    })
                except:
                    continue
        
        # Sort by quality score
        scored_keys.sort(key=lambda x: x['quality_score'], reverse=True)
        
        # Take top keys
        top_keys = scored_keys[:MAX_KEYS_TO_CHECK]
        
        print(f"🏆 Selected {len(top_keys)} highest quality keys for laser focus hunting")
        if top_keys:
            print(f"📊 Top quality score: {top_keys[0]['quality_score']:.3f}")
            print(f"📊 Average quality score: {sum(k['quality_score'] for k in top_keys) / len(top_keys):.3f}")
        
        return top_keys
    
    def laser_focus_hunt(self):
        """Execute laser-focused jackpot hunting on highest quality keys"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(RESULTS_DIR, f"LASER_FOCUS_HUNT_{timestamp}.json")
        
        print(f"""
╔══════════════════════════════════════════════════════╗
║           🎯 LASER FOCUS JACKPOT HUNTER v4.0         ║
║              Maximum Precision Strike                ║
╚══════════════════════════════════════════════════════╝

🔥 Strategy: Quality over Quantity
🎯 Target Keys: {MAX_KEYS_TO_CHECK}
⚡ Fast Balance Checking: ENABLED
🧠 Quality Scoring: ACTIVE
        """)
        
        # Load highest quality keys
        top_keys = self.load_highest_quality_keys()
        
        if not top_keys:
            print("❌ No high-quality keys found for laser focus hunting")
            return
        
        print(f"🚀 Beginning laser-focused hunt on {len(top_keys)} premium keys...")
        
        results = {
            'timestamp': timestamp,
            'strategy': 'laser_focus_v4',
            'total_keys': len(top_keys),
            'keys_checked': 0,
            'jackpots_found': 0,
            'jackpots': [],
            'high_quality_empty': [],
            'errors': []
        }
        
        start_time = time.time()
        
        for i, key_data in enumerate(top_keys):
            try:
                print(f"\n🎯 [{i+1}/{len(top_keys)}] {key_data['private_key'][:12]}... (Q: {key_data['quality_score']:.3f}, E: {key_data['entropy']:.3f})")
                
                # Derive addresses
                eth_addr, btc_addr, success = self.derive_addresses(key_data['private_key'])
                if not success:
                    print(f"    ❌ Address derivation failed")
                    continue
                
                print(f"    📍 ETH: {eth_addr}")
                print(f"    📍 BTC: {btc_addr}")
                
                # Check balances
                balances = self.check_balance_fast(eth_addr, btc_addr)
                
                if balances['has_balance']:
                    jackpot = {
                        'private_key': key_data['private_key'],
                        'eth_address': eth_addr,
                        'btc_address': btc_addr,
                        'eth_balance': balances['eth'],
                        'btc_balance': balances['btc'],
                        'quality_score': key_data['quality_score'],
                        'entropy': key_data['entropy'],
                        'found_at': datetime.now().isoformat()
                    }
                    
                    results['jackpots'].append(jackpot)
                    results['jackpots_found'] += 1
                    self.jackpots_found.append(jackpot)
                    
                    print(f"    🎉 LASER FOCUS JACKPOT! ETH: {balances['eth']} wei, BTC: {balances['btc']} sat")
                    
                    # Immediate jackpot save
                    jackpot_file = os.path.join(RESULTS_DIR, f"LASER_JACKPOT_{timestamp}_{i+1}.json")
                    with open(jackpot_file, 'w') as f:
                        json.dump(jackpot, f, indent=2)
                        
                else:
                    print(f"    ✓ Empty (but high quality)")
                    results['high_quality_empty'].append({
                        'private_key': key_data['private_key'][:16] + '...',
                        'quality_score': key_data['quality_score'],
                        'entropy': key_data['entropy']
                    })
                
                results['keys_checked'] += 1
                
                # Progress update
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                progress = ((i + 1) / len(top_keys)) * 100
                
                print(f"    📊 Progress: {progress:.1f}% | Rate: {rate:.2f} keys/sec | Jackpots: {results['jackpots_found']}")
                
            except Exception as e:
                error_info = {
                    'key': key_data['private_key'][:16] + '...',
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
                results['errors'].append(error_info)
                print(f"    ❌ Error: {e}")
        
        # Final results
        total_time = time.time() - start_time
        results['total_time'] = total_time
        results['processing_rate'] = len(top_keys) / total_time if total_time > 0 else 0
        
        # Save results
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Final report
        print(f"""
╔══════════════════════════════════════════════════════╗
║           🎯 LASER FOCUS HUNT COMPLETE                ║
╠══════════════════════════════════════════════════════╣
║  ⏱️  Total Time: {total_time:.1f} seconds                     ║
║  🔍 Keys Analyzed: {len(top_keys)}                        ║
║  ⚡ Processing Rate: {results['processing_rate']:.2f} keys/sec          ║
║  🎉 JACKPOTS FOUND: {results['jackpots_found']}                       ║
║  🏆 Success Rate: {(results['jackpots_found']/len(top_keys)*100) if top_keys else 0:.1f}%                    ║
╠══════════════════════════════════════════════════════╣
║  📁 Results: {os.path.basename(results_file)}      ║
╚══════════════════════════════════════════════════════╝
        """)
        
        if results['jackpots_found'] > 0:
            print("🎊 LASER FOCUS JACKPOTS DISCOVERED!")
            for jackpot in results['jackpots']:
                print(f"   💎 {jackpot['private_key'][:16]}... (Quality: {jackpot['quality_score']:.3f})")
                print(f"      ETH: {jackpot['eth_balance']} wei")
                print(f"      BTC: {jackpot['btc_balance']} satoshi")
        else:
            print("💡 No jackpots found in this laser-focused hunt.")
            print("🎯 All keys checked were high-quality but empty.")
            print("🔄 Consider expanding to additional datasets or lowering quality threshold.")

def main():
    print("🎯 Initializing Laser Focus Jackpot Hunter...")
    
    hunter = LaserFocusHunter()
    hunter.laser_focus_hunt()

if __name__ == "__main__":
    main()
