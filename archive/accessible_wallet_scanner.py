#!/usr/bin/env python3
"""
Accessible Wallet Scanner
Focus on finding wallets with recoverable private keys, not just addresses
"""

import os
import json
import sqlite3
import struct
import hashlib
import base64
import re
from pathlib import Path
import tempfile
import shutil
from typing import Dict, List, Tuple, Optional
import logging

class AccessibleWalletScanner:
    """Scanner focused on finding actually accessible wallets (with private keys)"""
    
    def __init__(self):
        self.accessible_wallets = []
        self.file_stats = {
            'processed': 0,
            'accessible_found': 0,
            'encrypted_found': 0,
            'addresses_only': 0
        }
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging for the scanner"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def scan_directory(self, directory_path: str) -> Dict:
        """
        Scan directory focusing on accessible wallets (with private keys)
        """
        directory_path = Path(directory_path)
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        print(f"🔓 ACCESSIBLE WALLET SCANNER")
        print(f"📁 Scanning directory: {directory_path}")
        print(f"🎯 Focus: Wallets with recoverable private keys")
        print("="*70)
        
        # Look for specific wallet types that commonly store private keys
        self._scan_for_bitcoin_core_wallets(directory_path)
        self._scan_for_electrum_wallets(directory_path)
        self._scan_for_ethereum_keystores(directory_path)
        self._scan_for_metamask_vaults(directory_path)
        self._scan_for_browser_stored_keys(directory_path)
        self._scan_for_text_private_keys(directory_path)
        self._scan_for_mnemonic_files(directory_path)
        self._scan_for_wallet_databases(directory_path)
        
        return self._generate_accessible_report()
    
    def _scan_for_bitcoin_core_wallets(self, directory_path: Path):
        """Look for Bitcoin Core wallet.dat files"""
        print("🔍 Scanning for Bitcoin Core wallets...")
        
        wallet_files = list(directory_path.rglob("*wallet*.dat")) + list(directory_path.rglob("*wallet*.db"))
        
        for wallet_file in wallet_files:
            try:
                print(f"   📄 Analyzing: {wallet_file.name}")
                result = self._analyze_bitcoin_core_wallet(wallet_file)
                if result:
                    self.accessible_wallets.append(result)
                    self.file_stats['accessible_found'] += 1
                self.file_stats['processed'] += 1
            except Exception as e:
                self.logger.warning(f"Error analyzing {wallet_file}: {e}")
    
    def _analyze_bitcoin_core_wallet(self, wallet_file: Path) -> Optional[Dict]:
        """Analyze Bitcoin Core wallet.dat file"""
        try:
            with open(wallet_file, 'rb') as f:
                data = f.read()
            
            # Look for Berkeley DB structure
            if data[:8] == b'\x00\x00\x00\x00\x00\x00\x00\x01':
                # This looks like a Bitcoin Core wallet
                
                # Look for private keys in the wallet
                private_keys = []
                mnemonic = None
                
                # Search for WIF private keys
                wif_pattern = rb'[5KL][1-9A-HJ-NP-Za-km-z]{50,51}'
                wif_matches = re.findall(wif_pattern, data)
                
                for match in wif_matches:
                    try:
                        key_str = match.decode('utf-8')
                        private_keys.append(key_str)
                    except:
                        pass
                
                # Search for hex private keys (32 bytes)
                hex_pattern = rb'[a-fA-F0-9]{64}'
                hex_matches = re.findall(hex_pattern, data)
                
                for match in hex_matches:
                    try:
                        key_str = match.decode('utf-8')
                        if len(key_str) == 64:  # 32 bytes hex
                            private_keys.append(key_str)
                    except:
                        pass
                
                # Look for master seed
                seed_patterns = [rb'seed', rb'mnemonic', rb'master']
                for pattern in seed_patterns:
                    if pattern in data.lower():
                        # Found potential seed data
                        mnemonic = "ENCRYPTED_SEED_FOUND"
                        break
                
                if private_keys or mnemonic:
                    return {
                        'type': 'bitcoin_core_wallet',
                        'source': str(wallet_file),
                        'chain': 'bitcoin',
                        'private_keys': private_keys,
                        'mnemonic': mnemonic,
                        'accessible': len(private_keys) > 0,
                        'encrypted': mnemonic == "ENCRYPTED_SEED_FOUND" and len(private_keys) == 0,
                        'file_size': wallet_file.stat().st_size
                    }
        
        except Exception as e:
            self.logger.warning(f"Error reading Bitcoin Core wallet {wallet_file}: {e}")
        
        return None
    
    def _scan_for_electrum_wallets(self, directory_path: Path):
        """Look for Electrum wallet files"""
        print("🔍 Scanning for Electrum wallets...")
        
        # Electrum wallets are usually JSON files
        electrum_patterns = ["*electrum*", "*default_wallet*"]
        
        for pattern in electrum_patterns:
            wallet_files = list(directory_path.rglob(pattern))
            
            for wallet_file in wallet_files:
                if wallet_file.is_file():
                    try:
                        print(f"   📄 Analyzing: {wallet_file.name}")
                        result = self._analyze_electrum_wallet(wallet_file)
                        if result:
                            self.accessible_wallets.append(result)
                            self.file_stats['accessible_found'] += 1
                        self.file_stats['processed'] += 1
                    except Exception as e:
                        self.logger.warning(f"Error analyzing {wallet_file}: {e}")
    
    def _analyze_electrum_wallet(self, wallet_file: Path) -> Optional[Dict]:
        """Analyze Electrum wallet file"""
        try:
            with open(wallet_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to parse as JSON
            try:
                wallet_data = json.loads(content)
            except json.JSONDecodeError:
                # Might be encrypted
                if 'seed_version' in content or 'electrum' in content.lower():
                    return {
                        'type': 'electrum_wallet_encrypted',
                        'source': str(wallet_file),
                        'chain': 'bitcoin',
                        'private_keys': [],
                        'mnemonic': None,
                        'accessible': False,
                        'encrypted': True,
                        'file_size': wallet_file.stat().st_size
                    }
                return None
            
            # Extract accessible data
            private_keys = []
            mnemonic = None
            addresses = []
            
            # Look for seed (mnemonic)
            if 'seed' in wallet_data:
                seed = wallet_data['seed']
                if isinstance(seed, str) and len(seed.split()) >= 12:
                    mnemonic = seed
            
            # Look for keypairs
            if 'keypairs' in wallet_data:
                keypairs = wallet_data['keypairs']
                for addr, key_data in keypairs.items():
                    if isinstance(key_data, list) and len(key_data) >= 1:
                        private_keys.append(key_data[0])  # Private key
                        addresses.append(addr)
            
            # Look for keystore
            if 'keystore' in wallet_data:
                keystore = wallet_data['keystore']
                if isinstance(keystore, dict):
                    if 'seed' in keystore:
                        mnemonic = keystore['seed']
                    if 'xprv' in keystore:
                        private_keys.append(keystore['xprv'])  # Master private key
            
            if private_keys or mnemonic:
                return {
                    'type': 'electrum_wallet',
                    'source': str(wallet_file),
                    'chain': 'bitcoin',
                    'private_keys': private_keys,
                    'mnemonic': mnemonic,
                    'addresses': addresses,
                    'accessible': True,
                    'encrypted': False,
                    'file_size': wallet_file.stat().st_size
                }
        
        except Exception as e:
            self.logger.warning(f"Error reading Electrum wallet {wallet_file}: {e}")
        
        return None
    
    def _scan_for_ethereum_keystores(self, directory_path: Path):
        """Look for Ethereum keystore files"""
        print("🔍 Scanning for Ethereum keystores...")
        
        # Ethereum keystores are JSON files with specific structure
        json_files = list(directory_path.rglob("*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if it looks like an Ethereum keystore
                if any(keyword in content.lower() for keyword in ['keystore', 'crypto', 'ciphertext', 'kdf']):
                    print(f"   📄 Analyzing: {json_file.name}")
                    result = self._analyze_ethereum_keystore(json_file, content)
                    if result:
                        self.accessible_wallets.append(result)
                        if result['accessible']:
                            self.file_stats['accessible_found'] += 1
                        else:
                            self.file_stats['encrypted_found'] += 1
                    self.file_stats['processed'] += 1
            except Exception as e:
                self.logger.warning(f"Error analyzing {json_file}: {e}")
    
    def _analyze_ethereum_keystore(self, keystore_file: Path, content: str) -> Optional[Dict]:
        """Analyze Ethereum keystore file"""
        try:
            keystore_data = json.loads(content)
            
            # Check if it's a valid keystore
            if not all(key in keystore_data for key in ['crypto', 'address']):
                return None
            
            address = keystore_data.get('address', '')
            if not address.startswith('0x'):
                address = '0x' + address
            
            # This is an encrypted keystore - would need password to decrypt
            return {
                'type': 'ethereum_keystore',
                'source': str(keystore_file),
                'chain': 'ethereum',
                'private_keys': [],
                'mnemonic': None,
                'addresses': [address],
                'accessible': False,  # Encrypted, needs password
                'encrypted': True,
                'file_size': keystore_file.stat().st_size,
                'encryption_params': {
                    'cipher': keystore_data['crypto'].get('cipher', 'unknown'),
                    'kdf': keystore_data['crypto'].get('kdf', 'unknown')
                }
            }
        
        except Exception as e:
            self.logger.warning(f"Error parsing Ethereum keystore {keystore_file}: {e}")
        
        return None
    
    def _scan_for_metamask_vaults(self, directory_path: Path):
        """Look for MetaMask vault files"""
        print("🔍 Scanning for MetaMask vaults...")
        
        # Look for MetaMask storage files
        metamask_patterns = ["*MetaMask*", "*metamask*"]
        
        for pattern in metamask_patterns:
            metamask_dirs = list(directory_path.rglob(pattern))
            
            for metamask_dir in metamask_dirs:
                if metamask_dir.is_dir():
                    try:
                        print(f"   📁 Analyzing MetaMask directory: {metamask_dir.name}")
                        results = self._analyze_metamask_directory(metamask_dir)
                        for result in results:
                            self.accessible_wallets.append(result)
                            if result['accessible']:
                                self.file_stats['accessible_found'] += 1
                            else:
                                self.file_stats['encrypted_found'] += 1
                        self.file_stats['processed'] += len(results)
                    except Exception as e:
                        self.logger.warning(f"Error analyzing MetaMask directory {metamask_dir}: {e}")
    
    def _analyze_metamask_directory(self, metamask_dir: Path) -> List[Dict]:
        """Analyze MetaMask directory for vault files"""
        results = []
        
        try:
            # Look for LevelDB files that might contain vaults
            for file_path in metamask_dir.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in ['.log', '.ldb']:
                    try:
                        with open(file_path, 'rb') as f:
                            data = f.read()
                        
                        # Look for vault data patterns
                        vault_patterns = [b'vault', b'mnemonic', b'seed', b'privateKey']
                        
                        for pattern in vault_patterns:
                            if pattern in data.lower():
                                # Found potential vault data
                                text_data = data.decode('utf-8', errors='ignore')
                                
                                # Look for JSON structures that might be vaults
                                vault_matches = re.findall(r'\{[^{}]*vault[^{}]*\}', text_data, re.IGNORECASE)
                                
                                for vault_match in vault_matches:
                                    try:
                                        vault_data = json.loads(vault_match)
                                        if 'vault' in vault_data or 'data' in vault_data:
                                            results.append({
                                                'type': 'metamask_vault',
                                                'source': str(file_path),
                                                'chain': 'ethereum',
                                                'private_keys': [],
                                                'mnemonic': None,
                                                'accessible': False,  # Encrypted
                                                'encrypted': True,
                                                'file_size': file_path.stat().st_size,
                                                'vault_data': vault_data
                                            })
                                    except:
                                        pass
                                break
                    
                    except Exception as e:
                        self.logger.warning(f"Error reading MetaMask file {file_path}: {e}")
        
        except Exception as e:
            self.logger.warning(f"Error analyzing MetaMask directory {metamask_dir}: {e}")
        
        return results
    
    def _scan_for_browser_stored_keys(self, directory_path: Path):
        """Look for browser-stored wallet data"""
        print("🔍 Scanning for browser-stored wallet data...")
        
        # Look for browser databases that might contain wallet data
        browser_patterns = [
            "*Chrome*", "*Firefox*", "*Edge*", "*Brave*",
            "*Login Data*", "*Web Data*", "*Preferences*"
        ]
        
        for pattern in browser_patterns:
            browser_files = list(directory_path.rglob(pattern))
            
            for browser_file in browser_files:
                if browser_file.is_file() and browser_file.suffix.lower() in ['.db', '.sqlite', '.sqlite3', '.json']:
                    try:
                        print(f"   📄 Analyzing browser file: {browser_file.name}")
                        result = self._analyze_browser_file(browser_file)
                        if result:
                            self.accessible_wallets.append(result)
                            if result['accessible']:
                                self.file_stats['accessible_found'] += 1
                            else:
                                self.file_stats['addresses_only'] += 1
                        self.file_stats['processed'] += 1
                    except Exception as e:
                        self.logger.warning(f"Error analyzing browser file {browser_file}: {e}")
    
    def _analyze_browser_file(self, browser_file: Path) -> Optional[Dict]:
        """Analyze browser file for wallet data"""
        try:
            if browser_file.suffix.lower() in ['.db', '.sqlite', '.sqlite3']:
                return self._analyze_browser_database(browser_file)
            elif browser_file.suffix.lower() == '.json':
                return self._analyze_browser_json(browser_file)
        except Exception as e:
            self.logger.warning(f"Error analyzing browser file {browser_file}: {e}")
        
        return None
    
    def _analyze_browser_database(self, db_file: Path) -> Optional[Dict]:
        """Analyze browser SQLite database"""
        try:
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            wallet_data = {
                'addresses': [],
                'private_keys': [],
                'mnemonics': []
            }
            
            for table_name, in tables:
                try:
                    # Get all data from the table
                    cursor.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()
                    
                    # Get column names
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    for row in rows:
                        for i, value in enumerate(row):
                            if value and isinstance(value, str):
                                # Check for wallet data
                                if self._is_bitcoin_address(value) or self._is_ethereum_address(value):
                                    wallet_data['addresses'].append(value)
                                elif self._is_private_key(value):
                                    wallet_data['private_keys'].append(value)
                                elif self._is_mnemonic(value):
                                    wallet_data['mnemonics'].append(value)
                
                except Exception as e:
                    self.logger.warning(f"Error processing table {table_name}: {e}")
            
            conn.close()
            
            # If we found any wallet data, return it
            if wallet_data['addresses'] or wallet_data['private_keys'] or wallet_data['mnemonics']:
                return {
                    'type': 'browser_database',
                    'source': str(db_file),
                    'chain': 'multi',
                    'private_keys': wallet_data['private_keys'],
                    'mnemonic': wallet_data['mnemonics'][0] if wallet_data['mnemonics'] else None,
                    'addresses': wallet_data['addresses'],
                    'accessible': len(wallet_data['private_keys']) > 0 or len(wallet_data['mnemonics']) > 0,
                    'encrypted': False,
                    'file_size': db_file.stat().st_size
                }
        
        except Exception as e:
            self.logger.warning(f"Error reading browser database {db_file}: {e}")
        
        return None
    
    def _analyze_browser_json(self, json_file: Path) -> Optional[Dict]:
        """Analyze browser JSON file"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for wallet-related data
            addresses = []
            private_keys = []
            mnemonics = []
            
            # Find potential addresses and keys
            bitcoin_addresses = re.findall(r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-z0-9]{39,59}', content)
            ethereum_addresses = re.findall(r'0x[a-fA-F0-9]{40}', content)
            hex_keys = re.findall(r'[a-fA-F0-9]{64}', content)
            wif_keys = re.findall(r'[5KL][1-9A-HJ-NP-Za-km-z]{50,51}', content)
            
            addresses.extend(bitcoin_addresses + ethereum_addresses)
            private_keys.extend(hex_keys + wif_keys)
            
            # Look for mnemonic phrases
            words = content.split()
            for i in range(len(words) - 11):  # At least 12 words
                phrase = ' '.join(words[i:i+12])
                if self._is_mnemonic(phrase):
                    mnemonics.append(phrase)
            
            if addresses or private_keys or mnemonics:
                return {
                    'type': 'browser_json',
                    'source': str(json_file),
                    'chain': 'multi',
                    'private_keys': private_keys,
                    'mnemonic': mnemonics[0] if mnemonics else None,
                    'addresses': addresses,
                    'accessible': len(private_keys) > 0 or len(mnemonics) > 0,
                    'encrypted': False,
                    'file_size': json_file.stat().st_size
                }
        
        except Exception as e:
            self.logger.warning(f"Error reading browser JSON {json_file}: {e}")
        
        return None
    
    def _scan_for_text_private_keys(self, directory_path: Path):
        """Look for plain text private keys"""
        print("🔍 Scanning for text files with private keys...")
        
        text_files = list(directory_path.rglob("*.txt")) + list(directory_path.rglob("*.key"))
        
        for text_file in text_files:
            try:
                if text_file.stat().st_size < 1024 * 1024:  # Only files < 1MB
                    print(f"   📄 Analyzing: {text_file.name}")
                    result = self._analyze_text_file(text_file)
                    if result:
                        self.accessible_wallets.append(result)
                        self.file_stats['accessible_found'] += 1
                    self.file_stats['processed'] += 1
            except Exception as e:
                self.logger.warning(f"Error analyzing text file {text_file}: {e}")
    
    def _analyze_text_file(self, text_file: Path) -> Optional[Dict]:
        """Analyze text file for private keys"""
        try:
            with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            private_keys = []
            addresses = []
            mnemonics = []
            
            # Look for private keys
            wif_keys = re.findall(r'[5KL][1-9A-HJ-NP-Za-km-z]{50,51}', content)
            hex_keys = re.findall(r'\b[a-fA-F0-9]{64}\b', content)
            
            private_keys.extend(wif_keys + hex_keys)
            
            # Look for addresses
            bitcoin_addresses = re.findall(r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-z0-9]{39,59}', content)
            ethereum_addresses = re.findall(r'0x[a-fA-F0-9]{40}', content)
            
            addresses.extend(bitcoin_addresses + ethereum_addresses)
            
            # Look for mnemonic phrases
            lines = content.split('\n')
            for line in lines:
                words = line.strip().split()
                if 12 <= len(words) <= 24:
                    if self._is_mnemonic(' '.join(words)):
                        mnemonics.append(' '.join(words))
            
            if private_keys or mnemonics:
                return {
                    'type': 'text_file',
                    'source': str(text_file),
                    'chain': 'multi',
                    'private_keys': private_keys,
                    'mnemonic': mnemonics[0] if mnemonics else None,
                    'addresses': addresses,
                    'accessible': True,
                    'encrypted': False,
                    'file_size': text_file.stat().st_size
                }
        
        except Exception as e:
            self.logger.warning(f"Error reading text file {text_file}: {e}")
        
        return None
    
    def _scan_for_mnemonic_files(self, directory_path: Path):
        """Look specifically for mnemonic/seed files"""
        print("🔍 Scanning for mnemonic/seed files...")
        
        seed_patterns = ["*seed*", "*mnemonic*", "*recovery*", "*backup*"]
        
        for pattern in seed_patterns:
            seed_files = list(directory_path.rglob(pattern))
            
            for seed_file in seed_files:
                if seed_file.is_file():
                    try:
                        print(f"   📄 Analyzing: {seed_file.name}")
                        result = self._analyze_seed_file(seed_file)
                        if result:
                            self.accessible_wallets.append(result)
                            self.file_stats['accessible_found'] += 1
                        self.file_stats['processed'] += 1
                    except Exception as e:
                        self.logger.warning(f"Error analyzing seed file {seed_file}: {e}")
    
    def _analyze_seed_file(self, seed_file: Path) -> Optional[Dict]:
        """Analyze potential seed/mnemonic file"""
        try:
            with open(seed_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().strip()
            
            # Check if content looks like a mnemonic phrase
            if self._is_mnemonic(content):
                return {
                    'type': 'mnemonic_file',
                    'source': str(seed_file),
                    'chain': 'universal',
                    'private_keys': [],
                    'mnemonic': content,
                    'addresses': [],
                    'accessible': True,
                    'encrypted': False,
                    'file_size': seed_file.stat().st_size
                }
        
        except Exception as e:
            self.logger.warning(f"Error reading seed file {seed_file}: {e}")
        
        return None
    
    def _scan_for_wallet_databases(self, directory_path: Path):
        """Look for database files that might contain wallet data"""
        print("🔍 Scanning for wallet databases...")
        
        db_files = list(directory_path.rglob("*.db")) + list(directory_path.rglob("*.sqlite")) + list(directory_path.rglob("*.sqlite3"))
        
        for db_file in db_files:
            if 'wallet' in db_file.name.lower() or 'bitcoin' in db_file.name.lower():
                try:
                    print(f"   📄 Analyzing: {db_file.name}")
                    result = self._analyze_wallet_database(db_file)
                    if result:
                        self.accessible_wallets.append(result)
                        if result['accessible']:
                            self.file_stats['accessible_found'] += 1
                        else:
                            self.file_stats['encrypted_found'] += 1
                    self.file_stats['processed'] += 1
                except Exception as e:
                    self.logger.warning(f"Error analyzing wallet database {db_file}: {e}")
    
    def _analyze_wallet_database(self, db_file: Path) -> Optional[Dict]:
        """Analyze wallet-specific database"""
        try:
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            private_keys = []
            addresses = []
            encrypted_data = []
            
            for table_name, in tables:
                try:
                    cursor.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()
                    
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    for row in rows:
                        row_dict = dict(zip(columns, row))
                        
                        for key, value in row_dict.items():
                            if value and isinstance(value, str):
                                if self._is_private_key(value):
                                    private_keys.append(value)
                                elif self._is_bitcoin_address(value) or self._is_ethereum_address(value):
                                    addresses.append(value)
                            elif value and isinstance(value, bytes):
                                # Might be encrypted private key
                                encrypted_data.append(base64.b64encode(value).decode())
                
                except Exception as e:
                    self.logger.warning(f"Error processing table {table_name}: {e}")
            
            conn.close()
            
            if private_keys or addresses or encrypted_data:
                return {
                    'type': 'wallet_database',
                    'source': str(db_file),
                    'chain': 'multi',
                    'private_keys': private_keys,
                    'mnemonic': None,
                    'addresses': addresses,
                    'accessible': len(private_keys) > 0,
                    'encrypted': len(encrypted_data) > 0 and len(private_keys) == 0,
                    'file_size': db_file.stat().st_size,
                    'encrypted_data': encrypted_data[:5]  # Store first 5 for analysis
                }
        
        except Exception as e:
            self.logger.warning(f"Error reading wallet database {db_file}: {e}")
        
        return None
    
    def _is_bitcoin_address(self, value: str) -> bool:
        """Check if string is a valid Bitcoin address"""
        if not isinstance(value, str):
            return False
        
        patterns = [
            r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$',
            r'^bc1[a-z0-9]{39,59}$'
        ]
        
        return any(re.match(pattern, value) for pattern in patterns)
    
    def _is_ethereum_address(self, value: str) -> bool:
        """Check if string is a valid Ethereum address"""
        if not isinstance(value, str):
            return False
        
        return re.match(r'^0x[a-fA-F0-9]{40}$', value) is not None
    
    def _is_private_key(self, value: str) -> bool:
        """Check if string looks like a private key"""
        if not isinstance(value, str):
            return False
        
        # WIF format (Bitcoin)
        if re.match(r'^[5KL][1-9A-HJ-NP-Za-km-z]{50,51}$', value):
            return True
        
        # Hex private key (32 bytes = 64 hex chars)
        if re.match(r'^[a-fA-F0-9]{64}$', value):
            return True
        
        return False
    
    def _is_mnemonic(self, value: str) -> bool:
        """Check if string looks like a mnemonic phrase"""
        if not isinstance(value, str):
            return False
        
        words = value.split()
        
        # Must be 12, 15, 18, 21, or 24 words
        if len(words) not in [12, 15, 18, 21, 24]:
            return False
        
        # All words should be alphabetic and at least 3 characters
        if not all(word.isalpha() and len(word) >= 3 for word in words):
            return False
        
        return True
    
    def _generate_accessible_report(self) -> Dict:
        """Generate report focusing on accessible wallets"""
        
        # Sort by accessibility (accessible first)
        accessible_wallets = [w for w in self.accessible_wallets if w['accessible']]
        encrypted_wallets = [w for w in self.accessible_wallets if not w['accessible'] and w['encrypted']]
        address_only_wallets = [w for w in self.accessible_wallets if not w['accessible'] and not w['encrypted']]
        
        print("\n" + "="*70)
        print("🔓 ACCESSIBLE WALLET SCANNER - RESULTS")
        print("="*70)
        print(f"📁 Files processed: {self.file_stats['processed']}")
        print(f"🔓 Accessible wallets found: {len(accessible_wallets)}")
        print(f"🔒 Encrypted wallets found: {len(encrypted_wallets)}")
        print(f"📍 Address-only entries: {len(address_only_wallets)}")
        print()
        
        if accessible_wallets:
            print("🎉 ACCESSIBLE WALLETS (with private keys/mnemonics):")
            for i, wallet in enumerate(accessible_wallets, 1):
                print(f"   {i}. {wallet['type'].upper()} - {wallet['chain'].upper()}")
                print(f"      Source: {wallet['source']}")
                print(f"      Private Keys: {len(wallet['private_keys'])}")
                if wallet['mnemonic']:
                    print(f"      Mnemonic: {'✓ Found' if wallet['mnemonic'] else '✗ None'}")
                print(f"      Addresses: {len(wallet.get('addresses', []))}")
                print()
        
        if encrypted_wallets:
            print("🔒 ENCRYPTED WALLETS (need passwords to access):")
            for i, wallet in enumerate(encrypted_wallets, 1):
                print(f"   {i}. {wallet['type'].upper()} - {wallet['chain'].upper()}")
                print(f"      Source: {wallet['source']}")
                print(f"      Status: Password required for decryption")
                print()
        
        # Save results
        results = {
            'accessible_wallets': accessible_wallets,
            'encrypted_wallets': encrypted_wallets,
            'address_only_wallets': address_only_wallets,
            'statistics': self.file_stats
        }
        
        with open('accessible_wallets_report.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Results saved to: accessible_wallets_report.json")
        print("="*70)
        
        return results

def main():
    """Main function for command line usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("🔓 ACCESSIBLE WALLET SCANNER")
        print("="*40)
        print()
        print("Usage: python accessible_wallet_scanner.py <directory_path>")
        print()
        print("This scanner focuses on finding wallets with recoverable private keys,")
        print("not just addresses. It will identify:")
        print("• Unencrypted private keys")
        print("• Mnemonic phrases")
        print("• Encrypted wallets that need passwords")
        print()
        sys.exit(1)
    
    directory_path = sys.argv[1]
    
    # Validate directory
    dir_path = Path(directory_path)
    if not dir_path.exists():
        print(f"❌ Directory does not exist: {directory_path}")
        sys.exit(1)
    
    if not dir_path.is_dir():
        print(f"❌ Path is not a directory: {directory_path}")
        sys.exit(1)
    
    scanner = AccessibleWalletScanner()
    
    try:
        results = scanner.scan_directory(directory_path)
        
        accessible_count = len(results.get('accessible_wallets', []))
        if accessible_count > 0:
            print(f"\n✅ Found {accessible_count} accessible wallet(s)!")
            print("🎯 These wallets can be used immediately (no password needed)")
        else:
            print(f"\n⚠️  No immediately accessible wallets found.")
            print("🔒 Some encrypted wallets were found that might be recoverable with passwords.")
        
        return results
    except Exception as e:
        print(f"\n❌ Scan failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
