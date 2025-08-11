#!/usr/bin/env python3
"""
Unified Wallet Scanner - Complete All-in-One Solution
Combines extraction, deduplication, pattern analysis, balance checking, and monitoring
Version 2.0 - Consolidated from all previous scanners
"""

import os
import json
import time
import sqlite3
import hashlib
import threading
import logging
import requests
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
        
        # Pattern analysis from successful finds (from your previous results)
        self.successful_patterns = [
            '0x9Ef2',  # Found with balance: 5.03e-16
            '0x5238',  # Found with balance: 1.60e-17
            '0x9E0F',  # Found with balance: 1.20e-17
        ]
        
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
                "bitcoin_apis": ["https://blockstream.info/api", "https://mempool.space/api"],
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
            print(f"⚠️  Cache loading error: {e}")
    
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
    
    def calculate_pattern_score(self, address, private_key=None):
        """Advanced pattern scoring based on successful finds"""
        score = 0
        
        # High priority: matches successful patterns
        for pattern in self.successful_patterns:
            if pattern.lower() in address.lower():
                score += 10
                self.stats['patterns_found'][pattern] += 1
        
        # Medium priority: interesting address characteristics
        if address:
            # Not obviously generated (avoid all zeros/sequential)
            if not address.endswith('0000') and not address.endswith('1111'):
                score += 2
            
            # Has mixed characters (not all same)
            unique_chars = len(set(address.lower()))
            if unique_chars > len(address) * 0.3:  # At least 30% unique characters
                score += 3
            
            # Starts with patterns that had success
            if address.lower().startswith('0x9'):
                score += 5
            elif address.lower().startswith('0x5'):
                score += 4
        
        # Private key analysis
        if private_key:
            # Avoid obviously weak keys
            if private_key.count('0') < len(private_key) * 0.7:  # Less than 70% zeros
                score += 3
            
            # Look for entropy indicators
            if any(char in private_key.lower() for char in 'abcdef'):
                score += 2
            
            # Avoid sequential patterns
            if '123' not in private_key and 'abc' not in private_key.lower():
                score += 1
        
        return min(score, 25)  # Cap at 25 for reasonable distribution
    
    def check_bitcoin_balance(self, address):
        """Enhanced Bitcoin balance checking with fallback APIs"""
        
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_api_calls.get('bitcoin', 0)
        min_interval = 1.0 / self.config.get('rate_limits', {}).get('bitcoin', 10)
        
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        
        # Try multiple Bitcoin APIs for reliability
        apis = self.config.get('bitcoin_apis', ['https://blockstream.info/api'])
        
        for api_base in apis:
            try:
                url = f"{api_base}/address/{address}"
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Different API response formats
                    if 'chain_stats' in data:
                        # Blockstream format
                        balance_sats = data['chain_stats'].get('funded_txo_sum', 0)
                    elif 'final_balance' in data:
                        # Blockchain.info format
                        balance_sats = data.get('final_balance', 0)
                    else:
                        # Generic format
                        balance_sats = data.get('balance', 0)
                    
                    balance_btc = balance_sats / 100000000  # Convert satoshis to BTC
                    
                    self.last_api_calls['bitcoin'] = time.time()
                    return balance_btc
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Bitcoin API {api_base} failed: {e}")
                continue
            except Exception as e:
                self.logger.warning(f"Bitcoin parsing error for {api_base}: {e}")
                continue
        
        return 0
    
    def check_ethereum_balance(self, address):
        """Enhanced Ethereum balance checking"""
        
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_api_calls.get('etherscan', 0)
        min_interval = 1.0 / self.config.get('rate_limits', {}).get('etherscan', 5)
        
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        
        api_key = self.config.get('etherscan_api_key')
        if not api_key or api_key == "YourApiKeyToken":
            return 0
        
        try:
            url = "https://api.etherscan.io/api"
            params = {
                'module': 'account',
                'action': 'balance',
                'address': address,
                'tag': 'latest',
                'apikey': api_key
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == '1':
                    balance_wei = int(data.get('result', 0))
                    balance_eth = balance_wei / (10**18)  # Convert Wei to ETH
                    
                    self.last_api_calls['etherscan'] = time.time()
                    return balance_eth
                else:
                    self.logger.warning(f"Etherscan API error: {data.get('message')}")
            
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Ethereum API request failed: {e}")
        except Exception as e:
            self.logger.warning(f"Ethereum parsing error: {e}")
        
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
            if chain.lower() == 'bitcoin':
                balance = self.check_bitcoin_balance(address)
            elif chain.lower() == 'ethereum':
                balance = self.check_ethereum_balance(address)
            elif chain.lower() == 'solana':
                balance = self.check_solana_balance(address)
            else:
                self.logger.warning(f"Unknown chain type: {chain}")
        
        except Exception as e:
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
                
                # Progress reporting
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
    
    print("🚀 UNIFIED WALLET SCANNER v2.0")
    print("="*50)
    print("Combines extraction, deduplication, pattern analysis, and balance checking")
    print()
    
    # Initialize scanner
    scanner = UnifiedWalletScanner()
    
    # Get directory to scan
    import sys
    if len(sys.argv) > 1:
        scan_directory = sys.argv[1]
    else:
        # Default to scanning current directory tree
        scan_directory = input("Enter directory path to scan (or press Enter for current directory): ").strip()
        if not scan_directory:
            scan_directory = "."
    
    # Validate directory
    if not os.path.exists(scan_directory):
        print(f"❌ Directory not found: {scan_directory}")
        sys.exit(1)
    
    print(f"📂 Scanning directory: {os.path.abspath(scan_directory)}")
    print()
    
    # Start scanning
    scanner.run_continuous_scan(scan_directory)

if __name__ == "__main__":
    main()
