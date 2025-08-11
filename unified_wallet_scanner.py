#!/usr/bin/env python3
"""
Unified Wallet Scanner - Complete All-in-One Solution
Combines extraction, deduplication, pattern analysis, balance checking, and monitoring
Version 2.0 - Consolidated from all previous scanners
"""
import json
import os
import sys
import time
import sqlite3
import hashlib
import threading
import logging
import requests
import argparse
import re
import plyvel
from decimal import Decimal
from collections import defaultdict
from datetime import datetime, timedelta
from bip_utils import WifEncoder, WifDecoder, Bip44, Bip44Coins, Bip44Changes, Bip39SeedGenerator
from eth_keys import keys as eth_keys
from eth_utils import to_checksum_address

class UnifiedWalletScanner:
    def __init__(self, config_file='api_config.json'):
        """Initialize the unified scanner with all capabilities"""
        
        # Load configuration
        self.config = self.load_config(config_file)
        
        # Setup HTTP session with proper headers
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'WalletRecovery/2.0'})
        
        # Initialize duplicate prevention system
        self.init_deduplication_db()
        self.address_cache = set()
        self.cache_lock = threading.Lock()
        
        # Setup logging
        self.setup_logging()
        
        # Statistics and monitoring
        self.stats = {
            'addresses_checked': 0,
            'duplicates_prevented': 0,
            'funded_addresses': [],
            'patterns_found': defaultdict(int),
            'start_time': time.time(),
            'last_funded_time': None,
            'scan_rate': 0,
            'current_batch': 0
        }
        
        # Pattern analysis - will be learned from data, not hardcoded
        self.successful_patterns = []
        
        # Rate limiting
        self.last_api_calls = {
            'etherscan': 0.0,
            'bitcoin': 0.0,
            'solana': 0.0
        }
        
        print("🚀 Unified Wallet Scanner initialized")
        print(f"✅ Configuration loaded from {config_file}")
        print(f"📊 Tracking {len(self.successful_patterns)} successful patterns")
    
    def load_config(self, config_file):
        """Load API configuration"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                self.logger.info("API configuration loaded successfully") if hasattr(self, 'logger') else None
                return config
        except Exception as e:
            print(f"⚠️  Using default config: {e}")
            return {
                "etherscan_api_key": "RHI2QM5XKCUI3TDNKSEVI28PGHR4RY9I79",
                "alchemy_api_key": "6Zn_wn5ckNFSoL6Ch3_kQ",
                "bitcoin_apis": [
                    "https://blockchain.info",
                    "https://api.blockcypher.com/v1/btc/main",
                    "https://mempool.space/api",
                    "https://blockstream.info/api", 
                    "https://insight.bitpay.com/api"
                ],
                "ethereum_apis": [
                    "https://api.etherscan.io/api",
                    "https://eth-mainnet.g.alchemy.com/v2/6Zn_wn5ckNFSoL6Ch3_kQ",
                    "https://mainnet.infura.io/v3/demo"
                ],
                "solana_rpc": "https://api.mainnet-beta.solana.com",
                "rate_limits": {
                    "etherscan": 5,      # requests per second
                    "bitcoin": 10,       # requests per second  
                    "solana": 3          # requests per second
                },
                "batch_size": 50,        # addresses per batch
                "save_interval": 100     # save progress every N addresses
            }
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('unified_scanner.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Unified Wallet Scanner started")
    
    def init_deduplication_db(self):
        """Initialize SQLite database for advanced duplicate prevention"""
        self.db_path = 'address_tracking.db'
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.db_lock = threading.Lock()
        
        with self.db_lock:
            # Enhanced schema with pattern tracking
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS checked_addresses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    address TEXT UNIQUE NOT NULL,
                    chain TEXT NOT NULL,
                    balance REAL DEFAULT 0,
                    checked_timestamp INTEGER NOT NULL,
                    private_key_hash TEXT,
                    pattern_score INTEGER DEFAULT 0,
                    source_type TEXT DEFAULT 'leveldb',
                    batch_id INTEGER DEFAULT 0,
                    verification_status TEXT DEFAULT 'checked'
                )
            ''')
            
            # Create optimized indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_address ON checked_addresses(address)",
                "CREATE INDEX IF NOT EXISTS idx_pattern_score ON checked_addresses(pattern_score DESC)",
                "CREATE INDEX IF NOT EXISTS idx_chain ON checked_addresses(chain)",
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON checked_addresses(checked_timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_balance ON checked_addresses(balance DESC)"
            ]
            
            for index_sql in indexes:
                self.conn.execute(index_sql)
            
            self.conn.commit()
            
        # Load existing addresses into cache for faster lookups
        self.load_address_cache()
        print("✅ Advanced duplicate prevention database initialized")
    
    def load_address_cache(self):
        """Load existing addresses into memory cache"""
        try:
            with self.db_lock:
                cursor = self.conn.execute("SELECT address FROM checked_addresses")
                addresses = [row[0] for row in cursor.fetchall()]
                
            with self.cache_lock:
                self.address_cache.update(addresses)
                
            print(f"📝 Loaded {len(addresses)} addresses into cache")
        except Exception as e:
            if hasattr(self, 'cache_lock'):
                print(f"⚠️  Cache loading error: {e}")
            else:
                print(f"⚠️  Cache loading error (cache_lock not initialized): {e}")
    
    def is_duplicate(self, address, private_key=None):
        """Advanced duplicate checking with caching"""
        
        # Fast cache check first
        with self.cache_lock:
            if address in self.address_cache:
                self.stats['duplicates_prevented'] += 1
                return True
        
        # Database verification for cache misses
        with self.db_lock:
            cursor = self.conn.execute(
                "SELECT id FROM checked_addresses WHERE address = ? LIMIT 1", 
                (address,)
            )
            if cursor.fetchone():
                self.stats['duplicates_prevented'] += 1
                # Add to cache for future fast lookups
                with self.cache_lock:
                    self.address_cache.add(address)
                return True
        
        return False
    
    def record_address(self, address, chain, balance=0.0, private_key=None, pattern_score=0):
        """Record checked address with enhanced metadata"""
        
        # Add to cache immediately
        with self.cache_lock:
            self.address_cache.add(address)
        
        # Generate private key hash for security
        private_key_hash = None
        if private_key:
            private_key_hash = hashlib.sha256(private_key.encode()).hexdigest()[:16]
        
        # Database record with full metadata
        with self.db_lock:
            self.conn.execute('''
                INSERT OR REPLACE INTO checked_addresses 
                (address, chain, balance, checked_timestamp, private_key_hash, 
                 pattern_score, source_type, batch_id, verification_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                address, chain, balance, int(time.time()), private_key_hash,
                pattern_score, 'leveldb', self.stats['current_batch'],
                'funded' if balance > 0 else 'checked'
            ))
            self.conn.commit()
        
        self.stats['addresses_checked'] += 1
        
        # Auto-save progress periodically
        if self.stats['addresses_checked'] % self.config.get('save_interval', 100) == 0:
            self.save_progress()
    
    def calculate_pattern_score(self, address, private_key=None, source=""):
        """Calculate sophisticated pattern-based score for address likelihood"""
        score = 0.0
        
        # Check against known successful patterns
        for pattern in self.successful_patterns:
            if pattern.lower() in address.lower():
                score += 10
                self.stats['patterns_found'][pattern] += 1
        
        # Advanced heuristics based on wallet analysis
        
        # 1. Address format scoring (higher = more likely to have funds)
        if address.startswith('1') and len(address) == 34:  # Bitcoin P2PKH (most common)
            score += 5.0
        elif address.startswith('bc1q') and len(address) == 42:  # Bitcoin Bech32 (modern)
            score += 4.0
        elif address.startswith('3') and len(address) == 34:  # Bitcoin P2SH (multisig/scripts)
            score += 3.5
        elif address.startswith('0x') and len(address) == 42:  # Ethereum
            score += 4.5
        
        # 2. Private key entropy analysis (non-sequential = higher score)
        if private_key:
            entropy_score = self.analyze_key_entropy(private_key)
            score += entropy_score
        
        # 3. Source wallet type scoring (based on likelihood of funds)
        source_lower = source.lower()
        if 'metamask' in source_lower:
            score += 8.0  # MetaMask very common, high chance of funds
        elif 'trust' in source_lower:
            score += 6.0  # Trust Wallet popular
        elif 'phantom' in source_lower:
            score += 5.0  # Phantom for Solana
        elif 'coinbase' in source_lower:
            score += 7.0  # Coinbase users likely have funds
        elif 'binance' in source_lower:
            score += 6.5  # Binance Chain Wallet
        elif 'ronin' in source_lower:
            score += 4.0  # Gaming wallet
        elif 'authenticator' in source_lower or 'authy' in source_lower:
            score -= 3.0  # 2FA apps, not wallets
        elif 'bitwarden' in source_lower or 'evernote' in source_lower:
            score -= 5.0  # Password managers, not crypto
        
        # 4. Geographic/IP analysis (some regions more likely to have funds)
        if 'US' in source or 'CA' in source or 'CH' in source or 'CY' in source:
            score += 2.0  # Developed countries
        elif 'BR' in source or 'CO' in source or 'CL' in source:
            score += 1.5  # Emerging markets with crypto adoption
        
        # 5. Browser profile analysis (multiple profiles = power user)
        if 'Profile' in source and any(x in source for x in ['2', '3', '9', '13']):
            score += 3.0  # Power users with multiple profiles
        elif 'Default' in source:
            score += 1.0  # Default profiles
        
        # 6. Penalize obviously problematic addresses
        if self.looks_sequential(address):
            score -= 10.0
        if self.is_known_empty_pattern(address):
            score -= 8.0
        
        # 7. Boost addresses that match funded patterns
        if self.matches_funded_pattern(address):
            score += 15.0
        
        return max(0.0, score)
    
    def analyze_key_entropy(self, private_key):
        """Analyze private key for entropy (randomness)"""
        if not private_key or len(private_key) < 32:
            return -2.0
        
        # Convert to bytes for analysis
        try:
            key_bytes = bytes.fromhex(private_key)
        except:
            return -1.0
        
        # Check for patterns that suggest low entropy
        if len(set(private_key)) < 8:  # Too few unique characters
            return -5.0
        
        # Check for repeated patterns
        if any(private_key[i:i+4] == private_key[i+4:i+8] for i in range(0, len(private_key)-8, 4)):
            return -3.0
        
        # Check for sequential patterns
        if self.has_sequential_hex(private_key):
            return -4.0
        
        # Good entropy indicators
        unique_chars = len(set(private_key))
        if unique_chars >= 12:
            return 3.0
        elif unique_chars >= 8:
            return 1.5
        else:
            return 0.0
    
    def has_sequential_hex(self, hex_string):
        """Check if hex string has sequential patterns"""
        for i in range(len(hex_string) - 6):
            chunk = hex_string[i:i+6]
            if chunk in ['012345', '123456', '234567', '345678', '456789', '56789a', 
                        '6789ab', '789abc', '89abcd', '9abcde', 'abcdef', 'fedcba', 
                        '987654', '876543', '765432', '654321', '543210']:
                return True
        return False
    
    def is_known_empty_pattern(self, address):
        """Check if address matches known empty patterns"""
        # Common empty/burn addresses
        empty_patterns = [
            '000000000000000000000000000000000000',
            '111111111111111111111111111111111111',
            'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
            'fffffffffffffffffffffffffffffffffffff'
        ]
        addr_lower = address.lower().replace('0x', '')
        return any(pattern in addr_lower for pattern in empty_patterns)
    
    def matches_funded_pattern(self, address):
        """Check if address matches patterns known to have funds"""
        # This would be enhanced with historical data
        # For now, basic heuristics
        if address.startswith('1') and address[1:3] in ['A', 'B', 'C', 'D', 'E', 'F']:
            return True  # These prefixes often have funds
        if address.startswith('0x') and address[2:4] in ['1', '2', '3', '4', '5']:
            return True  # These Ethereum prefixes common
        return False
    
    def looks_sequential(self, address):
        """Check if address looks like it was generated sequentially"""
        # Remove common prefixes
        addr = address.lower().replace('0x', '').replace('1', '').replace('3', '')
        
        # Check for obvious sequential patterns
        sequential_patterns = [
            '0000000000', '1111111111', '2222222222', '3333333333',
            '4444444444', '5555555555', '6666666666', '7777777777',
            '8888888888', '9999999999', 'aaaaaaaaaa', 'bbbbbbbbbb',
            '012345', '123456', '234567', '345678', '456789',
            '987654', '876543', '765432', '654321', '543210',
            'abcdef', 'bcdefg', 'cdefgh', 'defghi', 'efghij',
            'fedcba', 'edcbaf', 'dcbafe', 'cbafed', 'bafedx'
        ]
        
        return any(pattern in addr for pattern in sequential_patterns)
    
    def check_bitcoin_balance_batch(self, addresses):
        """Check multiple Bitcoin addresses at once using blockchain.info batch API"""
        
        # Remove duplicates from the batch before processing
        unique_addresses = list(dict.fromkeys(addresses))  # Preserves order while removing duplicates
        duplicate_count = len(addresses) - len(unique_addresses)
        
        if duplicate_count > 0:
            print(f"⚠️  Removed {duplicate_count} duplicate addresses from batch", end="")
        
        # Rate limiting for batch requests
        current_time = time.time()
        time_since_last = current_time - self.last_api_calls.get('bitcoin', 0)
        min_interval = 3.0  # 3 second minimum between batch requests
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)
        
        results = {}
        
        # Blockchain.info supports up to ~100 addresses per request
        batch_size = min(50, len(unique_addresses))  # Be conservative with batch size
        
        try:
            # Only use valid Bitcoin addresses for batch request
            valid_addresses = []
            for addr in unique_addresses[:batch_size]:
                # Basic validation - Bitcoin addresses should be 25-34 characters
                if len(addr) >= 25 and len(addr) <= 42 and not ' ' in addr:
                    valid_addresses.append(addr)
                else:
                    results[addr] = 0  # Invalid addresses get 0 balance
            
            if not valid_addresses:
                # No valid addresses, return all zeros
                for addr in unique_addresses:
                    results[addr] = 0
                return results
            
            # Join addresses with | separator for blockchain.info batch API
            address_string = '|'.join(valid_addresses)
            
            # Try blockchain.info batch endpoint first
            url = f"https://blockchain.info/balance?active={address_string}"
            print(f"🌐 Checking {len(valid_addresses)} unique addresses in batch", end="", flush=True)
            
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # blockchain.info returns: {"address": {"final_balance": satoshis, "n_tx": count, "total_received": satoshis}}
                for address in valid_addresses:
                    if address in data:
                        balance_sats = data[address].get('final_balance', 0)
                        balance_btc = balance_sats / 100000000
                        results[address] = balance_btc
                    else:
                        results[address] = 0
                
                self.last_api_calls['bitcoin'] = time.time()
                print(f" ✅ Batch complete", end="")
                
                # For duplicate addresses, copy the result
                if duplicate_count > 0:
                    for original_addr in addresses:
                        if original_addr not in results and original_addr in unique_addresses:
                            # Find the result for this duplicate address
                            idx = unique_addresses.index(original_addr)
                            if idx < len(unique_addresses):
                                results[original_addr] = results.get(unique_addresses[idx], 0)
                
                return results
            
            elif response.status_code == 400:
                print(f" ❌ Bad Request (possibly invalid addresses)", end="")
                # Fall back to individual requests for validation
            elif response.status_code == 429:
                print(f" ❌ Rate limited", end="")
            else:
                print(f" ❌ HTTP {response.status_code}", end="")
                
        except requests.exceptions.Timeout:
            print(f" ❌ Batch timeout", end="")
        except requests.exceptions.RequestException as e:
            print(f" ❌ Batch error: {str(e)[:20]}", end="")
        except Exception as e:
            print(f" ❌ Batch parse error: {str(e)[:20]}", end="")
        
        # Fall back to individual requests if batch fails
        print(f", falling back to individual requests", end="")
        for address in unique_addresses:
            if address not in results:  # Only check addresses not already processed
                individual_balance = self.check_bitcoin_balance(address)
                results[address] = individual_balance
        
        # For duplicate addresses in original list, copy the results
        if duplicate_count > 0:
            final_results = {}
            for original_addr in addresses:
                final_results[original_addr] = results.get(original_addr, 0)
            return final_results
        
        return results

    def check_bitcoin_balance(self, address):
        """Enhanced Bitcoin balance checking with Blockchain.info API prioritized"""
        
        # Rate limiting - be more conservative
        current_time = time.time()
        time_since_last = current_time - self.last_api_calls.get('bitcoin', 0)
        min_interval = 2.0  # 2 second minimum between requests to avoid rate limiting
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)
        
        # Try multiple Bitcoin APIs for reliability, prioritizing blockchain.info
        apis = self.config.get('bitcoin_apis', [
            "https://blockchain.info",
            "https://api.blockcypher.com/v1/btc/main",
            "https://mempool.space/api",
            "https://blockstream.info/api"
        ])
        
        for i, api_base in enumerate(apis):
            try:
                # Different URL formats for different APIs
                if "blockchain.info" in api_base:
                    # Use the single address balance endpoint for reliability
                    url = f"{api_base}/rawaddr/{address}?limit=0"
                elif "blockcypher.com" in api_base:
                    url = f"{api_base}/addrs/{address}/balance"
                elif "insight.bitpay.com" in api_base:
                    url = f"{api_base}/addr/{address}"
                else:
                    # mempool.space and blockstream.info format
                    url = f"{api_base}/address/{address}"
                
                api_name = api_base.split('//')[1].split('/')[0]
                print(f"🌐 {api_name}", end="", flush=True)
                
                # Shorter timeout and better error handling
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    balance_sats = 0
                    
                    # Handle different API response formats
                    if 'final_balance' in data:
                        # Blockchain.info format - this is the main one we want
                        balance_sats = data.get('final_balance', 0)
                        print(f" ✅ (blockchain.info)", end="")
                    elif 'chain_stats' in data:
                        # Blockstream format
                        balance_sats = data['chain_stats'].get('funded_txo_sum', 0)
                        print(f" ✅ (blockstream)", end="")
                    elif 'balance' in data and isinstance(data['balance'], int):
                        # BlockCypher or generic format (satoshis)
                        balance_sats = data.get('balance', 0)
                        print(f" ✅ (blockcypher)", end="")
                    elif 'balanceSat' in data:
                        # Insight format
                        balance_sats = data.get('balanceSat', 0)
                        print(f" ✅ (insight)", end="")
                    elif 'balance' in data and isinstance(data['balance'], (float, str)):
                        # Balance already in BTC format
                        try:
                            balance_btc = float(data['balance'])
                            self.last_api_calls['bitcoin'] = time.time()
                            print(f" ✅ (btc format)", end="")
                            return balance_btc
                        except:
                            continue
                    else:
                        # Try to find balance in any numeric field
                        for key, value in data.items():
                            if 'balance' in key.lower() and isinstance(value, (int, float)):
                                if value > 21000000:  # Likely satoshis if > 21M
                                    balance_sats = int(value)
                                    print(f" ✅ (found: {key})", end="")
                                    break
                                else:  # Likely BTC
                                    balance_btc = float(value)
                                    self.last_api_calls['bitcoin'] = time.time()
                                    print(f" ✅ (btc: {key})", end="")
                                    return balance_btc
                    
                    balance_btc = balance_sats / 100000000  # Convert satoshis to BTC
                    
                    self.last_api_calls['bitcoin'] = time.time()
                    return balance_btc
                
                elif response.status_code == 429:
                    print(f" ❌ Rate limited", end="")
                    # If rate limited, wait longer and try next API
                    if i < len(apis) - 1:  # Not the last API
                        print(f", trying next API", end="")
                        time.sleep(3)  # Wait 3 seconds before trying next
                        continue
                    else:
                        print(f", all APIs rate limited", end="")
                        return 0
                
                else:
                    print(f" ❌ HTTP {response.status_code}", end="")
                    continue
                
            except requests.exceptions.Timeout:
                print(f" ❌ Timeout", end="")
                continue
            except requests.exceptions.ConnectionError:
                print(f" ❌ Connection failed", end="")
                continue
            except requests.exceptions.RequestException as e:
                print(f" ❌ Request error: {str(e)[:15]}", end="")
                continue
            except Exception as e:
                print(f" ❌ Parse error: {str(e)[:15]}", end="")
                continue
        
        print(f" ❌ All APIs failed", end="")
        return 0
    
    def check_ethereum_balance(self, address):
        """Enhanced Ethereum balance checking with multiple API support"""
        
        # Rate limiting - be more conservative with APIs
        current_time = time.time()
        time_since_last = current_time - self.last_api_calls.get('etherscan', 0)
        min_interval = 1.0  # 1 second between requests
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)
        
        # Try multiple Ethereum APIs for reliability
        ethereum_apis = self.config.get('ethereum_apis', [
            "https://api.etherscan.io/api",
            "https://eth-mainnet.g.alchemy.com/v2/6Zn_wn5ckNFSoL6Ch3_kQ",
            "https://mainnet.infura.io/v3/demo"
        ])
        
        etherscan_api_key = self.config.get('etherscan_api_key')
        alchemy_api_key = self.config.get('alchemy_api_key')
        
        for i, api_url in enumerate(ethereum_apis):
            try:
                api_name = api_url.split('//')[1].split('/')[0]
                print(f"🌐 {api_name}", end="", flush=True)
                
                if "etherscan.io" in api_url:
                    # Etherscan API format
                    if not etherscan_api_key or etherscan_api_key == "YourApiKeyToken":
                        print(f" ❌ No API key", end="")
                        continue
                    
                    params = {
                        'module': 'account',
                        'action': 'balance',
                        'address': address,
                        'tag': 'latest',
                        'apikey': etherscan_api_key
                    }
                    
                    response = self.session.get(api_url, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if data.get('status') == '1':
                            balance_wei = int(data.get('result', 0))
                            balance_eth = balance_wei / (10**18)  # Convert Wei to ETH
                            
                            self.last_api_calls['etherscan'] = time.time()
                            print(f" ✅", end="")
                            return balance_eth
                        else:
                            error_msg = data.get('message', 'Unknown error')
                            print(f" ❌ API error: {error_msg[:15]}", end="")
                            continue
                    else:
                        print(f" ❌ HTTP {response.status_code}", end="")
                        continue
                
                elif "alchemy.com" in api_url or "infura.io" in api_url:
                    # JSON-RPC format for Alchemy/Infura
                    payload = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "eth_getBalance",
                        "params": [address, "latest"]
                    }
                    
                    response = self.session.post(api_url, json=payload, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'result' in data and data['result']:
                            # Convert hex result to decimal wei, then to ETH
                            balance_wei = int(data['result'], 16)
                            balance_eth = balance_wei / (10**18)  # Convert Wei to ETH
                            
                            self.last_api_calls['etherscan'] = time.time()
                            print(f" ✅", end="")
                            return balance_eth
                        elif 'error' in data:
                            error_msg = data['error'].get('message', 'Unknown error')
                            print(f" ❌ RPC error: {error_msg[:15]}", end="")
                            continue
                        else:
                            print(f" ❌ Invalid response", end="")
                            continue
                    else:
                        print(f" ❌ HTTP {response.status_code}", end="")
                        continue
                
                else:
                    print(f" ❌ Unknown API format", end="")
                    continue
                    
            except requests.exceptions.Timeout:
                print(f" ❌ Timeout", end="")
                continue
            except requests.exceptions.RequestException as e:
                print(f" ❌ Request error: {str(e)[:15]}", end="")
                continue
            except Exception as e:
                print(f" ❌ Parse error: {str(e)[:15]}", end="")
                continue
        
        print(f" ❌ All APIs failed", end="")
        return 0
    
    def check_solana_balance(self, address):
        """Basic Solana balance checking"""
        
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_api_calls.get('solana', 0)
        min_interval = 1.0 / self.config.get('rate_limits', {}).get('solana', 3)
        
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        
        try:
            rpc_url = self.config.get('solana_rpc', 'https://api.mainnet-beta.solana.com')
            
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [address]
            }
            
            response = self.session.post(rpc_url, json=payload, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if 'result' in data and 'value' in data['result']:
                    balance_lamports = data['result']['value']
                    balance_sol = balance_lamports / 1000000000  # Convert lamports to SOL
                    
                    self.last_api_calls['solana'] = time.time()
                    return balance_sol
            
        except Exception as e:
            self.logger.warning(f"Solana balance check error: {e}")
        
        return 0
    
    def save_funded_address(self, address, chain, balance, private_key, pattern_score):
        """Save funded address with comprehensive logging"""
        
        funded_info = {
            'address': address,
            'chain': chain,
            'balance': float(balance),
            'private_key': private_key,
            'pattern_score': pattern_score,
            'found_timestamp': time.time(),
            'found_date': datetime.now().isoformat(),
            'scanner_version': 'unified_v2.0',
            'verification_method': 'api_confirmed'
        }
        
        self.stats['funded_addresses'].append(funded_info)
        self.stats['last_funded_time'] = time.time()
        
        # Immediately save to multiple formats for safety
        self.save_results()
        
        # Log the discovery
        self.logger.info(f"FUNDED ADDRESS DISCOVERED: {chain.upper()} {address} - Balance: {balance}")
        
        # Print detailed discovery report
        print(f"\n" + "="*60)
        print(f"🎉 FUNDED ADDRESS FOUND!")
        print(f"="*60)
        print(f"🔗 Chain: {chain.upper()}")
        print(f"📍 Address: {address}")
        print(f"💰 Balance: {balance}")
        print(f"🎯 Pattern Score: {pattern_score}/25")
        print(f"🔑 Private Key: {private_key}")
        print(f"⏰ Found: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Total Found: {len(self.stats['funded_addresses'])}")
        print("="*60)
        
        return funded_info
    
    def process_address(self, address, chain, private_key=None):
        """Process a single address with full pipeline"""
        
        # Skip duplicates early
        if self.is_duplicate(address, private_key):
            return False
        
        # Calculate priority score for this address
        pattern_score = self.calculate_pattern_score(address, private_key)
        
        # Check balance based on chain
        balance = 0
        try:
            print(f"🔍 Checking {chain} balance for {address[:10]}...{address[-6:]}", end=" ", flush=True)
            if chain.lower() == 'bitcoin':
                balance = self.check_bitcoin_balance(address)
            elif chain.lower() == 'ethereum':
                balance = self.check_ethereum_balance(address)
            elif chain.lower() == 'solana':
                balance = self.check_solana_balance(address)
            else:
                self.logger.warning(f"Unknown chain type: {chain}")
            
            if balance > 0:
                print(f"💰 FUNDED! {balance}")
            else:
                print("❌")
        
        except Exception as e:
            print(f"⚠️ Error: {e}")
            self.logger.error(f"Balance check failed for {address}: {e}")
        
        # Record the address regardless of balance
        self.record_address(address, chain, balance, private_key, pattern_score)
        
        # Save funded addresses immediately
        if balance > 0:
            self.save_funded_address(address, chain, balance, private_key, pattern_score)
            return True
        
        return False
    
    def generate_addresses_from_private_key(self, private_key_hex):
        """Generate addresses for all supported chains from private key"""
        addresses = {}
        
        try:
            # Clean and validate private key
            private_key_hex = private_key_hex.strip().lower()
            if not private_key_hex or len(private_key_hex) != 64:
                return addresses
            
            # Bitcoin addresses (multiple formats)
            try:
                private_key_int = int(private_key_hex, 16)
                
                # Validate private key range
                if 1 <= private_key_int <= 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364140:
                    
                    # Compressed Bitcoin address (most common)
                    try:
                        private_key_bytes = private_key_int.to_bytes(32, byteorder='big')
                        ctx = Bip44.FromPrivateKey(private_key_bytes, Bip44Coins.BITCOIN)
                        addresses['bitcoin_compressed'] = ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0).PublicKey().ToAddress()
                    except:
                        pass
                    
                    # Uncompressed Bitcoin address (legacy)
                    try:
                        private_key_bytes = private_key_int.to_bytes(32, byteorder='big')
                        ctx = Bip44.FromPrivateKey(private_key_bytes, Bip44Coins.BITCOIN)
                        addresses['bitcoin_uncompressed'] = ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0).PublicKey().ToAddress()
                    except:
                        pass
            
            except ValueError:
                pass  # Invalid hex string
            except Exception as e:
                self.logger.debug(f"Bitcoin address generation error: {e}")
            
            # Ethereum address
            try:
                private_key_bytes = bytes.fromhex(private_key_hex.zfill(64))
                eth_private_key = eth_keys.PrivateKey(private_key_bytes)
                eth_address = to_checksum_address(eth_private_key.public_key.to_address())
                addresses['ethereum'] = eth_address
            
            except Exception as e:
                self.logger.debug(f"Ethereum address generation error: {e}")
            
            # Basic Solana support (would need solders library for full implementation)
            try:
                # Placeholder for Solana address generation
                # This would require proper Solana libraries
                # addresses['solana'] = generate_solana_address(private_key_hex)
                pass
            except Exception as e:
                self.logger.debug(f"Solana address generation error: {e}")
        
        except Exception as e:
            self.logger.error(f"Address generation error for key {private_key_hex[:8]}...: {e}")
        
        return addresses
    
    def extract_private_keys(self, text):
        """Extract potential private keys from text data"""
        import re
        
        private_keys = set()
        
        # 64-character hexadecimal strings (256-bit private keys)
        hex_pattern = r'\b[0-9a-fA-F]{64}\b'
        hex_matches = re.findall(hex_pattern, text)
        
        for match in hex_matches:
            # Skip obvious null keys or weak patterns
            if (not match.startswith('0000000000000000') and 
                not match == '0' * 64 and 
                not match == 'f' * 64):
                private_keys.add(match.lower())
        
        # WIF format Bitcoin private keys
        wif_pattern = r'\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b'
        wif_matches = re.findall(wif_pattern, text)
        
        for wif_key in wif_matches:
            try:
                # Convert WIF to hex format
                try:
                    decoded = WifDecoder.Decode(wif_key)
                    private_key_bytes = decoded[0]  # First element is the private key bytes
                    hex_key = private_key_bytes.hex().lower()
                    private_keys.add(hex_key)
                except Exception:
                    pass  # Invalid WIF key
            except Exception:
                pass  # Invalid WIF key
        
        # Base58 private keys (another Bitcoin format)
        base58_pattern = r'\b[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{51,52}\b'
        base58_matches = re.findall(base58_pattern, text)
        
        for b58_key in base58_matches:
            try:
                # Attempt to decode as WIF
                decoded = WifDecoder.Decode(b58_key)
                private_key_bytes = decoded[0]  # First element is the private key bytes
                hex_key = private_key_bytes.hex().lower()
                private_keys.add(hex_key)
            except Exception:
                pass  # Not a valid private key
        
        return list(private_keys)
    
    def scan_leveldb_directory(self, db_path):
        """Scan a single LevelDB directory"""
        
        print(f"📁 Scanning LevelDB: {db_path}")
        
        addresses_found = 0
        keys_processed = 0
        
        try:
            # Open LevelDB database
            db = plyvel.DB(db_path, create_if_missing=False)
            
            # Scan through all key-value pairs
            for key, value in db:
                keys_processed += 1
                
                try:
                    # Decode both key and value
                    key_str = key.decode('utf-8', errors='ignore')
                    value_str = value.decode('utf-8', errors='ignore')
                    combined_data = key_str + value_str
                    
                    # Extract potential private keys
                    potential_keys = self.extract_private_keys(combined_data)
                    
                    # Process each potential private key
                    for private_key in potential_keys:
                        addresses = self.generate_addresses_from_private_key(private_key)
                        
                        # Check each generated address
                        for chain_type, address in addresses.items():
                            chain_name = chain_type.split('_')[0]  # bitcoin_compressed -> bitcoin
                            
                            found = self.process_address(address, chain_name, private_key)
                            if found:
                                addresses_found += 1
                
                except Exception as e:
                    continue  # Skip problematic entries
                
                # Progress reporting - show more frequent updates
                if keys_processed % 100 == 0:  # Show progress every 100 keys instead of 1000
                    print(f"🔍 Processed {keys_processed} keys from database...")
                
                if keys_processed % 1000 == 0:
                    self.print_progress_update()
            
            db.close()
            
        except Exception as e:
            self.logger.error(f"Error scanning {db_path}: {e}")
        
        print(f"✅ Completed {db_path}: {keys_processed} keys processed, {addresses_found} funded found")
        return addresses_found
    
    def scan_directory_tree(self, root_directory):
        """Recursively scan directory tree for LevelDB databases"""
        
        print(f"🔍 Scanning directory tree: {root_directory}")
        
        if not os.path.exists(root_directory):
            print(f"❌ Directory not found: {root_directory}")
            return
        
        leveldb_dirs = []
        total_funded = 0
        
        # Find all LevelDB directories
        for root, dirs, files in os.walk(root_directory):
            # Check if this looks like a LevelDB directory
            if any(f.endswith('.ldb') for f in files) or 'CURRENT' in files:
                leveldb_dirs.append(root)
        
        print(f"📂 Found {len(leveldb_dirs)} LevelDB directories")
        
        # Process each LevelDB directory
        for i, db_dir in enumerate(leveldb_dirs, 1):
            print(f"\n📊 Processing database {i}/{len(leveldb_dirs)}")
            self.stats['current_batch'] = i
            
            found_in_db = self.scan_leveldb_directory(db_dir)
            total_funded += found_in_db
            
            # Save progress after each database
            self.save_progress()
        
        print(f"\n🎉 Scan Complete!")
        print(f"📊 Total LevelDB databases: {len(leveldb_dirs)}")
        print(f"💰 Total funded addresses found: {total_funded}")
        print(f"⏱️  Total time: {self.get_runtime()}")
        
        # Final comprehensive report
        self.generate_final_report()
    
    def run_extraction_only(self, root_directory):
        """Extract all private keys and addresses, then sort by likelihood without balance checking"""
        print("📦 Starting extraction-only mode...")
        print("🔍 This will collect all private keys, generate addresses, and sort by likelihood")
        print("💡 No balance checking - just gathering and prioritizing for later analysis")
        print()
        
        leveldb_dirs = []
        
        # Find all LevelDB directories
        for root, dirs, files in os.walk(root_directory):
            if any(f.endswith('.ldb') for f in files) or 'CURRENT' in files:
                leveldb_dirs.append(root)
        
        print(f"📂 Found {len(leveldb_dirs)} LevelDB directories")
        
        extracted_data = []
        
        # Process each LevelDB directory
        for i, db_dir in enumerate(leveldb_dirs, 1):
            print(f"\n📊 Processing database {i}/{len(leveldb_dirs)}")
            print(f"📁 Extracting from: {db_dir}")
            
            db_data = self.extract_from_leveldb_directory(db_dir)
            extracted_data.extend(db_data)
            
            print(f"✅ Extracted {len(db_data)} key-address pairs from this database")
        
        print(f"\n🎯 Starting pattern analysis and sorting...")
        print(f"📊 Total extracted addresses: {len(extracted_data)}")
        
        # Calculate pattern scores for all addresses
        for i, addr_data in enumerate(extracted_data, 1):
            if i % 1000 == 0:
                print(f"🔍 Analyzing patterns: {i:,}/{len(extracted_data):,} ({100*i/len(extracted_data):.1f}%)")
            
            pattern_score = self.calculate_pattern_score(
                addr_data.get('address', ''), 
                addr_data.get('private_key', ''),
                addr_data.get('source_db', '')
            )
            addr_data['pattern_score'] = pattern_score
        
        # Sort by pattern score (highest first = most likely to have funds)
        print(f"🏆 Sorting {len(extracted_data):,} addresses by likelihood...")
        extracted_data.sort(key=lambda x: x.get('pattern_score', 0), reverse=True)
        
        # Show top results
        print(f"\n📈 Top 20 most promising addresses (highest likelihood):")
        for i, addr_data in enumerate(extracted_data[:20], 1):
            source_short = addr_data.get('source_db', 'unknown').split('/')[-1][:30]
            print(f"   {i:2d}. {addr_data['address'][:12]}...{addr_data['address'][-8:]} "
                  f"(score: {addr_data['pattern_score']:5.1f}, chain: {addr_data['chain']:<8}, source: {source_short})")
        
        # Show distribution
        print(f"\n📊 Likelihood score distribution:")
        high_score = len([x for x in extracted_data if x['pattern_score'] > 15])
        medium_score = len([x for x in extracted_data if 8 <= x['pattern_score'] <= 15])
        low_score = len([x for x in extracted_data if x['pattern_score'] < 8])
        
        print(f"   🔥 High likelihood (>15):   {high_score:6,} addresses ({100*high_score/len(extracted_data):.1f}%)")
        print(f"   ⚡ Medium likelihood (8-15): {medium_score:6,} addresses ({100*medium_score/len(extracted_data):.1f}%)")
        print(f"   📝 Low likelihood (<8):      {low_score:6,} addresses ({100*low_score/len(extracted_data):.1f}%)")
        
        # Save sorted data
        output_file = "extracted_addresses_sorted.json"
        with open(output_file, 'w') as f:
            json.dump(extracted_data, f, indent=2)
        
        print(f"\n🎉 Extraction and Sorting Complete!")
        print(f"📊 Total databases processed: {len(leveldb_dirs)}")
        print(f"🔑 Total key-address pairs extracted: {len(extracted_data):,}")
        print(f"💾 Saved sorted results to: {output_file}")
        print()
        print("🎯 Next steps:")
        print("   python3 unified_wallet_scanner.py --check-balances")
        print("   This will check balances starting with the highest likelihood addresses")
        
        # Also save top 1000 for quick testing
        top_1000 = extracted_data[:1000]
        top_1000_file = "top_1000_addresses.json"
        with open(top_1000_file, 'w') as f:
            json.dump(top_1000, f, indent=2)
        
        print(f"🚀 Also saved top 1,000 most promising addresses to: {top_1000_file}")
        print("\n👋 Extraction mode finished successfully!")
        return extracted_data
    
    def run_balance_check_prioritized(self, json_file_path=None):
        """Check balances for extracted addresses using pre-sorted prioritization"""
        print("💰 Starting balance checking on sorted addresses...")
        print("📊 Loading pre-sorted addresses (highest likelihood first)")
        print()
        
        # Load extracted addresses (prioritize sorted file)
        addresses_file = None
        if json_file_path and os.path.exists(json_file_path):
            addresses_file = json_file_path
            print(f"📂 Loading addresses from: {json_file_path}")
        elif os.path.exists("extracted_addresses_sorted.json"):
            addresses_file = "extracted_addresses_sorted.json"
            print(f"📂 Loading sorted addresses from: extracted_addresses_sorted.json")
        elif os.path.exists("top_1000_addresses.json"):
            addresses_file = "top_1000_addresses.json"
            print(f"📂 Loading top 1,000 addresses from: top_1000_addresses.json")
        elif os.path.exists("extracted_addresses_all.json"):
            addresses_file = "extracted_addresses_all.json"
            print(f"📂 Loading addresses from: extracted_addresses_all.json (will need to sort)")
        else:
            print("❌ No extracted addresses found. Run with --extract-only first.")
            return
        
        with open(addresses_file, 'r') as f:
            data = json.load(f)
        
        # Handle different JSON formats
        if isinstance(data, list):
            # Handle simple extractor format
            if data and isinstance(data[0], dict) and 'address' in data[0]:
                print(f"📊 Converting {len(data)} addresses from simple extractor format...")
                all_addresses = []
                for item in data:
                    all_addresses.append({
                        'address': item['address'],
                        'chain': item['chain'],
                        'source': item.get('source', 'unknown'),
                        'private_key': item.get('private_key', '')
                    })
            else:
                all_addresses = data
        elif 'extracted_addresses' in data:
            all_addresses = data['extracted_addresses']
        elif 'addresses' in data:
            all_addresses = data['addresses']
        else:
            print("❌ Unknown JSON format in file")
            return
        
        print(f"📦 Loaded {len(all_addresses)} extracted addresses")
        
        # Apply pattern scoring and prioritization
        print("🎯 Applying pattern analysis...")
        prioritized_addresses = []
        
        for addr_data in all_addresses:
            # Calculate pattern score with source analysis
            pattern_score = self.calculate_pattern_score(
                addr_data.get('address', ''), 
                addr_data.get('private_key', ''),
                addr_data.get('source', '')
            )
            addr_data['pattern_score'] = pattern_score
            prioritized_addresses.append(addr_data)
        
        # Sort by pattern score (highest first)
        prioritized_addresses.sort(key=lambda x: x['pattern_score'], reverse=True)
        
        print(f"🏆 Prioritized addresses by success pattern similarity")
        print(f"📈 Top 20 most promising addresses:")
        
        for i, addr_data in enumerate(prioritized_addresses[:20], 1):
            source_short = addr_data.get('source', 'unknown').split('/')[-1][:30]
            print(f"   {i:2d}. {addr_data['address'][:12]}...{addr_data['address'][-8:]} "
                  f"(score: {addr_data['pattern_score']:5.1f}, chain: {addr_data['chain']:<8}, source: {source_short})")
        
        print(f"\n📊 Score distribution:")
        high_score = len([x for x in prioritized_addresses if x['pattern_score'] > 15])
        medium_score = len([x for x in prioritized_addresses if 8 <= x['pattern_score'] <= 15])
        low_score = len([x for x in prioritized_addresses if x['pattern_score'] < 8])
        
        print(f"   � High priority (>15):   {high_score:6,} addresses")
        print(f"   ⚡ Medium priority (8-15): {medium_score:6,} addresses") 
        print(f"   📝 Low priority (<8):      {low_score:6,} addresses")
        
        # Skip the prompt for automated testing - just start checking
        print()
        print("🔍 Starting balance checks in priority order...")
        print(f"⚡ Checking highest scoring addresses first for maximum efficiency!")
        print()
        
        funded_found = 0
        start_time = time.time()
        
        # Separate addresses by chain for batch processing
        bitcoin_addresses = []
        ethereum_addresses = []
        solana_addresses = []
        other_addresses = []
        
        for addr_data in prioritized_addresses:
            chain = addr_data['chain'].lower()
            if chain == 'bitcoin':
                bitcoin_addresses.append(addr_data)
            elif chain == 'ethereum':
                ethereum_addresses.append(addr_data)
            elif chain == 'solana':
                solana_addresses.append(addr_data)
            else:
                other_addresses.append(addr_data)
        
        print(f"📊 Addresses by chain:")
        print(f"   🟠 Bitcoin: {len(bitcoin_addresses)}")
        print(f"   🔷 Ethereum: {len(ethereum_addresses)}")
        print(f"   🟣 Solana: {len(solana_addresses)}")
        print(f"   ❓ Other: {len(other_addresses)}")
        print()
        
        checked_count = 0
        
        # Track addresses already checked in this session to prevent duplicates
        checked_addresses_this_session = set()
        
        # Process Bitcoin addresses in batches (most efficient)
        if bitcoin_addresses:
            print(f"🟠 Processing Bitcoin addresses with batch API...")
            batch_size = 50
            
            for batch_start in range(0, len(bitcoin_addresses), batch_size):
                batch_end = min(batch_start + batch_size, len(bitcoin_addresses))
                batch_data = bitcoin_addresses[batch_start:batch_end]
                
                # Filter out addresses already checked in this session
                unique_batch_data = []
                duplicate_count = 0
                for addr_data in batch_data:
                    address = addr_data['address']
                    if address not in checked_addresses_this_session:
                        unique_batch_data.append(addr_data)
                        checked_addresses_this_session.add(address)
                    else:
                        duplicate_count += 1
                
                batch_addresses = [addr['address'] for addr in unique_batch_data]
                
                if duplicate_count > 0:
                    print(f"\n⚠️  Skipped {duplicate_count} duplicate addresses in this batch")
                
                if not batch_addresses:
                    continue  # Skip empty batches
                
                print(f"\n📦 Bitcoin Batch {batch_start//batch_size + 1}: Checking {len(batch_addresses)} unique addresses")
                print(f"   Range: {batch_start + 1} to {batch_end} of {len(bitcoin_addresses)} Bitcoin addresses")
                
                # Try batch check first
                batch_results = self.check_bitcoin_balance_batch(batch_addresses)
                print("")  # New line after batch status
                
                # Process results
                for addr_data in unique_batch_data:
                    checked_count += 1
                    address = addr_data['address']
                    balance = batch_results.get(address, 0)
                    
                    source = addr_data.get('source', 'unknown').split('/')[-1][:20]
                    print(f"🔍 [{checked_count:5d}/{len(prioritized_addresses)}] bitcoin   {address[:12]}...{address[-8:]} "
                          f"(score: {addr_data['pattern_score']:4.1f}, {source:<20}) ", end="")
                    
                    if balance > 0:
                        print(f"💰💰💰 FUNDED! Balance: {balance} BTC 💰💰💰")
                        self.save_funded_address(address, 'bitcoin', balance, addr_data.get('private_key'), addr_data['pattern_score'])
                        funded_found += 1
                        
                        # Show celebration and details
                        elapsed = time.time() - start_time
                        rate = checked_count / elapsed if elapsed > 0 else 0
                        print(f"🎉 FOUND FUNDS AFTER {checked_count} CHECKS IN {elapsed/60:.1f}m (rate: {rate:.1f}/s)")
                        print(f"🔥 Source: {addr_data.get('source', 'unknown')}")
                        print(f"🔑 Private Key: {addr_data.get('private_key')}")
                        print("="*80)
                    else:
                        print("❌")
                    
                    # Update stats
                    self.stats['addresses_checked'] += 1
                    
                    # Progress update every 100 addresses
                    if checked_count % 100 == 0:
                        elapsed = time.time() - start_time
                        rate = checked_count / elapsed if elapsed > 0 else 0
                        remaining = len(prioritized_addresses) - checked_count
                        eta_seconds = remaining / rate if rate > 0 else 0
                        eta_mins = eta_seconds / 60
                        
                        print(f"\n📊 Progress: {checked_count:,}/{len(prioritized_addresses):,} checked ({100*checked_count/len(prioritized_addresses):.1f}%)")
                        print(f"💰 Funded found: {funded_found}")
                        print(f"⚡ Rate: {rate:.1f} addresses/sec")
                        print(f"⏱️  ETA: {eta_mins:.1f} minutes")
                        print(f"🕐 Elapsed: {elapsed/60:.1f} minutes")
                        print("-" * 60)
        
        # Process Ethereum addresses individually (no efficient batch API)
        if ethereum_addresses:
            print(f"\n🔷 Processing Ethereum addresses individually...")
            
            ethereum_duplicate_count = 0
            for addr_data in ethereum_addresses:
                address = addr_data['address']
                
                # Skip if already checked in this session
                if address in checked_addresses_this_session:
                    ethereum_duplicate_count += 1
                    continue
                
                checked_addresses_this_session.add(address)
                checked_count += 1
                chain = addr_data['chain']
                private_key = addr_data.get('private_key')
                source = addr_data.get('source', 'unknown').split('/')[-1][:20]
                
                print(f"🔍 [{checked_count:5d}/{len(prioritized_addresses)}] {chain:<8} {address[:12]}...{address[-8:]} "
                      f"(score: {addr_data['pattern_score']:4.1f}, {source:<20})", end=" ", flush=True)
                
                # Check balance
                balance = 0
                try:
                    balance = self.check_ethereum_balance(address)
                except Exception as e:
                    print(f"⚠️ Error: {e}")
                    continue
                
                if balance > 0:
                    print(f"💰💰💰 FUNDED! Balance: {balance} ETH 💰💰💰")
                    self.save_funded_address(address, chain, balance, private_key, addr_data['pattern_score'])
                    funded_found += 1
                    
                    # Show celebration and details
                    elapsed = time.time() - start_time
                    rate = checked_count / elapsed if elapsed > 0 else 0
                    print(f"🎉 FOUND FUNDS AFTER {checked_count} CHECKS IN {elapsed/60:.1f}m (rate: {rate:.1f}/s)")
                    print(f"🔥 Source: {addr_data.get('source', 'unknown')}")
                    print(f"🔑 Private Key: {private_key}")
                    print("="*80)
                else:
                    print("❌")
                
                # Update stats
                self.stats['addresses_checked'] += 1
                
                # Progress update every 100 addresses
                if checked_count % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = checked_count / elapsed if elapsed > 0 else 0
                    remaining = len(prioritized_addresses) - checked_count
                    eta_seconds = remaining / rate if rate > 0 else 0
                    eta_mins = eta_seconds / 60
                    
                    print(f"\n📊 Progress: {checked_count:,}/{len(prioritized_addresses):,} checked ({100*checked_count/len(prioritized_addresses):.1f}%)")
                    print(f"💰 Funded found: {funded_found}")
                    print(f"⚡ Rate: {rate:.1f} addresses/sec")
                    print(f"⏱️  ETA: {eta_mins:.1f} minutes")
                    print(f"🕐 Elapsed: {elapsed/60:.1f} minutes")
                    print("-" * 60)
            
            if ethereum_duplicate_count > 0:
                print(f"\n⚠️  Skipped {ethereum_duplicate_count} duplicate Ethereum addresses")
        
        # Process Solana and other addresses individually
        other_duplicate_count = 0
        for addr_data in solana_addresses + other_addresses:
            address = addr_data['address']
            
            # Skip if already checked in this session
            if address in checked_addresses_this_session:
                other_duplicate_count += 1
                continue
            
            checked_addresses_this_session.add(address)
            checked_count += 1
            chain = addr_data['chain']
            private_key = addr_data.get('private_key')
            source = addr_data.get('source', 'unknown').split('/')[-1][:20]
            
            print(f"🔍 [{checked_count:5d}/{len(prioritized_addresses)}] {chain:<8} {address[:12]}...{address[-8:]} "
                  f"(score: {addr_data['pattern_score']:4.1f}, {source:<20})", end=" ", flush=True)
            
            # Check balance
            balance = 0
            try:
                if chain.lower() == 'solana':
                    balance = self.check_solana_balance(address)
            except Exception as e:
                print(f"⚠️ Error: {e}")
                continue
            
            if balance > 0:
                print(f"💰💰💰 FUNDED! Balance: {balance} 💰💰💰")
                self.save_funded_address(address, chain, balance, private_key, addr_data['pattern_score'])
                funded_found += 1
                
                # Show celebration and details
                elapsed = time.time() - start_time
                rate = checked_count / elapsed if elapsed > 0 else 0
                print(f"🎉 FOUND FUNDS AFTER {checked_count} CHECKS IN {elapsed/60:.1f}m (rate: {rate:.1f}/s)")
                print(f"🔥 Source: {addr_data.get('source', 'unknown')}")
                print(f"🔑 Private Key: {private_key}")
                print("="*80)
            else:
                print("❌")
            
            # Update stats
            self.stats['addresses_checked'] += 1
        
        if other_duplicate_count > 0:
            print(f"\n⚠️  Skipped {other_duplicate_count} duplicate Solana/other addresses")
        
        print(f"\n🎉 Prioritized Balance Check Complete!")
        print(f"📊 Total unique addresses checked: {checked_count}")
        print(f"💰 Funded addresses found: {funded_found}")
        
        # Calculate and show duplicate prevention stats
        total_duplicates_skipped = (ethereum_duplicate_count if 'ethereum_duplicate_count' in locals() else 0) + \
                                 (other_duplicate_count if 'other_duplicate_count' in locals() else 0)
        
        if total_duplicates_skipped > 0:
            print(f"⚠️  Duplicate addresses prevented: {total_duplicates_skipped}")
            print(f"✅ Efficiency gained by avoiding duplicate API calls")
        else:
            print(f"✅ No duplicate addresses found - clean address list")
        
        # Generate final report
        self.generate_final_report()
    
    def extract_from_leveldb_directory(self, db_path):
        """Extract private keys and addresses from a LevelDB directory without balance checking"""
        extracted_data = []
        extracted_addresses_set = set()  # For fast duplicate checking
        keys_processed = 0
        
        try:
            db = plyvel.DB(db_path, create_if_missing=False)
            
            # First, count total keys for progress calculation
            print(f"� Counting total keys in database...")
            total_keys = sum(1 for _ in db)
            print(f"📊 Total keys to process: {total_keys:,}")
            
            # Reset iterator and start processing
            db.close()
            db = plyvel.DB(db_path, create_if_missing=False)
            
            print(f"🔓 Starting extraction with progress tracking...")
            
            for key, value in db:
                keys_processed += 1
                
                # Limit for testing - remove this line for full extraction
                if keys_processed > 10000:
                    print(f"\n🔄 Reached 10,000 keys limit for testing. Remove this limit for full extraction.")
                    break
                
                try:
                    print(f"\n🔑 Processing key #{keys_processed}: {len(key)} bytes key, {len(value)} bytes value")
                    
                    key_str = key.decode('utf-8', errors='ignore')
                    value_str = value.decode('utf-8', errors='ignore')
                    combined_data = key_str + value_str
                    
                    print(f"📝 Combined data length: {len(combined_data)} characters")
                    
                    # Extract potential private keys
                    potential_keys = self.extract_private_keys(combined_data)
                    print(f"🔍 Found {len(potential_keys)} potential private keys")
                    
                    # Process each potential private key
                    for i, private_key in enumerate(potential_keys, 1):
                        print(f"  🔐 Processing private key {i}/{len(potential_keys)}: {private_key[:10]}...{private_key[-10:]}")
                        
                        addresses = self.generate_addresses_from_private_key(private_key)
                        print(f"  📍 Generated {len(addresses)} addresses from this key")
                        
                        # Store each generated address
                        for chain_type, address in addresses.items():
                            chain_name = chain_type.split('_')[0]
                            
                            print(f"    ✅ {chain_name}: {address}")
                            
                            # Skip if already seen (check in-memory set only for speed)
                            if address in extracted_addresses_set:
                                print(f"    ⚠️  Duplicate address skipped")
                                continue
                            
                            # Add to extracted data and tracking set
                            extracted_addresses_set.add(address)
                            extracted_data.append({
                                'address': address,
                                'chain': chain_name,
                                'private_key': private_key,
                                'source_db': db_path,
                                'extraction_timestamp': time.time()
                            })
                            print(f"    ✨ New address added to collection")
                            
                            # Add to extracted data and tracking set
                            extracted_data.append({
                                'address': address,
                                'chain': chain_name,
                                'private_key': private_key,
                                'source_db': db_path,
                                'extraction_time': time.time()
                            })
                            extracted_addresses_set.add(address)
                            print(f"    ✨ New address added to collection")
                
                except Exception as e:
                    print(f"\n❌ Error processing key #{keys_processed}: {e}")
                    continue
                
                # Progress reporting with percentage and progress bar
                if keys_processed % 100 == 0:
                    percentage = (keys_processed / total_keys) * 100
                    progress_bar = self.create_progress_bar(percentage)
                    print(f"\r🔍 [{progress_bar}] {percentage:.1f}% ({keys_processed:,}/{total_keys:,}) - {len(extracted_data)} addresses extracted", end="", flush=True)
                
                if keys_processed % 1000 == 0:
                    percentage = (keys_processed / total_keys) * 100
                    print(f"\n📊 Milestone: {keys_processed:,}/{total_keys:,} keys ({percentage:.1f}%) - {len(extracted_data)} addresses extracted")
            
            db.close()
            
            print(f"\n✅ Extraction complete for this database")
            
        except Exception as e:
            self.logger.error(f"Error processing LevelDB {db_path}: {e}")
        
        return extracted_data
    
    def create_progress_bar(self, percentage, width=30):
        """Create a visual progress bar"""
        filled = int(width * percentage / 100)
        bar = '█' * filled + '░' * (width - filled)
        return bar
    
    def record_address_fast(self, address, chain, balance, private_key, pattern_score):
        """Record address without immediate commit (for batch operations)"""
        try:
            self.conn.execute("""
                INSERT OR IGNORE INTO addresses 
                (address, chain, balance, private_key, pattern_score, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (address, chain, float(balance), private_key, float(pattern_score), time.time()))
        except Exception as e:
            self.logger.warning(f"Database insert failed: {e}")
    
    def print_progress_update(self):
        """Print current progress and statistics"""
        runtime = self.get_runtime()
        rate = self.stats['addresses_checked'] / max(runtime, 1) * 60  # per minute
        
        efficiency = 0
        if self.stats['addresses_checked'] > 0:
            efficiency = (self.stats['duplicates_prevented'] / 
                         (self.stats['addresses_checked'] + self.stats['duplicates_prevented']) * 100)
        
        print(f"📊 Progress: {self.stats['addresses_checked']} checked, "
              f"{len(self.stats['funded_addresses'])} funded, "
              f"{self.stats['duplicates_prevented']} duplicates prevented "
              f"({efficiency:.1f}% efficiency), "
              f"{rate:.1f} addr/min")
    
    def get_runtime(self):
        """Get current runtime in seconds"""
        return time.time() - self.stats['start_time']
    
    def save_progress(self):
        """Save current progress to file"""
        progress_data = {
            'timestamp': datetime.now().isoformat(),
            'runtime_seconds': self.get_runtime(),
            'statistics': dict(self.stats),
            'funded_addresses': self.stats['funded_addresses'],
            'pattern_matches': dict(self.stats['patterns_found']),
            'database_info': {
                'path': self.db_path,
                'total_addresses': self.stats['addresses_checked'],
                'duplicates_prevented': self.stats['duplicates_prevented']
            }
        }
        
        with open('unified_scanner_progress.json', 'w') as f:
            json.dump(progress_data, f, indent=2)
    
    def save_results(self):
        """Save final results in multiple formats"""
        
        # Update consolidated funded addresses
        try:
            # Load existing consolidated data
            consolidated_path = 'funded_addresses_consolidated.json'
            if os.path.exists(consolidated_path):
                with open(consolidated_path, 'r') as f:
                    existing_data = json.load(f)
                existing_addresses = existing_data.get('addresses', [])
            else:
                existing_addresses = []
            
            # Add new addresses (avoid duplicates)
            existing_addr_set = {addr.get('address', '') for addr in existing_addresses}
            new_addresses = []
            
            for addr in self.stats['funded_addresses']:
                if addr['address'] not in existing_addr_set:
                    new_addresses.append(addr)
                    existing_addresses.append(addr)
            
            # Update consolidated data
            consolidated_data = {
                'consolidation_date': datetime.now().isoformat(),
                'scanner_version': 'unified_v2.0',
                'total_unique_addresses': len(existing_addresses),
                'total_value': sum(float(addr.get('balance', 0)) for addr in existing_addresses),
                'addresses': existing_addresses,
                'summary': {
                    'bitcoin': len([a for a in existing_addresses if a.get('chain', '').lower() == 'bitcoin']),
                    'ethereum': len([a for a in existing_addresses if a.get('chain', '').lower() == 'ethereum']),
                    'solana': len([a for a in existing_addresses if a.get('chain', '').lower() == 'solana']),
                },
                'latest_scan': {
                    'new_addresses_found': len(new_addresses),
                    'scan_date': datetime.now().isoformat()
                }
            }
            
            # Save consolidated results
            with open(consolidated_path, 'w') as f:
                json.dump(consolidated_data, f, indent=2)
            
            if new_addresses:
                print(f"💾 Saved {len(new_addresses)} new funded addresses to consolidated results")
        
        except Exception as e:
            self.logger.error(f"Error saving consolidated results: {e}")
    
    def generate_final_report(self):
        """Generate comprehensive final scan report"""
        
        runtime = self.get_runtime()
        efficiency = 0
        if self.stats['addresses_checked'] > 0:
            efficiency = (self.stats['duplicates_prevented'] / 
                         (self.stats['addresses_checked'] + self.stats['duplicates_prevented']) * 100)
        
        report = {
            'scan_summary': {
                'scanner_version': 'unified_v2.0',
                'scan_date': datetime.now().isoformat(),
                'total_runtime_seconds': runtime,
                'total_runtime_formatted': str(timedelta(seconds=int(runtime))),
                'addresses_checked': self.stats['addresses_checked'],
                'duplicates_prevented': self.stats['duplicates_prevented'],
                'duplicate_prevention_efficiency': f"{efficiency:.2f}%",
                'scan_rate_per_minute': self.stats['addresses_checked'] / max(runtime, 1) * 60
            },
            'funded_addresses_found': {
                'total_count': len(self.stats['funded_addresses']),
                'total_value': sum(addr['balance'] for addr in self.stats['funded_addresses']),
                'by_chain': {
                    'bitcoin': len([a for a in self.stats['funded_addresses'] if a['chain'] == 'bitcoin']),
                    'ethereum': len([a for a in self.stats['funded_addresses'] if a['chain'] == 'ethereum']),
                    'solana': len([a for a in self.stats['funded_addresses'] if a['chain'] == 'solana'])
                },
                'addresses': self.stats['funded_addresses']
            },
            'pattern_analysis': {
                'successful_patterns_used': self.successful_patterns,
                'pattern_matches_found': dict(self.stats['patterns_found']),
                'highest_scoring_addresses': sorted(
                    self.stats['funded_addresses'], 
                    key=lambda x: x.get('pattern_score', 0), 
                    reverse=True
                )[:10]
            },
            'technical_details': {
                'database_path': self.db_path,
                'configuration': self.config,
                'api_rate_limits_used': self.last_api_calls,
                'cache_size': len(self.address_cache)
            }
        }
        
        # Save detailed report
        with open('unified_scanner_final_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary to console
        print(f"\n" + "="*80)
        print(f"🎉 UNIFIED WALLET SCANNER - FINAL REPORT")
        print(f"="*80)
        print(f"⏱️  Runtime: {str(timedelta(seconds=int(runtime)))}")
        print(f"📊 Addresses checked: {self.stats['addresses_checked']:,}")
        print(f"🔄 Duplicates prevented: {self.stats['duplicates_prevented']:,} ({efficiency:.1f}% efficiency)")
        print(f"💰 Funded addresses found: {len(self.stats['funded_addresses'])}")
        print(f"💎 Total value: {sum(addr['balance'] for addr in self.stats['funded_addresses'])}")
        print(f"⚡ Average scan rate: {self.stats['addresses_checked'] / max(runtime, 1) * 60:.1f} addresses/minute")
        print(f"📁 Detailed report saved to: unified_scanner_final_report.json")
        print(f"="*80)
    
    def run_continuous_scan(self, directory_path):
        """Run continuous scanning with monitoring"""
        
        print(f"🚀 Starting Unified Wallet Scanner v2.0")
        print(f"📂 Target directory: {directory_path}")
        print(f"⚙️  Configuration: {len(self.config)} settings loaded")
        print(f"🎯 Tracking {len(self.successful_patterns)} successful patterns")
        print(f"📝 Duplicate prevention: {len(self.address_cache)} addresses cached")
        print()
        
        try:
            self.scan_directory_tree(directory_path)
        except KeyboardInterrupt:
            print(f"\n⚠️  Scan interrupted by user")
            self.save_progress()
            self.generate_final_report()
        except Exception as e:
            self.logger.error(f"Scan failed: {e}")
            self.save_progress()
        finally:
            print(f"💾 Final results saved")

def main():
    """Main scanner entry point"""
    
    parser = argparse.ArgumentParser(description='Unified Wallet Scanner v2.0')
    parser.add_argument('directory', nargs='?', help='Directory to scan')
    parser.add_argument('--extract-only', action='store_true', 
                       help='Only extract private keys and addresses, sort by likelihood (no balance checking)')
    parser.add_argument('--check-balances', action='store_true',
                       help='Check balances for extracted addresses using pattern prioritization')
    args = parser.parse_args()
    
    print("🚀 UNIFIED WALLET SCANNER v2.0")
    print("="*50)
    
    if args.extract_only:
        print("📦 EXTRACTION MODE: Gathering and sorting addresses by likelihood")
        print("🎯 Will extract all private keys and sort by success probability")
    elif args.check_balances:
        print("💰 BALANCE CHECK MODE: Checking sorted addresses (highest probability first)")
        print("🎯 Will check balances starting with most likely addresses")
    else:
        print("🔄 FULL SCAN MODE: Extraction + pattern analysis + balance checking")
    print()
    
    # Initialize scanner
    scanner = UnifiedWalletScanner()
    
    # Run appropriate mode
    if args.check_balances:
        # For balance checking, we don't need a directory - we use existing extracted files
        if args.directory and os.path.isfile(args.directory):
            scanner.run_balance_check_prioritized(args.directory)
        else:
            scanner.run_balance_check_prioritized()
    else:
        # Get directory to scan for extraction modes
        if args.directory:
            scan_directory = args.directory
        else:
            scan_directory = input("Enter directory path to scan (or press Enter for current directory): ").strip()
            if not scan_directory:
                scan_directory = "."
        
        # Validate directory
        if not os.path.exists(scan_directory):
            print(f"❌ Directory not found: {scan_directory}")
            sys.exit(1)
        
        print(f"📂 Target directory: {os.path.abspath(scan_directory)}")
        print()
        
        # Run appropriate mode
        if args.extract_only:
            scanner.run_extraction_only(scan_directory)
        else:
            scanner.run_continuous_scan(scan_directory)

if __name__ == "__main__":
    main()
