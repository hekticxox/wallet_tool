#!/usr/bin/env python3
"""
MHY2120BH Mac OS X System Hunter
Advanced wallet extraction and recovery tool for mounted Mac drive
Specialized for Mac OS X wallet locations and formats
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

class MacOSXWalletHunter:
    def __init__(self):
        self.base_dir = "/mnt/MHY2120BH"  # Direct mounted access
        self.results_file = f"MHY2120BH_MAC_HUNT_RESULTS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.processed_dirs_file = "PROCESSED_MHY2120BH_DIRECTORIES.json"
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
            'mac_keychain': re.compile(r'[a-fA-F0-9]{32,128}'),  # Mac keychain entries
        }
        
        # Mac-specific wallet file patterns
        self.mac_wallet_files = [
            r'.*[Ww]allet.*\.dat$',
            r'.*\.key$',
            r'.*\.keystore$',
            r'.*\.json$',
            r'.*[Bb]itcoin.*\.plist$',
            r'.*[Ee]thereum.*\.plist$',
            r'.*\.wallet$',
            r'.*[Pp]rivkey.*',
            r'.*[Ss]eed.*\.txt$',
            r'.*[Bb]ackup.*\.txt$',
            r'.*[Rr]ecovery.*\.txt$',
            r'.*bitcoin.*\.conf$',
            r'.*electrum.*',
            r'.*multibit.*',
            r'.*armory.*',
            r'.*com\.bitcoin.*\.plist$',
            r'.*Keychain.*\.db$',
        ]
        
        # Mac OS X specific directories to prioritize
        self.mac_priority_dirs = [
            'Users',  # User home directories
            'Applications',  # Installed applications
            'Library',  # System and user libraries
            'private',  # System private data
        ]
        
        # API endpoints for balance checking
        self.apis = {
            'ethereum': [
                'https://api.blockcypher.com/v1/eth/main/addrs/{}/balance',
                'https://api.etherscan.io/api?module=account&action=balance&address={}&tag=latest'
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

    def scan_mac_directory_structure(self):
        """Scan the Mac OS X directory structure for high-value targets"""
        print(f"\n🔍 Scanning Mac OS X directory structure...")
        
        high_priority_dirs = []
        user_dirs = []
        app_dirs = []
        
        try:
            # Explore Users directory (home directories)
            users_path = os.path.join(self.base_dir, "Users")
            if os.path.exists(users_path):
                for user_dir in os.listdir(users_path):
                    if user_dir not in ['.localized', 'Shared']:
                        user_path = os.path.join(users_path, user_dir)
                        if os.path.isdir(user_path):
                            user_dirs.append(user_path)
                            
                            # Check user's Library for wallet apps
                            user_lib = os.path.join(user_path, "Library")
                            if os.path.exists(user_lib):
                                user_dirs.append(user_lib)
                                
                            # Check user's Documents
                            user_docs = os.path.join(user_path, "Documents")
                            if os.path.exists(user_docs):
                                user_dirs.append(user_docs)
                                
                            # Check user's Desktop
                            user_desktop = os.path.join(user_path, "Desktop")
                            if os.path.exists(user_desktop):
                                user_dirs.append(user_desktop)
            
            # Explore Applications directory
            apps_path = os.path.join(self.base_dir, "Applications")
            if os.path.exists(apps_path):
                for app_dir in os.listdir(apps_path):
                    app_path = os.path.join(apps_path, app_dir)
                    if os.path.isdir(app_path):
                        # Look for crypto-related apps
                        if any(crypto in app_dir.lower() for crypto in ['bitcoin', 'ethereum', 'crypto', 'wallet', 'electrum', 'multibit']):
                            app_dirs.append(app_path)
                        else:
                            app_dirs.append(app_path)  # Add all apps for comprehensive scan
            
            # Explore system Library
            lib_path = os.path.join(self.base_dir, "Library")
            if os.path.exists(lib_path):
                high_priority_dirs.append(lib_path)
                
        except PermissionError as e:
            print(f"⚠️ Permission error accessing directory: {e}")
            
        return high_priority_dirs, user_dirs, app_dirs

    def extract_keys_from_file(self, file_path):
        """Extract potential private keys from a Mac file"""
        keys_found = []
        
        try:
            # Handle Mac-specific file types
            file_extension = os.path.splitext(file_path)[1].lower()
            
            # Try different encodings (Mac uses various encodings)
            for encoding in ['utf-8', 'macroman', 'latin-1', 'cp1252', 'ascii']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            else:
                # If text reading fails, try binary
                with open(file_path, 'rb') as f:
                    content = f.read().decode('utf-8', errors='ignore')
            
            # Special handling for Mac plist files
            if file_extension == '.plist':
                keys_found.extend(self.extract_from_plist(content, file_path))
            
            # Extract using patterns
            for key_type, pattern in self.key_patterns.items():
                matches = pattern.findall(content)
                for match in matches:
                    if self.validate_key_format(match, key_type):
                        keys_found.append({
                            'key': match,
                            'type': key_type,
                            'source': file_path,
                            'confidence': self.calculate_mac_confidence(match, key_type, file_path)
                        })
                        
        except Exception as e:
            # Don't print errors for system files that are expected to fail
            if not any(x in file_path.lower() for x in ['system', 'kernel', 'framework', '.framework']):
                print(f"⚠️ Error reading {file_path}: {e}")
            
        return keys_found

    def extract_from_plist(self, content, file_path):
        """Extract keys from Mac plist files"""
        keys_found = []
        
        # Look for base64 encoded data in plists
        base64_pattern = re.compile(r'<data>\s*([A-Za-z0-9+/=\s]+)\s*</data>')
        matches = base64_pattern.findall(content)
        
        for match in matches:
            try:
                import base64
                decoded = base64.b64decode(match.replace('\n', '').replace(' ', ''))
                # Check if decoded data looks like a private key
                if len(decoded) == 32 and all(b != 0 for b in decoded[:4]):  # Not all zeros
                    hex_key = decoded.hex()
                    keys_found.append({
                        'key': hex_key,
                        'type': 'plist_decoded_key',
                        'source': file_path,
                        'confidence': 0.8  # High confidence for plist keys
                    })
            except:
                continue
                
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
        elif key_type == 'mac_keychain':
            return 32 <= len(key) <= 128 and all(c in '0123456789abcdefABCDEF' for c in key)
        return True

    def calculate_mac_confidence(self, key, key_type, file_path):
        """Calculate confidence score for Mac-extracted key"""
        confidence = 0.5  # Base confidence
        
        # Mac-specific file path indicators
        mac_wallet_indicators = [
            'bitcoin', 'ethereum', 'wallet', 'key', 'seed', 'backup', 'private', 'secret',
            'electrum', 'multibit', 'armory', 'breadwallet', 'copay', 'exodus',
            'library/application support', 'keychain', 'preferences'
        ]
        
        for indicator in mac_wallet_indicators:
            if indicator.lower() in file_path.lower():
                confidence += 0.2
                
        # User directory bonus
        if '/Users/' in file_path and '/Library/' in file_path:
            confidence += 0.1
            
        # Application support directory bonus
        if 'Application Support' in file_path:
            confidence += 0.15
            
        # Key type specific scoring
        if key_type == 'mnemonic':
            confidence += 0.3
        elif key_type == 'bitcoin_wif':
            confidence += 0.2
        elif key_type == 'plist_decoded_key':
            confidence += 0.3
        elif key_type == 'eth_private_key':
            confidence += 0.1
            
        return min(confidence, 1.0)

    def hunt_mac_directory(self, directory, max_files=1000):
        """Hunt for wallet data in a Mac directory"""
        print(f"\n🔍 Mac Hunting: {directory}")
        
        files_scanned = 0
        keys_found = []
        
        try:
            for root, dirs, files in os.walk(directory):
                # Skip system directories that are unlikely to have wallets
                dirs[:] = [d for d in dirs if not d.startswith('.') or d in ['.bitcoin', '.ethereum']]
                
                for file in files:
                    if files_scanned >= max_files:
                        break
                        
                    file_path = os.path.join(root, file)
                    
                    # Check if file matches Mac wallet patterns
                    should_scan = False
                    for pattern in self.mac_wallet_files:
                        if re.match(pattern, file, re.IGNORECASE):
                            should_scan = True
                            break
                    
                    # Always scan small text files and crypto-related files
                    if not should_scan:
                        try:
                            file_size = os.path.getsize(file_path)
                            if file_size < 500000:  # Under 500KB
                                if (file.endswith(('.txt', '.log', '.cfg', '.conf', '.json', '.plist', '.dat')) or
                                    any(crypto in file.lower() for crypto in ['bitcoin', 'ethereum', 'wallet', 'key', 'seed'])):
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
            print(f"⚠️ Error hunting Mac directory {directory}: {e}")
            
        self.total_files_scanned += files_scanned
        return keys_found

    def run_mac_hunt(self, batch_size=5):
        """Main Mac hunting function"""
        print(f"\n🚀 Starting MHY2120BH Mac OS X Hunt - {datetime.now()}")
        print(f"📁 Target: {self.base_dir}")
        print(f"🖥️ System: Mac OS X (2008-2014 era)")
        
        # Scan Mac directory structure
        high_priority, user_dirs, app_dirs = self.scan_mac_directory_structure()
        
        print(f"\n📊 Mac Directory Analysis:")
        print(f"   🏠 User directories found: {len(user_dirs)}")
        print(f"   📱 Application directories: {len(app_dirs)}")
        print(f"   📚 System library directories: {len(high_priority)}")
        
        # Load processed directories
        processed_dirs = self.load_processed_directories()
        
        all_directories = high_priority + user_dirs + app_dirs
        unprocessed_dirs = [d for d in all_directories if d not in processed_dirs]
        
        print(f"📊 {len(processed_dirs)} directories already processed")
        print(f"📊 {len(unprocessed_dirs)} directories remaining")
        
        if not unprocessed_dirs:
            print("✅ All directories already processed!")
            return
        
        # Process directories in batches
        all_keys = []
        batch_dirs = unprocessed_dirs[:batch_size]
        
        print(f"\n🔍 Processing next {len(batch_dirs)} Mac directories:")
        
        for directory in batch_dirs:
            print(f"\n   📁 {directory}")
            keys = self.hunt_mac_directory(directory)
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
            
            print(f"\n🎯 MAC HUNT SUMMARY:")
            print(f"   📄 Files scanned: {self.total_files_scanned}")
            print(f"   🔑 Keys extracted: {len(unique_keys)}")
            print(f"   💎 Funded wallets: {funded_count}")
            print(f"   📁 Directories processed: {len(batch_dirs)}")
            print(f"   📁 Directories remaining: {len(unprocessed_dirs) - len(batch_dirs)}")
        else:
            print("   ❌ No keys found in this batch")

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
                            print(f"   💎 FUNDED MAC WALLET FOUND!")
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
            if key_type in ['eth_private_key', 'bitcoin_hex', 'plist_decoded_key'] and len(key) == 64:
                # Try to generate Ethereum address
                try:
                    from eth_keys import keys
                    private_key = keys.PrivateKey(bytes.fromhex(key))
                    addresses['ethereum'] = private_key.public_key.to_checksum_address()
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
            'system_type': 'Mac OS X (2008-2014)',
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

def main():
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--status':
        # Show status
        hunter = MacOSXWalletHunter()
        processed_dirs = hunter.load_processed_directories()
        
        high_priority, user_dirs, app_dirs = hunter.scan_mac_directory_structure()
        all_directories = high_priority + user_dirs + app_dirs
        unprocessed_dirs = [d for d in all_directories if d not in processed_dirs]
        
        print(f"\n📊 MHY2120BH Mac Hunt Status:")
        print(f"   📁 Total directories found: {len(all_directories)}")
        print(f"   ✅ Processed: {len(processed_dirs)}")
        print(f"   ⏳ Remaining: {len(unprocessed_dirs)}")
        return
    
    # Run the Mac hunt
    hunter = MacOSXWalletHunter()
    hunter.run_mac_hunt()

if __name__ == "__main__":
    main()
