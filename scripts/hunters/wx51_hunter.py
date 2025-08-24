#!/usr/bin/env python3
"""
WX51A40D1621 Windows System Hunter
Advanced wallet extraction and recovery tool for mounted Windows drive
Based on our successful deep_net607_hunter.py methodology
"""

import os
import re
import json
import hashlib
import binascii
import threading
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import requests

class WX51Hunter:
    def __init__(self):
        self.base_dir = "/mnt/WX51A40D1621"  # Direct mounted access
        self.results_file = f"WX51_HUNT_RESULTS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.processed_dirs_file = "PROCESSED_WX51_DIRECTORIES.json"
        self.unique_keys = set()
        self.key_sources = defaultdict(list)
        self.total_files_scanned = 0
        self.total_keys_extracted = 0
        self.funded_wallets = []
        
        # Enhanced patterns for key detection
        self.key_patterns = {
            'eth_private_key': re.compile(r'\b[a-fA-F0-9]{64}\b'),
            'bitcoin_wif': re.compile(r'\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b'),
            'bitcoin_hex': re.compile(r'\b[a-fA-F0-9]{64}\b'),
            'mnemonic': re.compile(r'\b(?:[a-z]+\s+){11,23}[a-z]+\b'),
            'base58_key': re.compile(r'\b[1-9A-HJ-NP-Za-km-z]{44,88}\b'),
        }
        
        # High-value file patterns
        self.target_files = [
            r'.*wallet.*\.dat$',
            r'.*\.key$',
            r'.*\.keystore$',
            r'.*\.json$',
            r'.*privkey.*',
            r'.*seed.*\.txt$',
            r'.*backup.*\.txt$',
            r'.*recovery.*\.txt$',
            r'.*\.wallet$',
            r'.*bitcoin.*\.conf$',
            r'.*ethereum.*\.json$',
        ]
        
        # API endpoints for balance checking
        self.apis = {
            'ethereum': [
                'https://api.etherscan.io/api?module=account&action=balance&address={}&tag=latest&apikey=YourApiKeyToken',
                'https://api.blockcypher.com/v1/eth/main/addrs/{}/balance'
            ],
            'bitcoin': [
                'https://api.blockcypher.com/v1/btc/main/addrs/{}/balance',
                'https://blockstream.info/api/address/{}'
            ]
        }

    def load_processed_directories(self):
        """Load list of already processed directories"""
        if os.path.exists(self.processed_dirs_file):
            with open(self.processed_dirs_file, 'r') as f:
                return set(json.load(f))
        return set()

    def save_processed_directories(self, processed_dirs):
        """Save list of processed directories"""
        with open(self.processed_dirs_file, 'w') as f:
            json.dump(list(processed_dirs), f, indent=2)

    def scan_directory_structure(self):
        """Scan the mounted Windows drive structure"""
        print(f"\n🔍 Scanning WX51A40D1621 directory structure...")
        
        interesting_dirs = []
        user_dirs = []
        
        try:
            # Look for user directories
            docs_and_settings = os.path.join(self.base_dir, "Documents and Settings")
            if os.path.exists(docs_and_settings):
                for user_dir in os.listdir(docs_and_settings):
                    user_path = os.path.join(docs_and_settings, user_dir)
                    if os.path.isdir(user_path):
                        user_dirs.append(user_path)
                        
            # Look for Program Files directories
            program_files = os.path.join(self.base_dir, "Program Files")
            if os.path.exists(program_files):
                interesting_dirs.append(program_files)
                
            # Look for the hash-named directory (likely system/user data)
            for item in os.listdir(self.base_dir):
                item_path = os.path.join(self.base_dir, item)
                if os.path.isdir(item_path) and len(item) > 10:  # Hash-like directory
                    interesting_dirs.append(item_path)
                    
        except PermissionError as e:
            print(f"⚠️ Permission error accessing directory: {e}")
            
        return interesting_dirs, user_dirs

    def extract_keys_from_file(self, file_path):
        """Extract potential private keys from a file"""
        keys_found = []
        
        try:
            # Try different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252', 'ascii']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                # If text reading fails, try binary
                with open(file_path, 'rb') as f:
                    content = f.read().decode('utf-8', errors='ignore')
            
            # Extract using patterns
            for key_type, pattern in self.key_patterns.items():
                matches = pattern.findall(content)
                for match in matches:
                    if self.validate_key_format(match, key_type):
                        keys_found.append({
                            'key': match,
                            'type': key_type,
                            'source': file_path,
                            'confidence': self.calculate_confidence(match, key_type, file_path)
                        })
                        
        except Exception as e:
            print(f"⚠️ Error reading {file_path}: {e}")
            
        return keys_found

    def validate_key_format(self, key, key_type):
        """Validate if extracted string is likely a valid private key"""
        if key_type == 'eth_private_key':
            return len(key) == 64 and all(c in '0123456789abcdefABCDEF' for c in key)
        elif key_type == 'bitcoin_wif':
            return len(key) in [51, 52] and key[0] in '5KL'
        elif key_type == 'bitcoin_hex':
            return len(key) == 64 and all(c in '0123456789abcdefABCDEF' for c in key)
        elif key_type == 'mnemonic':
            words = key.split()
            return 12 <= len(words) <= 24
        return True

    def calculate_confidence(self, key, key_type, file_path):
        """Calculate confidence score for extracted key"""
        confidence = 0.5  # Base confidence
        
        # File path indicators
        wallet_indicators = ['wallet', 'key', 'seed', 'backup', 'private', 'secret']
        for indicator in wallet_indicators:
            if indicator.lower() in file_path.lower():
                confidence += 0.2
                
        # Key type specific scoring
        if key_type == 'mnemonic':
            confidence += 0.3
        elif key_type == 'bitcoin_wif':
            confidence += 0.2
        elif key_type == 'eth_private_key':
            confidence += 0.1
            
        return min(confidence, 1.0)

    def hunt_directory(self, directory, max_files=1000):
        """Hunt for wallet data in a specific directory"""
        print(f"\n🔍 Hunting in: {directory}")
        
        files_scanned = 0
        keys_found = []
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if files_scanned >= max_files:
                        break
                        
                    file_path = os.path.join(root, file)
                    
                    # Check if file matches target patterns
                    should_scan = False
                    for pattern in self.target_files:
                        if re.match(pattern, file, re.IGNORECASE):
                            should_scan = True
                            break
                    
                    # Always scan small text files
                    if not should_scan:
                        try:
                            if os.path.getsize(file_path) < 100000:  # Under 100KB
                                if file.endswith(('.txt', '.log', '.cfg', '.conf', '.json')):
                                    should_scan = True
                        except OSError:
                            continue
                    
                    if should_scan:
                        extracted_keys = self.extract_keys_from_file(file_path)
                        keys_found.extend(extracted_keys)
                        files_scanned += 1
                        
                        if files_scanned % 100 == 0:
                            print(f"   📄 Scanned {files_scanned} files, found {len(keys_found)} potential keys")
                            
                if files_scanned >= max_files:
                    break
                    
        except Exception as e:
            print(f"⚠️ Error hunting directory {directory}: {e}")
            
        self.total_files_scanned += files_scanned
        return keys_found

    def deduplicate_and_score(self, all_keys):
        """Deduplicate keys and score by likelihood"""
        print(f"\n🔧 Deduplicating and scoring {len(all_keys)} keys...")
        
        unique_keys = {}
        
        for key_data in all_keys:
            key_hash = hashlib.sha256(key_data['key'].encode()).hexdigest()
            
            if key_hash not in unique_keys:
                unique_keys[key_hash] = key_data
            else:
                # Keep the one with higher confidence
                if key_data['confidence'] > unique_keys[key_hash]['confidence']:
                    unique_keys[key_hash] = key_data
        
        # Sort by confidence score
        sorted_keys = sorted(unique_keys.values(), key=lambda x: x['confidence'], reverse=True)
        
        print(f"   ✅ Deduplicated to {len(sorted_keys)} unique keys")
        return sorted_keys

    def check_balance_sample(self, keys, sample_size=50):
        """Check balance for a sample of the most promising keys"""
        print(f"\n💰 Checking balances for top {min(sample_size, len(keys))} keys...")
        
        funded_count = 0
        sample_keys = keys[:sample_size]
        
        for i, key_data in enumerate(sample_keys):
            try:
                # Generate addresses for different networks
                addresses = self.generate_addresses(key_data['key'], key_data['type'])
                
                for network, address in addresses.items():
                    if address:
                        balance = self.check_address_balance(address, network)
                        if balance > 0:
                            print(f"   💎 FUNDED WALLET FOUND!")
                            print(f"      Network: {network}")
                            print(f"      Address: {address}")
                            print(f"      Balance: {balance}")
                            print(f"      Key: {key_data['key']}")
                            print(f"      Source: {key_data['source']}")
                            
                            self.funded_wallets.append({
                                'network': network,
                                'address': address,
                                'balance': balance,
                                'key': key_data['key'],
                                'source': key_data['source'],
                                'confidence': key_data['confidence']
                            })
                            funded_count += 1
                
                if (i + 1) % 10 == 0:
                    print(f"   📊 Checked {i + 1}/{len(sample_keys)} keys, found {funded_count} funded")
                    
            except Exception as e:
                print(f"   ⚠️ Error checking key {i}: {e}")
                continue
                
        return funded_count

    def generate_addresses(self, key, key_type):
        """Generate addresses from private key for different networks"""
        addresses = {'ethereum': None, 'bitcoin': None}
        
        try:
            if key_type in ['eth_private_key', 'bitcoin_hex'] and len(key) == 64:
                # Try to generate Ethereum address
                try:
                    from eth_keys import keys
                    private_key = keys.PrivateKey(bytes.fromhex(key))
                    addresses['ethereum'] = private_key.public_key.to_checksum_address()
                except:
                    pass
                
                # Try to generate Bitcoin address
                try:
                    import hashlib
                    import base58
                    
                    # Generate Bitcoin address from hex private key
                    private_key_bytes = bytes.fromhex(key)
                    # This is a simplified version - full implementation would require secp256k1
                    pass
                except:
                    pass
                    
        except Exception as e:
            print(f"⚠️ Error generating addresses: {e}")
            
        return addresses

    def check_address_balance(self, address, network):
        """Check balance for a specific address"""
        try:
            if network == 'ethereum':
                url = f"https://api.blockcypher.com/v1/eth/main/addrs/{address}/balance"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return data.get('balance', 0) / 1e18  # Convert from wei
                    
            elif network == 'bitcoin':
                url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return data.get('balance', 0) / 1e8  # Convert from satoshi
                    
        except Exception as e:
            print(f"⚠️ Error checking balance for {address}: {e}")
            
        return 0

    def save_results(self, keys):
        """Save hunt results to file"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'source_directory': self.base_dir,
            'total_files_scanned': self.total_files_scanned,
            'total_keys_extracted': len(keys),
            'funded_wallets': self.funded_wallets,
            'top_keys': keys[:100],  # Save top 100 keys
            'statistics': {
                'by_type': {},
                'by_confidence': {},
                'funded_count': len(self.funded_wallets)
            }
        }
        
        # Calculate statistics
        for key_data in keys:
            key_type = key_data['type']
            results['statistics']['by_type'][key_type] = results['statistics']['by_type'].get(key_type, 0) + 1
            
        with open(self.results_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        print(f"\n💾 Results saved to: {self.results_file}")

    def run_hunt(self, batch_size=5):
        """Main hunting function"""
        print(f"\n🚀 Starting WX51A40D1621 Hunt - {datetime.now()}")
        print(f"📁 Target: {self.base_dir}")
        
        # Scan directory structure
        interesting_dirs, user_dirs = self.scan_directory_structure()
        
        print(f"\n📊 Found {len(interesting_dirs)} interesting directories")
        print(f"📊 Found {len(user_dirs)} user directories")
        
        # Load processed directories
        processed_dirs = self.load_processed_directories()
        
        all_directories = interesting_dirs + user_dirs
        unprocessed_dirs = [d for d in all_directories if d not in processed_dirs]
        
        print(f"📊 {len(processed_dirs)} directories already processed")
        print(f"📊 {len(unprocessed_dirs)} directories remaining")
        
        if not unprocessed_dirs:
            print("✅ All directories already processed!")
            return
        
        # Process directories in batches
        all_keys = []
        batch_dirs = unprocessed_dirs[:batch_size]
        
        print(f"\n🔍 Processing next {len(batch_dirs)} directories:")
        
        for directory in batch_dirs:
            print(f"\n   📁 {directory}")
            keys = self.hunt_directory(directory)
            all_keys.extend(keys)
            processed_dirs.add(directory)
            
        # Save processed directories
        self.save_processed_directories(processed_dirs)
        
        if all_keys:
            # Deduplicate and score
            unique_keys = self.deduplicate_and_score(all_keys)
            
            # Check balances for most promising keys
            funded_count = self.check_balance_sample(unique_keys)
            
            # Save results
            self.save_results(unique_keys)
            
            print(f"\n🎯 HUNT SUMMARY:")
            print(f"   📄 Files scanned: {self.total_files_scanned}")
            print(f"   🔑 Keys extracted: {len(unique_keys)}")
            print(f"   💎 Funded wallets: {funded_count}")
            print(f"   📁 Directories processed: {len(batch_dirs)}")
            print(f"   📁 Directories remaining: {len(unprocessed_dirs) - len(batch_dirs)}")
        else:
            print("   ❌ No keys found in this batch")

def main():
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--status':
        # Show status
        hunter = WX51Hunter()
        processed_dirs = hunter.load_processed_directories()
        
        interesting_dirs, user_dirs = hunter.scan_directory_structure()
        all_directories = interesting_dirs + user_dirs
        unprocessed_dirs = [d for d in all_directories if d not in processed_dirs]
        
        print(f"\n📊 WX51A40D1621 Hunt Status:")
        print(f"   📁 Total directories found: {len(all_directories)}")
        print(f"   ✅ Processed: {len(processed_dirs)}")
        print(f"   ⏳ Remaining: {len(unprocessed_dirs)}")
        return
    
    # Run the hunt
    hunter = WX51Hunter()
    hunter.run_hunt()

if __name__ == "__main__":
    main()
