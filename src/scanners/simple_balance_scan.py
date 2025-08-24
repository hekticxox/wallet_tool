#!/usr/bin/env python3
"""
Simple Balance Scanner - File-based scanning without database
============================================================
Scans extracted keys for balances using direct API calls
"""

import json
import logging
import asyncio
import requests
import time
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Import Bitcoin utilities for key conversion
try:
    import bitcoin
    BITCOIN_AVAILABLE = True
except ImportError:
    bitcoin = None
    BITCOIN_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleBalanceScanner:
    """Simple balance scanner for file-based operation"""
    
    def __init__(self):
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
    
    def hex_to_bitcoin_address(self, hex_key: str) -> str:
        """Convert hex private key to Bitcoin address"""
        if not BITCOIN_AVAILABLE:
            logger.warning("Bitcoin library not available, cannot convert hex key")
            return hex_key
        
        try:
            # Validate hex key format (64 characters, valid hex)
            if len(hex_key) != 64:
                logger.warning(f"Invalid hex key length: {len(hex_key)}, expected 64")
                return hex_key
                
            # Convert hex to int, then to WIF, then to address
            private_key_int = int(hex_key, 16)
            wif_key = bitcoin.encode_privkey(private_key_int, 'wif')
            public_key = bitcoin.privkey_to_pubkey(wif_key)
            address = bitcoin.pubkey_to_address(public_key)
            
            logger.info(f"Converted hex key to address: {address}")
            return address
            
        except Exception as e:
            logger.error(f"Error converting hex key {hex_key[:8]}...{hex_key[-8:]}: {e}")
            return hex_key

    def wif_to_bitcoin_address(self, wif_key: str) -> str:
        """Convert WIF private key to Bitcoin address"""
        if not BITCOIN_AVAILABLE:
            logger.warning("Bitcoin library not available, cannot convert WIF")
            return wif_key
        
        try:
            # Check if it's a valid private key
            if not bitcoin.is_privkey(wif_key):
                logger.warning(f"Invalid private key format: {wif_key[:10]}...")
                return wif_key
            
            # Get the format and decode
            key_format = bitcoin.get_privkey_format(wif_key)
            private_key = bitcoin.decode_privkey(wif_key, key_format)
            
            # Convert private key to address
            address = bitcoin.privkey_to_address(private_key)
            return address
        except Exception as e:
            logger.warning(f"Failed to convert WIF {wif_key[:10]}...: {e}")
            return wif_key
        
    def load_extracted_keys(self) -> List[Dict[str, Any]]:
        """Load keys from extraction result files"""
        keys = []
        
        # Look for extraction result files (multiple patterns)
        patterns = [
            "*extraction_results*.json",
            "priority_extraction_results*.json",
            "*findings*.json",
            "*results*.json"
        ]
        
        for pattern in patterns:
            for file in Path(".").glob(pattern):
                try:
                    with open(file, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            if 'keys' in data:
                                keys.extend(data['keys'])
                                logger.info(f"Loaded {len(data['keys'])} keys from {file.name}")
                            elif 'findings' in data:
                                # Extract keys from findings format
                                findings = data['findings']
                                for finding in findings:
                                    if 'key' in finding:
                                        # Preserve original structure but add network info
                                        key_entry = finding.copy()  # Keep original structure
                                        key_entry['network'] = 'bitcoin' if 'bitcoin' in finding.get('type', '') else 'ethereum'
                                        keys.append(key_entry)
                                logger.info(f"Loaded {len(findings)} keys from findings in {file.name}")
                        elif isinstance(data, list):
                            keys.extend(data)
                            logger.info(f"Loaded {len(data)} keys from {file.name}")
                            
                except Exception as e:
                    logger.warning(f"Could not load {file}: {e}")
                
        return keys
    
    def check_bitcoin_balance(self, address: str) -> float:
        """Check Bitcoin balance using multiple APIs with fallback"""
        try:
            # Primary: Blockchain.info API
            url = f"https://blockchain.info/q/addressbalance/{address}"
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                satoshis = int(response.text)
                btc = satoshis / 100000000  # Convert satoshis to BTC
                return btc
            elif response.status_code == 429:
                logger.warning(f"Rate limited by blockchain.info, waiting...")
                time.sleep(3)  # Wait longer for rate limits
                
        except Exception as e:
            logger.warning(f"Primary API failed for {address[:10]}...: {e}")
        
        try:
            # Fallback: Blockstream API
            url = f"https://blockstream.info/api/address/{address}"
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                funded = data.get('chain_stats', {}).get('funded_txo_sum', 0)
                spent = data.get('chain_stats', {}).get('spent_txo_sum', 0)
                balance_satoshis = funded - spent
                btc = balance_satoshis / 100000000
                return btc
                
        except Exception as e:
            logger.warning(f"Fallback API failed for {address[:10]}...: {e}")
            
        return 0.0
    
    def check_ethereum_balance(self, address: str) -> float:
        """Check Ethereum balance using etherscan API"""
        try:
            # This is a demo - in production you'd use a proper API key
            url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey=YourApiKeyToken"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == '1':
                    wei = int(data.get('result', '0'))
                    eth = wei / 1000000000000000000  # Convert wei to ETH
                    return eth
            return 0.0
        except Exception as e:
            logger.warning(f"Error checking ETH balance for {address}: {e}")
            return 0.0
    
    async def scan_balances(self, max_keys: int = 100) -> Dict[str, Any]:
        """Scan balances for extracted keys"""
        logger.info(f"🚀 Starting Simple Balance Scanner")
        
        # Load extracted keys
        all_keys = self.load_extracted_keys()
        
        if not all_keys:
            logger.warning("No keys found in extraction files")
            return {"status": "no_keys", "message": "No keys found to scan"}
        
        # Limit keys to scan
        keys_to_scan = all_keys[:max_keys]
        logger.info(f"Starting balance check for {len(keys_to_scan)} keys")
        
        results = []
        funded_count = 0
        
        for i, key_data in enumerate(keys_to_scan, 1):
            try:
                # Extract address based on key format
                address = None
                network = "unknown"
                original_key = None
                
                if isinstance(key_data, dict):
                    # Get the key from the data
                    original_key = key_data.get('key', '')
                    key_type = key_data.get('type', 'unknown')
                    
                    # Convert WIF keys to addresses
                    if key_type in ['bitcoin_wif', 'bitcoin_wif_compressed'] and original_key:
                        address = self.wif_to_bitcoin_address(original_key)
                        network = "bitcoin"
                        logger.info(f"Converted {key_type} to address: {address}")
                    else:
                        # Try different address fields for direct addresses
                        for addr_field in ['bitcoin_address', 'address', 'public_key', 'wallet_address', 'eth_address']:
                            if addr_field in key_data:
                                address = key_data[addr_field]
                                break
                        network = key_data.get('network', 'bitcoin')
                
                elif isinstance(key_data, str):
                    original_key = key_data
                    # Check if it looks like a WIF key
                    if (key_data.startswith('L') or key_data.startswith('5') or key_data.startswith('K')) and len(key_data) > 50:
                        address = self.wif_to_bitcoin_address(key_data)
                        network = "bitcoin"
                        logger.info(f"Converted WIF key to address: {address}")
                    else:
                        address = key_data
                        network = "bitcoin"  # Default assumption
                
                if not address:
                    logger.warning(f"No address found for key {i}")
                    continue
                
                logger.info(f"Checking balance for address: {address[:20]}...")
                
                # Check balance based on network
                balance = 0.0
                if network.lower() in ['bitcoin', 'btc'] or address.startswith('1') or address.startswith('3') or address.startswith('bc1'):
                    balance = self.check_bitcoin_balance(address)
                    network = "bitcoin"
                elif network.lower() in ['ethereum', 'eth'] or address.startswith('0x'):
                    balance = self.check_ethereum_balance(address)
                    network = "ethereum"
                else:
                    # Default to Bitcoin check
                    balance = self.check_bitcoin_balance(address)
                    network = "bitcoin"
                
                if balance > 0:
                    funded_count += 1
                    logger.info(f"🎉 FUNDED WALLET FOUND: {address} - {balance} {network.upper()}")
                    
                    result_entry = {
                        'address': address,
                        'balance': balance,
                        'network': network,
                        'timestamp': datetime.now().isoformat(),
                        'key_data': key_data
                    }
                    
                    # Add original key info if it was converted
                    if original_key and original_key != address:
                        result_entry['original_key'] = original_key
                        result_entry['converted'] = True
                    
                    results.append(result_entry)
                
                # Rate limiting for production use
                delay = float(os.getenv('RATE_LIMIT_DELAY', '1.5'))
                time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Error processing key {i}: {e}")
                continue
        
        # Save results
        timestamp = int(time.time())
        results_file = self.results_dir / f"balance_scan_results_{timestamp}.json"
        
        scan_results = {
            'timestamp': datetime.now().isoformat(),
            'keys_scanned': len(keys_to_scan),
            'funded_wallets': funded_count,
            'results': results
        }
        
        with open(results_file, 'w') as f:
            json.dump(scan_results, f, indent=2)
        
        logger.info(f"✅ Scan complete: {len(keys_to_scan)} keys checked, {funded_count} funded wallets found")
        logger.info(f"📄 Results saved to: {results_file.name}")
        
        return scan_results

async def main():
    """Main entry point"""
    scanner = SimpleBalanceScanner()
    results = await scanner.scan_balances(max_keys=50)
    
    if results and results.get('funded_wallets', 0) > 0:
        print(f"\n🎉 SUCCESS: Found {results['funded_wallets']} funded wallets!")
    else:
        print("\n💰 No funded wallets found in this batch")

if __name__ == "__main__":
    asyncio.run(main())
