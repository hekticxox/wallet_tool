#!/usr/bin/env python3
"""
MK3265GSXN Windows Drive Hunter
Advanced key extraction and wallet hunting system for Windows-based systems
Optimized for diverse file types and crypto-related applications
"""

import os
import sys
import json
import re
import hashlib
import time
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from datetime import datetime
import concurrent.futures
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'/home/admin/wallet_tool/MK3265GSXN_HUNT_LOG_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class MK3265GSXNHunter:
    def __init__(self):
        self.drive_path = "/mnt/MK3265GSXN"
        self.results_file = f"/home/admin/wallet_tool/MK3265GSXN_HUNT_RESULTS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.processed_dirs_file = "/home/admin/wallet_tool/PROCESSED_MK3265GSXN_DIRECTORIES.json"
        
        # Statistics
        self.stats = {
            'directories_processed': 0,
            'files_scanned': 0,
            'keys_extracted': 0,
            'errors': 0,
            'start_time': time.time(),
            'skipped_dirs': 0
        }
        
        # Key patterns - comprehensive set for Windows systems
        self.key_patterns = {
            'ethereum_private_key': re.compile(r'\b[0-9a-fA-F]{64}\b'),
            'bitcoin_private_key_wif': re.compile(r'\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b'),
            'bitcoin_private_key_hex': re.compile(r'\b[0-9a-fA-F]{64}\b'),
            'mnemonic_12': re.compile(r'\b(?:[a-z]+\s+){11}[a-z]+\b', re.IGNORECASE),
            'mnemonic_24': re.compile(r'\b(?:[a-z]+\s+){23}[a-z]+\b', re.IGNORECASE),
            'bitcoin_address': re.compile(r'\b[13][a-km-z-A-HJ-NP-Z1-9]{25,34}\b'),
            'ethereum_address': re.compile(r'\b0x[a-fA-F0-9]{40}\b'),
            'base58_key': re.compile(r'\b[1-9A-HJ-NP-Za-km-z]{44,88}\b'),
            'xprv_key': re.compile(r'\bxprv[a-zA-Z0-9]{107,108}\b'),
            'xpub_key': re.compile(r'\bxpub[a-zA-Z0-9]{107,108}\b'),
            'json_key': re.compile(r'"private[_-]?key"\s*:\s*"([^"]+)"', re.IGNORECASE),
            'wallet_import_format': re.compile(r'\bK[xyz][1-9A-HJ-NP-Za-km-z]{50}\b'),
            'seed_phrase': re.compile(r'seed\s*[:=]\s*["\']([^"\']+)["\']', re.IGNORECASE),
            'keystore_json': re.compile(r'\{"version":\s*3,.*"crypto":', re.IGNORECASE),
        }
        
        # File extensions to scan - Windows-focused
        self.target_extensions = {
            # Wallet files
            '.wallet', '.dat', '.json', '.key', '.keystore', '.pkcs12', '.p12',
            # Config files
            '.conf', '.config', '.cfg', '.ini', '.properties', '.yaml', '.yml',
            # Text files
            '.txt', '.log', '.bak', '.backup', '.old', '.csv', '.tsv',
            # Database files
            '.db', '.sqlite', '.sqlite3', '.ldb', '.sdb',
            # Application data
            '.bin', '.data', '.store', '.cache', '.prefs',
            # Code files (might contain hardcoded keys)
            '.py', '.js', '.php', '.java', '.cpp', '.c', '.cs', '.rb', '.go',
            # Archive files (extract if small)
            '.zip', '.rar', '.7z', '.tar', '.gz',
            # Windows-specific
            '.reg', '.pst', '.ost', '.mdb', '.accdb'
        }
        
        # Crypto-related directory patterns for Windows
        self.crypto_dir_patterns = [
            r'.*wallet.*', r'.*crypto.*', r'.*bitcoin.*', r'.*ethereum.*', r'.*coin.*',
            r'.*electrum.*', r'.*exodus.*', r'.*atomic.*', r'.*jaxx.*', r'.*trust.*',
            r'.*ledger.*', r'.*trezor.*', r'.*metamask.*', r'.*coinbase.*',
            r'.*roaming.*', r'.*appdata.*', r'.*\.bitcoin.*', r'.*\.ethereum.*',
            r'.*mining.*', r'.*blockchain.*', r'.*keys?.*', r'.*seed.*',
            r'.*backup.*', r'.*zelcore.*', r'.*binance.*', r'.*exchange.*'
        ]
        
        # Load processed directories
        self.processed_dirs = self.load_processed_dirs()
        
        # Thread-safe containers
        self.found_keys = []
        self.lock = threading.Lock()
        
        # High-priority directories (scan first)
        self.priority_dirs = [
            'users', 'user', 'documents', 'desktop', 'downloads', 'appdata',
            'roaming', 'local', 'program files', 'programdata', 'temp',
            'bitcoin', 'ethereum', 'wallet', 'crypto', 'electrum', 'exodus'
        ]

    def load_processed_dirs(self) -> Set[str]:
        """Load previously processed directories."""
        try:
            if os.path.exists(self.processed_dirs_file):
                with open(self.processed_dirs_file, 'r') as f:
                    return set(json.load(f))
        except Exception as e:
            logger.warning(f"Could not load processed directories: {e}")
        return set()

    def save_processed_dirs(self):
        """Save processed directories to file."""
        try:
            with open(self.processed_dirs_file, 'w') as f:
                json.dump(list(self.processed_dirs), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save processed directories: {e}")

    def is_crypto_related(self, path: str) -> bool:
        """Check if a path is crypto-related."""
        path_lower = path.lower()
        for pattern in self.crypto_dir_patterns:
            if re.search(pattern, path_lower):
                return True
        return False

    def calculate_priority_score(self, dir_path: str) -> int:
        """Calculate priority score for directory (higher = more important)."""
        path_lower = dir_path.lower()
        score = 0
        
        # Crypto-related directories get highest priority
        if self.is_crypto_related(dir_path):
            score += 1000
            
        # User directories are high priority
        for priority_dir in self.priority_dirs:
            if priority_dir in path_lower:
                score += 500
                break
                
        # Recently modified directories get bonus
        try:
            mtime = os.path.getmtime(dir_path)
            days_old = (time.time() - mtime) / (24 * 3600)
            if days_old < 30:  # Less than 30 days old
                score += int(100 - days_old)
        except:
            pass
            
        # Penalize very deep directories
        depth = dir_path.count(os.sep)
        if depth > 10:
            score -= (depth - 10) * 10
            
        return score

    def extract_keys_from_content(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract potential keys from file content."""
        found = []
        
        for pattern_name, pattern in self.key_patterns.items():
            matches = pattern.findall(content)
            for match in matches:
                # Extract the key value
                if isinstance(match, tuple):
                    key_value = match[0] if match[0] else match[1] if len(match) > 1 else str(match)
                else:
                    key_value = match
                    
                if key_value and len(key_value) > 10:  # Minimum key length
                    key_info = {
                        'key': key_value,
                        'type': pattern_name,
                        'file': file_path,
                        'length': len(key_value),
                        'context': content[max(0, content.find(key_value)-50):content.find(key_value)+len(key_value)+50],
                        'extracted_at': datetime.now().isoformat()
                    }
                    found.append(key_info)
        
        return found

    def scan_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Scan a single file for keys."""
        try:
            file_size = os.path.getsize(file_path)
            
            # Skip very large files (>50MB)
            if file_size > 50 * 1024 * 1024:
                return []
                
            # Try different encodings
            encodings = ['utf-8', 'ascii', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                        # Read file in chunks for large files
                        if file_size > 1024 * 1024:  # 1MB
                            content = f.read(1024 * 1024)  # Read first 1MB only
                        else:
                            content = f.read()
                    break
                except:
                    continue
            else:
                # If all text encodings fail, try binary
                try:
                    with open(file_path, 'rb') as f:
                        binary_content = f.read(min(file_size, 1024 * 1024))
                        # Try to decode as utf-8 with errors ignored
                        content = binary_content.decode('utf-8', errors='ignore')
                except:
                    return []
            
            return self.extract_keys_from_content(content, file_path)
            
        except Exception as e:
            logger.debug(f"Error scanning file {file_path}: {e}")
            return []

    def scan_directory_batch(self, directories: List[str]) -> List[Dict[str, Any]]:
        """Scan a batch of directories."""
        batch_keys = []
        
        for directory in directories:
            if directory in self.processed_dirs:
                self.stats['skipped_dirs'] += 1
                continue
                
            try:
                logger.info(f"Scanning directory: {directory}")
                dir_keys = self.scan_directory(directory)
                batch_keys.extend(dir_keys)
                
                # Mark as processed
                self.processed_dirs.add(directory)
                self.stats['directories_processed'] += 1
                
                # Save progress periodically
                if self.stats['directories_processed'] % 10 == 0:
                    self.save_processed_dirs()
                    self.save_intermediate_results(batch_keys)
                    
            except Exception as e:
                logger.error(f"Error scanning directory {directory}: {e}")
                self.stats['errors'] += 1
                
        return batch_keys

    def scan_directory(self, directory: str) -> List[Dict[str, Any]]:
        """Scan a single directory for wallet files and keys."""
        found_keys = []
        
        try:
            for root, dirs, files in os.walk(directory):
                # Skip system and temporary directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d.lower() not in 
                          ['temp', 'tmp', 'cache', 'logs', 'system volume information']]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    try:
                        # Check file extension
                        _, ext = os.path.splitext(file.lower())
                        if ext not in self.target_extensions:
                            continue
                            
                        # Scan the file
                        file_keys = self.scan_file(file_path)
                        found_keys.extend(file_keys)
                        self.stats['files_scanned'] += 1
                        
                        if len(file_keys) > 0:
                            logger.info(f"Found {len(file_keys)} keys in {file_path}")
                            
                    except Exception as e:
                        logger.debug(f"Error processing file {file_path}: {e}")
                        
        except Exception as e:
            logger.error(f"Error walking directory {directory}: {e}")
            
        return found_keys

    def get_directory_list(self) -> List[str]:
        """Get list of directories to scan, prioritized."""
        directories = []
        
        try:
            # Get all top-level directories
            items = os.listdir(self.drive_path)
            for item in items:
                item_path = os.path.join(self.drive_path, item)
                if os.path.isdir(item_path):
                    directories.append(item_path)
                    
            # Sort by priority score (highest first)
            directories.sort(key=self.calculate_priority_score, reverse=True)
            
            logger.info(f"Found {len(directories)} directories to scan")
            for i, dir_path in enumerate(directories[:10]):  # Show top 10
                score = self.calculate_priority_score(dir_path)
                logger.info(f"Priority {i+1}: {dir_path} (score: {score})")
                
        except Exception as e:
            logger.error(f"Error getting directory list: {e}")
            
        return directories

    def save_intermediate_results(self, keys: List[Dict[str, Any]]):
        """Save intermediate results."""
        try:
            with self.lock:
                # Deduplicate keys
                seen = set()
                unique_keys = []
                for key in keys:
                    key_hash = hashlib.md5(key['key'].encode()).hexdigest()
                    if key_hash not in seen:
                        seen.add(key_hash)
                        unique_keys.append(key)
                
                results = {
                    'drive': 'MK3265GSXN',
                    'scan_time': datetime.now().isoformat(),
                    'stats': self.stats.copy(),
                    'keys_found': unique_keys
                }
                
                with open(self.results_file, 'w') as f:
                    json.dump(results, f, indent=2)
                    
        except Exception as e:
            logger.error(f"Error saving intermediate results: {e}")

    def run_hunt(self):
        """Run the complete hunting process."""
        logger.info("=== MK3265GSXN Windows Drive Hunter Started ===")
        logger.info(f"Target drive: {self.drive_path}")
        
        # Verify drive exists
        if not os.path.exists(self.drive_path):
            logger.error(f"Drive not found: {self.drive_path}")
            return
            
        # Get directories to scan
        directories = self.get_directory_list()
        if not directories:
            logger.error("No directories found to scan")
            return
            
        logger.info(f"Starting scan of {len(directories)} directories")
        
        # Process directories in batches
        batch_size = 5  # Process 5 directories at a time
        all_keys = []
        
        for i in range(0, len(directories), batch_size):
            batch = directories[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} directories")
            
            batch_keys = self.scan_directory_batch(batch)
            all_keys.extend(batch_keys)
            
            # Update stats
            self.stats['keys_extracted'] = len(all_keys)
            
            # Progress update
            processed = min(i + batch_size, len(directories))
            progress = (processed / len(directories)) * 100
            logger.info(f"Progress: {processed}/{len(directories)} directories ({progress:.1f}%)")
            
        # Final save
        self.save_processed_dirs()
        self.save_intermediate_results(all_keys)
        
        # Summary
        duration = time.time() - self.stats['start_time']
        logger.info("=== Hunt Complete ===")
        logger.info(f"Directories processed: {self.stats['directories_processed']}")
        logger.info(f"Files scanned: {self.stats['files_scanned']}")
        logger.info(f"Keys extracted: {self.stats['keys_extracted']}")
        logger.info(f"Errors encountered: {self.stats['errors']}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Results saved to: {self.results_file}")
        
        return all_keys

if __name__ == "__main__":
    hunter = MK3265GSXNHunter()
    try:
        keys = hunter.run_hunt()
        print(f"\n✅ Hunt completed! Found {len(keys) if keys else 0} potential keys.")
        print(f"📁 Results saved to: {hunter.results_file}")
    except KeyboardInterrupt:
        logger.info("Hunt interrupted by user")
        print("\n⚠️ Hunt interrupted by user")
    except Exception as e:
        logger.error(f"Hunt failed: {e}")
        print(f"\n❌ Hunt failed: {e}")
        traceback.print_exc()
