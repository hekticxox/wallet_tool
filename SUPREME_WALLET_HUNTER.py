#!/usr/bin/env python3
"""
SUPREME WALLET HUNTER - Ultimate Private Key Discovery & Balance Checker
Consolidates all wallet recovery tools into one supreme working file
"""

import os
import sys
import json
import time
import random
import hashlib
import requests
import re
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import logging

# Try to import Bitcoin library
try:
    import bitcoin
    BITCOIN_AVAILABLE = True
except ImportError:
    BITCOIN_AVAILABLE = False
    print("⚠️  Bitcoin library not available. Install with: pip install bitcoin")

# Try to import Ethereum libraries
try:
    from eth_keys import keys as eth_keys
    ETH_AVAILABLE = True
except ImportError:
    ETH_AVAILABLE = False
    print("⚠️  Ethereum library not available. Install with: pip install eth-keys")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('supreme_wallet_hunter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SupremeWalletHunter')

class SupremeWalletHunter:
    """Ultimate wallet hunter combining all proven methods"""
    
    def __init__(self):
        self.results = []
        self.funded_wallets = []
        self.session = requests.Session()
        self.apis = {
            'bitcoin': [
                'https://blockstream.info/api/address/{}/balance',
                'https://blockchain.info/q/addressbalance/{}'
            ],
            'ethereum': [
                'https://api.etherscan.io/api?module=account&action=balance&address={}&tag=latest'
            ]
        }
        
    def generate_brain_wallets(self, count=100000):
        """Generate brain wallet phrases from premium dictionaries"""
        phrases = []
        
        # Premium crypto-era phrases (2009-2017 focus)
        crypto_terms = [
            'bitcoin', 'satoshi', 'blockchain', 'crypto', 'hodl', 'moon',
            'lambo', 'diamond', 'hands', 'ape', 'doge', 'ethereum', 'btc',
            'eth', 'defi', 'nft', 'web3', 'metaverse', 'altcoin', 'pump'
        ]
        
        # Early adopter phrases
        early_phrases = [
            'digital gold', 'be your own bank', 'magic internet money',
            'to the moon', 'when lambo', 'diamond hands', 'paper hands',
            'buy the dip', 'not your keys', 'trustless', 'decentralized'
        ]
        
        # Common passwords + crypto
        for term in crypto_terms:
            for year in range(2009, 2025):
                phrases.extend([
                    f"{term}{year}",
                    f"{term}_{year}",
                    f"{year}{term}",
                    f"my{term}{year}",
                    f"{term}wallet{year}",
                    f"secret{term}{year}"
                ])
        
        # Personal + crypto combinations
        personal = ['love', 'life', 'money', 'secret', 'password', 'wallet']
        for p in personal:
            for c in crypto_terms:
                phrases.extend([f"{p}{c}", f"{c}{p}", f"{p}_{c}", f"{c}_{p}"])
        
        # Famous crypto phrases
        phrases.extend([
            'hal finney running bitcoin',
            'gm gm gm',
            'few understand',
            'this is gentlemen',
            'bitcoin fixes this',
            'number go up',
            'laser eyes',
            'have fun staying poor',
            'wagmi',
            'ngmi'
        ])
        
        return list(set(phrases))[:count]
    
    def sha256_to_private_key(self, phrase):
        """Convert phrase to private key via SHA256"""
        return hashlib.sha256(phrase.encode('utf-8')).hexdigest()
    
    def private_key_to_bitcoin_address(self, private_key):
        """Convert private key to Bitcoin address"""
        if BITCOIN_AVAILABLE:
            try:
                return bitcoin.privkey_to_address(private_key)
            except Exception as e:
                logger.debug(f"Bitcoin address generation error: {e}")
        
        # Fallback: Generate a mock address for testing
        return f"1{hashlib.sha256(private_key.encode()).hexdigest()[:33]}"
    
    def private_key_to_ethereum_address(self, private_key):
        """Convert private key to Ethereum address"""
        if ETH_AVAILABLE:
            try:
                pk = eth_keys.PrivateKey(bytes.fromhex(private_key.replace('0x', '')))
                return pk.public_key.to_checksum_address()
            except Exception as e:
                logger.debug(f"Ethereum address generation error: {e}")
        
        # Fallback: Generate a mock address for testing
        return f"0x{hashlib.sha256(private_key.encode()).hexdigest()[-40:]}"
    
    def check_bitcoin_balance(self, address):
        """Check Bitcoin balance via multiple APIs"""
        for api_url in self.apis['bitcoin']:
            try:
                url = api_url.format(address)
                response = self.session.get(url, timeout=10)
                
                if 'blockstream' in url:
                    data = response.json()
                    balance = data.get('confirmed', 0) / 100000000  # Convert satoshi to BTC
                elif 'blockchain.info' in url:
                    balance = int(response.text) / 100000000  # Convert satoshi to BTC
                
                if balance > 0:
                    return balance
                    
            except Exception as e:
                logger.debug(f"Bitcoin API error: {e}")
                continue
        
        return 0
    
    def check_ethereum_balance(self, address):
        """Check Ethereum balance"""
        try:
            url = self.apis['ethereum'][0].format(address)
            response = self.session.get(url, timeout=10)
            data = response.json()
            
            if data.get('status') == '1':
                balance = int(data.get('result', 0)) / 10**18  # Convert wei to ETH
                return balance
                
        except Exception as e:
            logger.debug(f"Ethereum API error: {e}")
            
        return 0
    
    def hunt_brain_wallets(self, phrase_count=100000):
        """Ultimate brain wallet hunting"""
        logger.info(f"🔥 SUPREME BRAIN WALLET HUNT STARTING")
        logger.info(f"🎯 Target: {phrase_count:,} optimized phrases")
        
        phrases = self.generate_brain_wallets(phrase_count)
        found_count = 0
        
        for i, phrase in enumerate(phrases):
            if i % 100 == 0:
                logger.info(f"📊 Progress: {i:,}/{len(phrases):,} ({i/len(phrases)*100:.1f}%) | Found: {found_count}")
            
            try:
                # Generate private key
                private_key = self.sha256_to_private_key(phrase)
                
                # Check Bitcoin
                btc_address = self.private_key_to_bitcoin_address(private_key)
                btc_balance = self.check_bitcoin_balance(btc_address)
                
                # Check Ethereum  
                eth_address = self.private_key_to_ethereum_address(private_key)
                eth_balance = self.check_ethereum_balance(eth_address)
                
                total_value = btc_balance + eth_balance
                
                if total_value > 0:
                    found_count += 1
                    wallet_info = {
                        'phrase': phrase,
                        'private_key': private_key,
                        'bitcoin_address': btc_address,
                        'bitcoin_balance': btc_balance,
                        'ethereum_address': eth_address,
                        'ethereum_balance': eth_balance,
                        'total_value': total_value,
                        'found_at': datetime.now().isoformat()
                    }
                    
                    self.funded_wallets.append(wallet_info)
                    logger.info(f"💰 FUNDED WALLET FOUND! Phrase: '{phrase}' | Value: ${total_value*50000:.2f}")
                    
                    # Save immediately
                    self.save_results()
                
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.debug(f"Error processing phrase '{phrase}': {e}")
                continue
        
        logger.info(f"🎯 HUNT COMPLETE! Found {found_count} funded wallets from {len(phrases):,} phrases")
        return found_count
    
    def extract_from_files(self, directory):
        """Extract private keys from files with live progress"""
        logger.info(f"🔍 STARTING EXTRACTION from: {directory}")
        
        patterns = {
            'bitcoin_wif': r'[5KL][1-9A-HJ-NP-Za-km-z]{50,51}',
            'ethereum_hex': r'0x[a-fA-F0-9]{64}',
            'hex_64': r'[a-fA-F0-9]{64}',
            'seed_12': r'(\w+\s+){11}\w+',
            'seed_24': r'(\w+\s+){23}\w+'
        }
        
        found_keys = []
        files_processed = 0
        total_files = 0
        
        # Count total files first
        logger.info("📊 Counting files to process...")
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(('.json', '.txt', '.key', '.pem', '.dat', '.csv')):
                    total_files += 1
        
        logger.info(f"🎯 Found {total_files} relevant files to process")
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(('.json', '.txt', '.key', '.pem', '.dat', '.csv')):
                    files_processed += 1
                    
                    # Show progress every 5 files
                    if files_processed % 5 == 0 or files_processed <= 10:
                        progress_pct = (files_processed / total_files) * 100
                        logger.info(f"📂 Extraction: {files_processed}/{total_files} files ({progress_pct:.1f}%) | Keys found: {len(found_keys)}")
                    
                    try:
                        file_path = Path(root) / file
                        
                        # Skip very large files
                        if file_path.stat().st_size > 10 * 1024 * 1024:
                            logger.info(f"⚠️ Skipping large file: {file_path.name}")
                            continue
                        
                        # Show current file being processed (every 25 files)
                        if files_processed % 25 == 0:
                            logger.info(f"🔍 Processing: {file_path.name}")
                        
                        content = file_path.read_text(errors='ignore')
                        
                        for key_type, pattern in patterns.items():
                            matches = re.findall(pattern, content)
                            for match in matches:
                                if isinstance(match, tuple):
                                    match = ''.join(match).strip()
                                
                                found_keys.append({
                                    'type': key_type,
                                    'key': str(match).strip(),
                                    'file': str(file_path),
                                    'found_at': datetime.now().isoformat()
                                })
                                
                                # Show key discovery progress
                                if len(found_keys) % 1000 == 0:
                                    logger.info(f"🔑 Found {len(found_keys)} keys so far!")
                                
                    except Exception as e:
                        logger.debug(f"Error processing file {file_path}: {e}")
                        continue
        
        logger.info(f"✅ EXTRACTION COMPLETE! Found {len(found_keys)} keys from {files_processed} files")
        logger.info(f"🎯 Starting balance scanning for {len(found_keys)} keys...")
        return found_keys
    
    def scan_extracted_keys(self, keys):
        """Scan extracted keys for balances with live progress"""
        # Convert to list if needed
        if not isinstance(keys, list):
            keys = list(keys)
            
        logger.info(f"🎯 STARTING BALANCE SCAN for {len(keys)} extracted keys")
        
        funded_count = 0
        total_keys = len(keys)
        
        for i, key_data in enumerate(keys):
            # Show progress every 25 keys (more frequent updates)
            if i % 25 == 0 or i < 100:
                progress_pct = (i/total_keys*100) if total_keys > 0 else 0
                logger.info(f"� Balance Scan: {i:,}/{total_keys:,} ({progress_pct:.1f}%) | Funded: {funded_count}")
            
            # Show major milestones
            if i > 0 and i % 1000 == 0:
                logger.info(f"🎯 MILESTONE: {i:,} keys scanned! Found {funded_count} funded wallets")
            
            try:
                key_type = key_data.get('type', '')
                key_value = key_data.get('key', '')
                
                # Show what type of key we're processing (occasionally)
                if i % 500 == 0:
                    logger.info(f"🔍 Processing {key_type} key: {key_value[:20]}...")
                
                if 'bitcoin' in key_type or 'wif' in key_type:
                    # Handle Bitcoin keys
                    if BITCOIN_AVAILABLE:
                        try:
                            address = bitcoin.privkey_to_address(key_value)
                            balance = self.check_bitcoin_balance(address)
                            
                            if balance > 0:
                                funded_count += 1
                                wallet_info = {
                                    'type': key_type,
                                    'private_key': key_value,
                                    'address': address,
                                    'balance': balance,
                                    'currency': 'BTC',
                                    'value_usd': balance * 50000,
                                    'source_file': key_data.get('file', ''),
                                    'found_at': datetime.now().isoformat()
                                }
                                
                                self.funded_wallets.append(wallet_info)
                                logger.info(f"💰 FUNDED BITCOIN WALLET! Balance: {balance} BTC (${balance*50000:.2f})")
                                self.save_results()
                                
                        except Exception as e:
                            logger.debug(f"Bitcoin key processing error: {e}")
                    else:
                        logger.debug("Bitcoin library not available, skipping Bitcoin keys")
                
                elif 'ethereum' in key_type or 'hex' in key_type:
                    # Handle Ethereum keys
                    if ETH_AVAILABLE:
                        try:
                            clean_key = key_value.replace('0x', '')
                            if len(clean_key) == 64:  # Valid 64-char hex key
                                pk = eth_keys.PrivateKey(bytes.fromhex(clean_key))
                                address = pk.public_key.to_checksum_address()
                                balance = self.check_ethereum_balance(address)
                                
                                if balance > 0:
                                    funded_count += 1
                                    wallet_info = {
                                        'type': key_type,
                                        'private_key': key_value,
                                        'address': address,
                                        'balance': balance,
                                        'currency': 'ETH',
                                        'value_usd': balance * 3000,
                                        'source_file': key_data.get('file', ''),
                                        'found_at': datetime.now().isoformat()
                                    }
                                    
                                    self.funded_wallets.append(wallet_info)
                                    logger.info(f"💰 FUNDED ETHEREUM WALLET! Balance: {balance} ETH (${balance*3000:.2f})")
                                    self.save_results()
                                    
                        except Exception as e:
                            logger.debug(f"Ethereum key processing error: {e}")
                    else:
                        logger.debug("Ethereum library not available, skipping Ethereum keys")
                
                time.sleep(0.05)  # Reduced rate limiting for faster scanning
                
            except Exception as e:
                logger.debug(f"Key processing error: {e}")
                continue
        
        logger.info(f"🎯 SCAN COMPLETE! Found {funded_count} funded wallets from {total_keys:,} keys")
        return funded_count
    
    def save_results(self):
        """Save results to JSON file"""
        timestamp = int(time.time())
        filename = f"supreme_hunt_results_{timestamp}.json"
        
        results_data = {
            'scan_info': {
                'timestamp': datetime.now().isoformat(),
                'total_funded_wallets': len(self.funded_wallets),
                'total_estimated_value': sum(w.get('value_usd', 0) for w in self.funded_wallets)
            },
            'funded_wallets': self.funded_wallets
        }
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        logger.info(f"💾 Results saved to: {filename}")
        return filename

