#!/usr/bin/env python3
"""
Multi-chain wallet balance scanner for extracted private keys
Supports Bitcoin (WIF format) and Ethereum (hex format) keys
"""

import json
import time
import requests
from datetime import datetime
import os
import sys
from typing import Dict, List, Optional, Tuple
import hashlib
from bitcoin import privtoaddr, encode_privkey, decode_privkey
from eth_keys import keys
from web3 import Web3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultiChainScanner:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        
        # API endpoints
        self.btc_api_urls = [
            'https://blockchain.info/q/addressbalance/',
            'https://blockstream.info/api/address/',
        ]
        
        self.eth_api_urls = [
            'https://api.etherscan.io/api?module=account&action=balance&address=',
        ]
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms between requests

    def rate_limit(self):
        """Enforce rate limiting between API requests"""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def bitcoin_hex_to_address(self, hex_key: str) -> Optional[str]:
        """Convert Bitcoin hex private key to address"""
        try:
            # Ensure proper format
            hex_key = hex_key.strip()
            if len(hex_key) != 64:
                return None
            
            # Convert hex to WIF and then to address
            wif_key = encode_privkey(hex_key, 'wif')
            address = privtoaddr(wif_key)
            return address
        except Exception as e:
            logger.debug(f"Failed to convert Bitcoin hex key {hex_key[:8]}...: {e}")
            return None

    def bitcoin_wif_to_address(self, wif_key: str) -> Optional[str]:
        """Convert Bitcoin WIF private key to address"""
        try:
            address = privtoaddr(wif_key)
            return address
        except Exception as e:
            logger.debug(f"Failed to convert Bitcoin WIF key {wif_key[:8]}...: {e}")
            return None

    def ethereum_hex_to_address(self, hex_key: str) -> Optional[str]:
        """Convert Ethereum hex private key to address"""
        try:
            # Ensure proper format
            hex_key = hex_key.strip().lower()
            if len(hex_key) != 64:
                return None
            
            # Convert hex to private key object
            private_key = keys.PrivateKey(bytes.fromhex(hex_key))
            address = private_key.public_key.to_checksum_address()
            return address
        except Exception as e:
            logger.debug(f"Failed to convert Ethereum hex key {hex_key[:8]}...: {e}")
            return None

    def check_bitcoin_balance(self, address: str) -> Tuple[Optional[float], str]:
        """Check Bitcoin balance for an address"""
        try:
            self.rate_limit()
            
            # Try blockchain.info first
            url = f"https://blockchain.info/q/addressbalance/{address}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                balance_satoshis = int(response.text.strip())
                balance_btc = balance_satoshis / 100000000  # Convert satoshis to BTC
                return balance_btc, "blockchain.info"
            
        except Exception as e:
            logger.debug(f"blockchain.info failed for {address}: {e}")
        
        try:
            # Try blockstream.info as fallback
            self.rate_limit()
            url = f"https://blockstream.info/api/address/{address}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                balance_satoshis = data.get('chain_stats', {}).get('funded_txo_sum', 0) - \
                                 data.get('chain_stats', {}).get('spent_txo_sum', 0)
                balance_btc = balance_satoshis / 100000000
                return balance_btc, "blockstream.info"
            
        except Exception as e:
            logger.debug(f"blockstream.info failed for {address}: {e}")
        
        return None, "failed"

    def check_ethereum_balance(self, address: str) -> Tuple[Optional[float], str]:
        """Check Ethereum balance for an address"""
        try:
            self.rate_limit()
            
            # Use etherscan.io API
            url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey=YourApiKeyToken"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == '1':
                    balance_wei = int(data.get('result', '0'))
                    balance_eth = balance_wei / (10**18)  # Convert wei to ETH
                    return balance_eth, "etherscan.io"
            
        except Exception as e:
            logger.debug(f"etherscan.io failed for {address}: {e}")
        
        return None, "failed"

    def scan_key(self, key_data: Dict) -> Optional[Dict]:
        """Scan a single key for balance"""
        key_type = key_data.get('type', '')
        key_value = key_data.get('key', '')
        
        result = {
            'original_key': key_value,
            'key_type': key_type,
            'file': key_data.get('file', ''),
            'position': key_data.get('position', 0),
            'timestamp': key_data.get('timestamp', ''),
            'scan_timestamp': datetime.now().isoformat(),
            'success': False,
            'address': None,
            'balance': None,
            'balance_currency': None,
            'api_source': None,
            'error': None
        }
        
        try:
            # Handle Bitcoin keys
            if key_type in ['bitcoin_hex', 'bitcoin_wif', 'bitcoin_wif_compressed']:
                if key_type == 'bitcoin_hex':
                    address = self.bitcoin_hex_to_address(key_value)
                else:  # WIF formats
                    address = self.bitcoin_wif_to_address(key_value)
                
                if address:
                    result['address'] = address
                    balance, source = self.check_bitcoin_balance(address)
                    if balance is not None:
                        result['balance'] = balance
                        result['balance_currency'] = 'BTC'
                        result['api_source'] = source
                        result['success'] = True
                        if balance > 0:
                            logger.info(f"FUNDED BITCOIN WALLET FOUND! Address: {address}, Balance: {balance} BTC")
                    else:
                        result['error'] = f"Failed to get balance from {source}"
                else:
                    result['error'] = "Failed to convert key to address"
            
            # Handle Ethereum keys
            elif key_type == 'ethereum_hex':
                address = self.ethereum_hex_to_address(key_value)
                
                if address:
                    result['address'] = address
                    balance, source = self.check_ethereum_balance(address)
                    if balance is not None:
                        result['balance'] = balance
                        result['balance_currency'] = 'ETH'
                        result['api_source'] = source
                        result['success'] = True
                        if balance > 0:
                            logger.info(f"FUNDED ETHEREUM WALLET FOUND! Address: {address}, Balance: {balance} ETH")
                    else:
                        result['error'] = f"Failed to get balance from {source}"
                else:
                    result['error'] = "Failed to convert key to address"
            
            else:
                result['error'] = f"Unsupported key type: {key_type}"
        
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error scanning key {key_value[:8]}...: {e}")
        
        return result

    def scan_keys_from_file(self, extraction_file: str, max_keys: int = 100, key_types: List[str] = None) -> Dict:
        """Scan keys from extraction results file"""
        logger.info(f"Loading extraction results from {extraction_file}")
        
        try:
            with open(extraction_file, 'r') as f:
                extraction_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load extraction file: {e}")
            return {}
        
        findings = extraction_data.get('findings', [])
        logger.info(f"Found {len(findings):,} total keys in extraction file")
        
        # Filter by key types if specified
        if key_types:
            findings = [f for f in findings if f.get('type') in key_types]
            logger.info(f"Filtered to {len(findings):,} keys of types: {', '.join(key_types)}")
        
        # Limit number of keys to scan
        if max_keys > 0 and len(findings) > max_keys:
            findings = findings[:max_keys]
            logger.info(f"Limited to first {max_keys} keys for scanning")
        
        # Start scanning
        results = []
        funded_wallets = []
        
        logger.info(f"Starting scan of {len(findings)} keys...")
        
        for i, key_data in enumerate(findings, 1):
            if i % 50 == 0:
                logger.info(f"Progress: {i}/{len(findings)} keys scanned")
            
            result = self.scan_key(key_data)
            if result:
                results.append(result)
                
                # Track funded wallets
                if result.get('success') and result.get('balance', 0) > 0:
                    funded_wallets.append(result)
        
        # Prepare final results
        scan_summary = {
            'scan_timestamp': datetime.now().isoformat(),
            'extraction_file': extraction_file,
            'total_keys_available': len(extraction_data.get('findings', [])),
            'keys_scanned': len(results),
            'funded_wallets_found': len(funded_wallets),
            'successful_scans': len([r for r in results if r.get('success')]),
            'failed_scans': len([r for r in results if not r.get('success')]),
            'key_types_scanned': key_types or 'all',
            'funded_wallets': funded_wallets,
            'all_results': results
        }
        
        # Save results
        timestamp = int(time.time())
        results_file = f"multi_chain_scan_results_{timestamp}.json"
        
        try:
            with open(results_file, 'w') as f:
                json.dump(scan_summary, f, indent=2)
            logger.info(f"Results saved to {results_file}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
        
        # Print summary
        logger.info(f"\n=== SCAN COMPLETE ===")
        logger.info(f"Keys scanned: {len(results):,}")
        logger.info(f"Successful scans: {scan_summary['successful_scans']:,}")
        logger.info(f"Failed scans: {scan_summary['failed_scans']:,}")
        logger.info(f"FUNDED WALLETS FOUND: {len(funded_wallets)}")
        
        if funded_wallets:
            logger.info(f"\n=== FUNDED WALLETS ===")
            for wallet in funded_wallets:
                currency = wallet.get('balance_currency', 'Unknown')
                balance = wallet.get('balance', 0)
                address = wallet.get('address', 'Unknown')
                logger.info(f"Address: {address}")
                logger.info(f"Balance: {balance} {currency}")
                logger.info(f"Key Type: {wallet.get('key_type')}")
                logger.info(f"Source File: {wallet.get('file', 'Unknown')}")
                logger.info("-" * 60)
        
        return scan_summary

def main():
    if len(sys.argv) < 2:
        print("Usage: python multi_chain_scanner.py <extraction_results.json> [max_keys] [key_types...]")
        print("Example: python multi_chain_scanner.py unified_extraction_results_1755835800.json 200 bitcoin_hex ethereum_hex")
        sys.exit(1)
    
    extraction_file = sys.argv[1]
    max_keys = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    key_types = sys.argv[3:] if len(sys.argv) > 3 else None
    
    if not os.path.exists(extraction_file):
        logger.error(f"Extraction file not found: {extraction_file}")
        sys.exit(1)
    
    scanner = MultiChainScanner()
    results = scanner.scan_keys_from_file(extraction_file, max_keys, key_types)
    
    return results

if __name__ == "__main__":
    main()
