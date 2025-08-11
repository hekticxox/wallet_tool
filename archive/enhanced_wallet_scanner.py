#!/usr/bin/env python3
"""
Enhanced Multi-Format Wallet Scanner
Detects and processes various wallet file formats to extract addresses and private keys
"""

import os
import json
import sqlite3
import struct
import hashlib
import base64
import re
from pathlib import Path
import zipfile
import tarfile
import tempfile
import shutil
from typing import Dict, List, Tuple, Optional
import logging

class MultiFormatWalletScanner:
    """Enhanced scanner that can detect and process multiple wallet formats"""
    
    def __init__(self):
        self.extracted_data = []
        self.file_stats = {
            'leveldb': 0,
            'sqlite': 0,
            'json': 0,
            'text': 0,
            'csv': 0,
            'binary': 0,
            'encrypted': 0,
            'archives': 0,
            'unknown': 0
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
        Comprehensive scan of directory for all wallet formats
        """
        directory_path = Path(directory_path)
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        print(f"🔍 ENHANCED MULTI-FORMAT WALLET SCANNER")
        print(f"📁 Scanning directory: {directory_path}")
        print(f"🎯 Detecting: LevelDB, SQLite, JSON, CSV, Text, Binary, Archives")
        print("="*70)
        
        # First, scan for all files and categorize them
        all_files = self._get_all_files(directory_path)
        categorized_files = self._categorize_files(all_files)
        
        # Process each category
        self._process_archives(categorized_files.get('archives', []))
        self._process_leveldb(categorized_files.get('leveldb', []))
        self._process_sqlite(categorized_files.get('sqlite', []))
        self._process_json(categorized_files.get('json', []))
        self._process_csv(categorized_files.get('csv', []))
        self._process_text(categorized_files.get('text', []))
        self._process_binary(categorized_files.get('binary', []))
        
        # Generate summary report
        return self._generate_report()
    
    def _get_all_files(self, directory_path: Path) -> List[Path]:
        """Recursively get all files in directory"""
        all_files = []
        try:
            for root, dirs, files in os.walk(directory_path):
                # Limit the number of files to process to avoid hanging
                if len(all_files) > 10000:  # Stop at 10k files
                    print(f"⚠️  Limiting scan to first 10,000 files to avoid hanging...")
                    break
                
                for file in files:
                    try:
                        file_path = Path(root) / Path(file)
                        if file_path.is_file() and file_path.exists():
                            all_files.append(file_path)
                    except (OSError, ValueError) as e:
                        self.logger.warning(f"Skipping problematic file: {file} - {e}")
                        continue
        except PermissionError as e:
            self.logger.warning(f"Permission denied: {e}")
        except Exception as e:
            self.logger.warning(f"Error walking directory: {e}")
        
        print(f"📊 Found {len(all_files)} total files")
        return all_files
    
    def _categorize_files(self, files: List[Path]) -> Dict[str, List[Path]]:
        """Categorize files by their likely wallet format"""
        categories = {
            'leveldb': [],
            'sqlite': [],
            'json': [],
            'csv': [],
            'text': [],
            'binary': [],
            'archives': [],
            'unknown': []
        }
        
        for file_path in files:
            try:
                category = self._detect_file_type(file_path)
                categories[category].append(file_path)
                self.file_stats[category] += 1
            except Exception as e:
                self.logger.warning(f"Error categorizing {file_path}: {e}")
                categories['unknown'].append(file_path)
                self.file_stats['unknown'] += 1
        
        # Print categorization summary
        print("\n📋 File Categorization:")
        for category, file_list in categories.items():
            if file_list:
                print(f"   {category.upper()}: {len(file_list)} files")
        print()
        
        return categories
    
    def _detect_file_type(self, file_path: Path) -> str:
        """Detect wallet file type based on extension, content, and structure"""
        file_name = file_path.name.lower()
        suffix = file_path.suffix.lower()
        
        # Check for archives first
        if suffix in ['.zip', '.tar', '.tar.gz', '.tgz', '.rar', '.7z']:
            return 'archives'
        
        # Check for known wallet file patterns
        if any(pattern in file_name for pattern in [
            'wallet', 'bitcoin', 'electrum', 'exodus', 'atomic', 
            'coinomi', 'trust', 'metamask', 'private', 'seed',
            'keys', 'account', 'keystore'
        ]):
            # Further analyze based on extension
            if suffix in ['.json', '.jsonl']:
                return 'json'
            elif suffix in ['.db', '.sqlite', '.sqlite3', '.dat']:
                return 'sqlite'
            elif suffix in ['.csv', '.tsv']:
                return 'csv'
            elif suffix in ['.txt', '.key', '.priv', '.seed']:
                return 'text'
        
        # Check by file extension
        if suffix in ['.json', '.jsonl']:
            return 'json'
        elif suffix in ['.db', '.sqlite', '.sqlite3']:
            return 'sqlite'
        elif suffix in ['.csv', '.tsv']:
            return 'csv'
        elif suffix in ['.txt', '.log', '.key', '.priv', '.seed', '.mnemonic']:
            return 'text'
        
        # Check for LevelDB structure
        if file_name in ['manifest-000001', 'current'] or file_name.startswith('log'):
            parent_has_leveldb = any(f.name in ['manifest-000001', 'current'] for f in file_path.parent.iterdir())
            if parent_has_leveldb:
                return 'leveldb'
        
        # Check file content for magic bytes or patterns
        try:
            with open(file_path, 'rb') as f:
                header = f.read(64)
                
                # SQLite magic bytes
                if header.startswith(b'SQLite format 3'):
                    return 'sqlite'
                
                # JSON content
                if header.strip().startswith(b'{') or header.strip().startswith(b'['):
                    return 'json'
                
                # Bitcoin Core wallet.dat magic
                if b'\x00\x00\x00\x01' in header or b'wallet' in header:
                    return 'binary'
                
                # Check for text-like content
                try:
                    text_content = header.decode('utf-8', errors='ignore')
                    if any(pattern in text_content.lower() for pattern in [
                        'private', 'seed', 'mnemonic', 'address', 'bitcoin', 'ethereum'
                    ]):
                        return 'text'
                except:
                    pass
        
        except (IOError, OSError):
            pass
        
        # If file is small and might contain keys
        try:
            if file_path.stat().st_size < 10000:  # Less than 10KB
                return 'text'
            else:
                return 'binary'
        except:
            return 'unknown'
    
    def _process_archives(self, archive_files: List[Path]):
        """Extract and process archive files"""
        if not archive_files:
            return
        
        print(f"📦 Processing {len(archive_files)} archive files...")
        
        for archive_path in archive_files:
            try:
                temp_dir = tempfile.mkdtemp()
                extracted = False
                
                # Try different extraction methods
                if archive_path.suffix.lower() == '.zip':
                    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                        extracted = True
                
                elif archive_path.suffix.lower() in ['.tar', '.tar.gz', '.tgz']:
                    with tarfile.open(archive_path, 'r:*') as tar_ref:
                        tar_ref.extractall(temp_dir)
                        extracted = True
                
                if extracted:
                    print(f"   📂 Extracted {archive_path.name}")
                    # Recursively scan extracted contents
                    sub_result = self.scan_directory(temp_dir)
                    # Add source info to extracted data
                    for item in sub_result.get('extracted_data', []):
                        item['source'] = f"{archive_path.name}/{item.get('source', '')}"
                        self.extracted_data.append(item)
                
                # Cleanup
                shutil.rmtree(temp_dir, ignore_errors=True)
                
            except Exception as e:
                self.logger.warning(f"Failed to extract {archive_path}: {e}")
    
    def _process_leveldb(self, leveldb_files: List[Path]):
        """Process LevelDB wallet files (Bitcoin Core, etc.)"""
        if not leveldb_files:
            return
        
        print(f"🗄️  Processing {len(leveldb_files)} LevelDB files...")
        
        # Group files by directory (LevelDB stores data across multiple files)
        directories = set(f.parent for f in leveldb_files)
        
        for db_dir in directories:
            try:
                # Look for wallet-related keys
                manifest_file = db_dir / 'MANIFEST-000001'
                current_file = db_dir / 'CURRENT'
                
                if manifest_file.exists() or current_file.exists():
                    print(f"   📁 Processing LevelDB: {db_dir.name}")
                    self._extract_from_leveldb_dir(db_dir)
            
            except Exception as e:
                self.logger.warning(f"Error processing LevelDB {db_dir}: {e}")
    
    def _extract_from_leveldb_dir(self, db_dir: Path):
        """Extract data from LevelDB directory"""
        try:
            # Read all .log and .ldb files for wallet data
            for file_path in db_dir.iterdir():
                if file_path.suffix.lower() in ['.log', '.ldb']:
                    self._scan_leveldb_file(file_path)
        
        except Exception as e:
            self.logger.warning(f"Error extracting from LevelDB {db_dir}: {e}")
    
    def _scan_leveldb_file(self, file_path: Path):
        """Scan individual LevelDB file for wallet data"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
                
                # Look for Bitcoin addresses (1, 3, bc1 prefixes)
                bitcoin_pattern = rb'[13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-z0-9]{39,59}'
                addresses = re.findall(bitcoin_pattern, data)
                
                for addr in addresses:
                    try:
                        address_str = addr.decode('utf-8')
                        self.extracted_data.append({
                            'address': address_str,
                            'chain': 'bitcoin',
                            'source': f"leveldb/{file_path.name}",
                            'type': 'address'
                        })
                    except:
                        pass
                
                # Look for private keys (WIF format)
                wif_pattern = rb'[5KL][1-9A-HJ-NP-Za-km-z]{50,51}'
                private_keys = re.findall(wif_pattern, data)
                
                for pk in private_keys:
                    try:
                        pk_str = pk.decode('utf-8')
                        self.extracted_data.append({
                            'private_key': pk_str,
                            'chain': 'bitcoin',
                            'source': f"leveldb/{file_path.name}",
                            'type': 'private_key'
                        })
                    except:
                        pass
        
        except Exception as e:
            self.logger.warning(f"Error scanning LevelDB file {file_path}: {e}")
    
    def _process_sqlite(self, sqlite_files: List[Path]):
        """Process SQLite wallet databases"""
        if not sqlite_files:
            return
        
        print(f"🗃️  Processing {len(sqlite_files)} SQLite files...")
        
        for db_path in sqlite_files:
            try:
                print(f"   📄 Processing: {db_path.name}")
                self._extract_from_sqlite(db_path)
            except Exception as e:
                self.logger.warning(f"Error processing SQLite {db_path}: {e}")
    
    def _extract_from_sqlite(self, db_path: Path):
        """Extract wallet data from SQLite database"""
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            for table_name, in tables:
                try:
                    # Get table schema
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    # Look for wallet-related columns
                    wallet_columns = [col for col in columns if any(keyword in col.lower() for keyword in [
                        'address', 'private', 'public', 'key', 'seed', 'mnemonic', 'wallet'
                    ])]
                    
                    if wallet_columns:
                        # Extract data from this table
                        cursor.execute(f"SELECT * FROM {table_name}")
                        rows = cursor.fetchall()
                        
                        for row in rows:
                            row_dict = dict(zip(columns, row))
                            self._extract_wallet_data_from_row(row_dict, f"sqlite/{db_path.name}/{table_name}")
                
                except Exception as e:
                    self.logger.warning(f"Error processing table {table_name}: {e}")
            
            conn.close()
        
        except Exception as e:
            self.logger.warning(f"Error connecting to SQLite {db_path}: {e}")
    
    def _extract_wallet_data_from_row(self, row_dict: Dict, source: str):
        """Extract wallet data from database row"""
        for key, value in row_dict.items():
            if value and isinstance(value, str):
                # Check for Bitcoin addresses
                if self._is_bitcoin_address(value):
                    self.extracted_data.append({
                        'address': value,
                        'chain': 'bitcoin',
                        'source': source,
                        'type': 'address'
                    })
                
                # Check for Ethereum addresses
                elif self._is_ethereum_address(value):
                    self.extracted_data.append({
                        'address': value,
                        'chain': 'ethereum',
                        'source': source,
                        'type': 'address'
                    })
                
                # Check for private keys
                elif self._is_private_key(value):
                    chain = 'bitcoin' if len(value) == 51 or len(value) == 52 else 'ethereum'
                    self.extracted_data.append({
                        'private_key': value,
                        'chain': chain,
                        'source': source,
                        'type': 'private_key'
                    })
    
    def _process_json(self, json_files: List[Path]):
        """Process JSON wallet files (Ethereum keystores, etc.)"""
        if not json_files:
            return
        
        print(f"📋 Processing {len(json_files)} JSON files...")
        
        for json_path in json_files:
            try:
                print(f"   📄 Processing: {json_path.name}")
                self._extract_from_json(json_path)
            except Exception as e:
                self.logger.warning(f"Error processing JSON {json_path}: {e}")
    
    def _extract_from_json(self, json_path: Path):
        """Extract wallet data from JSON file"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, dict):
                self._extract_from_json_dict(data, f"json/{json_path.name}")
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    if isinstance(item, dict):
                        self._extract_from_json_dict(item, f"json/{json_path.name}[{i}]")
        
        except Exception as e:
            self.logger.warning(f"Error parsing JSON {json_path}: {e}")
    
    def _extract_from_json_dict(self, data: Dict, source: str):
        """Extract wallet data from JSON dictionary"""
        def recursive_extract(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    if isinstance(value, str):
                        # Check for addresses and keys
                        if self._is_bitcoin_address(value):
                            self.extracted_data.append({
                                'address': value,
                                'chain': 'bitcoin',
                                'source': f"{source}/{current_path}",
                                'type': 'address'
                            })
                        elif self._is_ethereum_address(value):
                            self.extracted_data.append({
                                'address': value,
                                'chain': 'ethereum',
                                'source': f"{source}/{current_path}",
                                'type': 'address'
                            })
                        elif self._is_private_key(value):
                            chain = 'bitcoin' if len(value) == 51 or len(value) == 52 else 'ethereum'
                            self.extracted_data.append({
                                'private_key': value,
                                'chain': chain,
                                'source': f"{source}/{current_path}",
                                'type': 'private_key'
                            })
                    else:
                        recursive_extract(value, current_path)
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    recursive_extract(item, f"{path}[{i}]")
        
        recursive_extract(data)
    
    def _process_csv(self, csv_files: List[Path]):
        """Process CSV files that might contain wallet data"""
        if not csv_files:
            return
        
        print(f"📊 Processing {len(csv_files)} CSV files...")
        
        for csv_path in csv_files:
            try:
                print(f"   📄 Processing: {csv_path.name}")
                self._extract_from_csv(csv_path)
            except Exception as e:
                self.logger.warning(f"Error processing CSV {csv_path}: {e}")
    
    def _extract_from_csv(self, csv_path: Path):
        """Extract wallet data from CSV file"""
        try:
            import csv
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                # Try to detect delimiter
                sample = f.read(1024)
                f.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(f, delimiter=delimiter)
                
                for row_num, row in enumerate(reader):
                    for column, value in row.items():
                        if value and isinstance(value, str):
                            if self._is_bitcoin_address(value):
                                self.extracted_data.append({
                                    'address': value,
                                    'chain': 'bitcoin',
                                    'source': f"csv/{csv_path.name}/row{row_num}/{column}",
                                    'type': 'address'
                                })
                            elif self._is_ethereum_address(value):
                                self.extracted_data.append({
                                    'address': value,
                                    'chain': 'ethereum',
                                    'source': f"csv/{csv_path.name}/row{row_num}/{column}",
                                    'type': 'address'
                                })
                            elif self._is_private_key(value):
                                chain = 'bitcoin' if len(value) == 51 or len(value) == 52 else 'ethereum'
                                self.extracted_data.append({
                                    'private_key': value,
                                    'chain': chain,
                                    'source': f"csv/{csv_path.name}/row{row_num}/{column}",
                                    'type': 'private_key'
                                })
        
        except Exception as e:
            self.logger.warning(f"Error parsing CSV {csv_path}: {e}")
    
    def _process_text(self, text_files: List[Path]):
        """Process text files that might contain wallet data"""
        if not text_files:
            return
        
        print(f"📝 Processing {len(text_files)} text files...")
        
        for text_path in text_files:
            try:
                print(f"   📄 Processing: {text_path.name}")
                self._extract_from_text(text_path)
            except Exception as e:
                self.logger.warning(f"Error processing text {text_path}: {e}")
    
    def _extract_from_text(self, text_path: Path):
        """Extract wallet data from text file"""
        try:
            with open(text_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Split into lines and words for analysis
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines):
                words = line.split()
                
                for word in words:
                    word = word.strip('",\'()[]{}')  # Remove common delimiters
                    
                    if self._is_bitcoin_address(word):
                        self.extracted_data.append({
                            'address': word,
                            'chain': 'bitcoin',
                            'source': f"text/{text_path.name}/line{line_num}",
                            'type': 'address'
                        })
                    elif self._is_ethereum_address(word):
                        self.extracted_data.append({
                            'address': word,
                            'chain': 'ethereum',
                            'source': f"text/{text_path.name}/line{line_num}",
                            'type': 'address'
                        })
                    elif self._is_private_key(word):
                        chain = 'bitcoin' if len(word) == 51 or len(word) == 52 else 'ethereum'
                        self.extracted_data.append({
                            'private_key': word,
                            'chain': chain,
                            'source': f"text/{text_path.name}/line{line_num}",
                            'type': 'private_key'
                        })
                
                # Also look for mnemonic phrases (12-24 words)
                line_words = line.lower().split()
                if 12 <= len(line_words) <= 24:
                    # Simple check for mnemonic-like content
                    if all(len(word) >= 3 and word.isalpha() for word in line_words):
                        self.extracted_data.append({
                            'mnemonic': line.strip(),
                            'chain': 'universal',
                            'source': f"text/{text_path.name}/line{line_num}",
                            'type': 'mnemonic'
                        })
        
        except Exception as e:
            self.logger.warning(f"Error reading text file {text_path}: {e}")
    
    def _process_binary(self, binary_files: List[Path]):
        """Process binary files that might contain wallet data"""
        if not binary_files:
            return
        
        print(f"🔢 Processing {len(binary_files)} binary files...")
        
        for binary_path in binary_files:
            try:
                # Only process smaller binary files to avoid memory issues
                if binary_path.stat().st_size < 50 * 1024 * 1024:  # 50MB limit
                    print(f"   📄 Processing: {binary_path.name}")
                    self._extract_from_binary(binary_path)
            except Exception as e:
                self.logger.warning(f"Error processing binary {binary_path}: {e}")
    
    def _extract_from_binary(self, binary_path: Path):
        """Extract wallet data from binary file"""
        try:
            with open(binary_path, 'rb') as f:
                data = f.read()
            
            # Convert to string and look for patterns
            try:
                text_content = data.decode('utf-8', errors='ignore')
                
                # Look for Bitcoin addresses
                bitcoin_pattern = r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-z0-9]{39,59}'
                bitcoin_addresses = re.findall(bitcoin_pattern, text_content)
                
                for addr in bitcoin_addresses:
                    self.extracted_data.append({
                        'address': addr,
                        'chain': 'bitcoin',
                        'source': f"binary/{binary_path.name}",
                        'type': 'address'
                    })
                
                # Look for Ethereum addresses
                ethereum_pattern = r'0x[a-fA-F0-9]{40}'
                ethereum_addresses = re.findall(ethereum_pattern, text_content)
                
                for addr in ethereum_addresses:
                    self.extracted_data.append({
                        'address': addr,
                        'chain': 'ethereum',
                        'source': f"binary/{binary_path.name}",
                        'type': 'address'
                    })
                
                # Look for private keys
                wif_pattern = r'[5KL][1-9A-HJ-NP-Za-km-z]{50,51}'
                private_keys = re.findall(wif_pattern, text_content)
                
                for pk in private_keys:
                    self.extracted_data.append({
                        'private_key': pk,
                        'chain': 'bitcoin',
                        'source': f"binary/{binary_path.name}",
                        'type': 'private_key'
                    })
            
            except Exception as e:
                self.logger.warning(f"Error extracting text from binary {binary_path}: {e}")
        
        except Exception as e:
            self.logger.warning(f"Error reading binary file {binary_path}: {e}")
    
    def _is_bitcoin_address(self, value: str) -> bool:
        """Check if string is a valid Bitcoin address"""
        if not isinstance(value, str):
            return False
        
        # Bitcoin address patterns
        patterns = [
            r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$',  # Legacy and P2SH
            r'^bc1[a-z0-9]{39,59}$'                 # Bech32
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
        
        # Compressed WIF
        if len(value) == 52 and value[0] in ['K', 'L']:
            return True
        
        return False
    
    def _calculate_likelihood_score(self, item: Dict) -> float:
        """Calculate likelihood score for having funds (0-100, higher = more likely)"""
        score = 0.0
        
        # Base scores by item type
        item_type = item.get('type', '').lower()
        if item_type == 'private_key':
            score += 50.0  # Private keys are very valuable
        elif item_type == 'mnemonic':
            score += 45.0  # Mnemonic phrases are very valuable
        elif item_type == 'address':
            score += 20.0  # Addresses are less likely to have funds without keys
        
        # Bonus for different chains
        chain = item.get('chain', '').lower()
        if chain == 'bitcoin':
            score += 15.0  # Bitcoin addresses often have higher value
        elif chain == 'ethereum':
            score += 12.0  # Ethereum addresses also valuable
        elif chain == 'universal':
            score += 20.0  # Universal (mnemonic) can access multiple chains
        
        # Bonus based on source file patterns (wallet-related files more likely)
        source = item.get('source', '').lower()
        if any(pattern in source for pattern in [
            'wallet', 'bitcoin', 'electrum', 'exodus', 'atomic',
            'coinomi', 'trust', 'metamask', 'keystore', 'private'
        ]):
            score += 15.0
        
        # Bonus for specific file types that commonly contain active wallets
        if 'json' in source and ('keystore' in source or 'wallet' in source):
            score += 10.0  # Ethereum keystores
        elif 'leveldb' in source:
            score += 20.0  # Bitcoin Core wallet files
        elif 'sqlite' in source and 'wallet' in source:
            score += 15.0  # Wallet database files
        
        # Pattern analysis bonuses
        if item_type == 'address':
            address = item.get('address', '')
            
            # Bitcoin address pattern bonuses
            if chain == 'bitcoin':
                if address.startswith('bc1'):
                    score += 8.0   # Bech32 addresses (newer, more likely active)
                elif address.startswith('3'):
                    score += 6.0   # P2SH addresses (multisig, often active)
                elif address.startswith('1'):
                    score += 4.0   # Legacy addresses
            
            # Ethereum address pattern bonuses
            elif chain == 'ethereum':
                if address.startswith('0x'):
                    score += 5.0
        
        # Private key format bonuses
        elif item_type == 'private_key':
            private_key = item.get('private_key', '')
            
            if len(private_key) == 64:  # Raw hex format
                score += 5.0
            elif len(private_key) in [51, 52]:  # WIF format
                score += 10.0  # WIF is more commonly used format
        
        # File location bonuses (some locations more likely to have active wallets)
        if any(location in source for location in [
            'desktop', 'documents', 'wallet', 'bitcoin', 'crypto'
        ]):
            score += 8.0
        
        # Penalize very common/template sources that are less likely to have funds
        if any(pattern in source for pattern in [
            'test', 'example', 'sample', 'demo', 'template'
        ]):
            score -= 20.0
        
        # Ensure score stays within bounds
        return max(0.0, min(100.0, score))
    
    def _generate_report(self) -> Dict:
        """Generate comprehensive report of extraction results"""
        
        # Deduplicate extracted data
        unique_data = []
        seen = set()
        
        for item in self.extracted_data:
            # Create a unique key for deduplication
            key_fields = ['address', 'private_key', 'mnemonic']
            key = tuple(item.get(field, '') for field in key_fields)
            
            if key not in seen:
                seen.add(key)
                # Calculate likelihood score for sorting
                item['likelihood_score'] = self._calculate_likelihood_score(item)
                unique_data.append(item)
        
        # Sort by likelihood score (highest first - most likely to have funds)
        unique_data.sort(key=lambda x: x.get('likelihood_score', 0), reverse=True)
        
        # Generate statistics
        stats = {
            'total_files_scanned': sum(self.file_stats.values()),
            'files_by_type': self.file_stats.copy(),
            'total_extracted_items': len(unique_data),
            'items_by_type': {},
            'items_by_chain': {}
        }
        
        # Count by type and chain
        for item in unique_data:
            item_type = item.get('type', 'unknown')
            chain = item.get('chain', 'unknown')
            
            stats['items_by_type'][item_type] = stats['items_by_type'].get(item_type, 0) + 1
            stats['items_by_chain'][chain] = stats['items_by_chain'].get(chain, 0) + 1
        
        # Generate final report
        print("\n" + "="*70)
        print("📊 ENHANCED WALLET SCANNER - FINAL REPORT")
        print("="*70)
        print(f"📁 Total files scanned: {stats['total_files_scanned']}")
        print(f"🎯 Total wallet items extracted: {stats['total_extracted_items']}")
        print()
        
        print("📋 Files by type:")
        for file_type, count in stats['files_by_type'].items():
            if count > 0:
                print(f"   {file_type.upper()}: {count} files")
        print()
        
        print("🔍 Extracted items by type:")
        for item_type, count in stats['items_by_type'].items():
            print(f"   {item_type.upper()}: {count} items")
        print()
        
        print("⛓️  Extracted items by blockchain:")
        for chain, count in stats['items_by_chain'].items():
            print(f"   {chain.upper()}: {count} items")
        print()
        
        # Show top 10 most promising items
        if unique_data:
            print("🏆 TOP 10 MOST PROMISING WALLET ITEMS (sorted by likelihood):")
            for i, item in enumerate(unique_data[:10], 1):
                item_type = item.get('type', 'unknown')
                chain = item.get('chain', 'unknown')
                score = item.get('likelihood_score', 0)
                source = item.get('source', 'unknown')
                
                # Show preview of the item
                if item_type == 'address':
                    preview = item.get('address', '')[:15] + "..." + item.get('address', '')[-10:]
                elif item_type == 'private_key':
                    preview = item.get('private_key', '')[:10] + "...[PRIVATE_KEY]"
                elif item_type == 'mnemonic':
                    words = item.get('mnemonic', '').split()
                    preview = f"{words[0] if words else ''}...{words[-1] if len(words) > 1 else ''} [{len(words)} words]"
                else:
                    preview = str(item)[:30] + "..."
                
                print(f"   {i:2d}. [{score:5.1f}] {chain.upper():<8} {item_type.upper():<12} {preview}")
                print(f"       Source: {source}")
            print()
        
        # Save detailed results to file
        output_file = 'enhanced_wallet_extraction_results.json'
        result_data = {
            'statistics': stats,
            'extracted_data': unique_data
        }
        
        with open(output_file, 'w') as f:
            json.dump(result_data, f, indent=2)
        
        # Save a sorted summary file for easy review
        summary_file = 'wallet_items_sorted_by_likelihood.json'
        summary_data = []
        
        for item in unique_data:
            summary_item = {
                'likelihood_score': item.get('likelihood_score', 0),
                'type': item.get('type'),
                'chain': item.get('chain'),
                'source': item.get('source'),
            }
            
            # Add the actual data (address/key/mnemonic)
            if 'address' in item:
                summary_item['address'] = item['address']
            if 'private_key' in item:
                summary_item['private_key'] = item['private_key']
            if 'mnemonic' in item:
                summary_item['mnemonic'] = item['mnemonic']
            
            summary_data.append(summary_item)
        
        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2)
        
        print(f"💾 Detailed results saved to: {output_file}")
        print(f"📊 Sorted summary saved to: {summary_file}")
        print("="*70)
        
        return result_data

def main():
    """Main function for command line usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("🔍 ENHANCED MULTI-FORMAT WALLET SCANNER")
        print("="*50)
        print()
        print("Usage: python enhanced_wallet_scanner.py <directory_path>")
        print()
        print("Examples:")
        print(f"   python enhanced_wallet_scanner.py {Path.home()}/Downloads")
        print(f"   python enhanced_wallet_scanner.py {Path.home()}/Desktop")
        print(f"   python enhanced_wallet_scanner.py /tmp")
        print()
        print("Or use the interactive version:")
        print("   python scan_directory.py")
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
    
    print(f"🎯 Scanning directory: {directory_path}")
    print(f"📊 This may take a while for large directories...")
    print()
    
    scanner = MultiFormatWalletScanner()
    
    try:
        results = scanner.scan_directory(directory_path)
        print(f"\n✅ Scan completed successfully!")
        return results
    except Exception as e:
        print(f"\n❌ Scan failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