def main():
    """Main execution function"""
    print("🔥" * 50)
    print("🚀 SUPREME WALLET HUNTER - ULTIMATE EDITION")
    print("🔥" * 50)
    
    hunter = SupremeWalletHunter()
    
    # Menu system
    while True:
        print("\n🎯 SELECT HUNTING MODE:")
        print("1. 🧠 Brain Wallet Hunt (100K phrases)")
        print("2. 📁 Extract & Scan Files")
        print("3. 🚀 MEGA Hunt (Brain + Files)")
        print("4. 📊 View Results")
        print("5. 🏃 Exit")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            phrase_count = int(input("Enter phrase count (default 100000): ") or 100000)
            hunter.hunt_brain_wallets(phrase_count)
            
        elif choice == '2':
            directory = input("Enter directory path: ").strip()
            if os.path.exists(directory):
                keys = hunter.extract_from_files(directory)
                if keys:
                    hunter.scan_extracted_keys(keys)
            else:
                print("❌ Directory not found")
                
        elif choice == '3':
            print("🔥 LAUNCHING MEGA HUNT...")
            # Brain wallet hunt
            hunter.hunt_brain_wallets(100000)
            
            # File extraction hunt
            common_dirs = ['data', 'Downloads', 'Documents']
            for dir_name in common_dirs:
                if os.path.exists(dir_name):
                    keys = hunter.extract_from_files(dir_name)
                    if keys:
                        hunter.scan_extracted_keys(keys)
                        
        elif choice == '4':
            if hunter.funded_wallets:
                print(f"\n💰 FOUND {len(hunter.funded_wallets)} FUNDED WALLETS:")
                total_value = 0
                for wallet in hunter.funded_wallets:
                    value = wallet.get('value_usd', 0)
                    total_value += value
                    print(f"   💎 {wallet.get('currency', 'CRYPTO')}: ${value:.2f}")
                print(f"🏆 TOTAL VALUE: ${total_value:.2f}")
            else:
                print("📊 No funded wallets found yet")
                
        elif choice == '5':
            print("🏃 Exiting Supreme Wallet Hunter")
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()