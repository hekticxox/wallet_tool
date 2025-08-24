#!/usr/bin/env python3
"""
Simple Hex Key Scanner - Using Bitcoin Library
==============================================
Converts hex private keys to Bitcoin addresses and checks balances
"""

import json
import logging
import requests
import time
import os
import bitcoin
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleHexScanner:
    """Simple scanner for hex private keys using bitcoin library"""
    
    def __init__(self):
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
        
        # Load rate limiting from environment
        self.rate_limit_delay = float(os.getenv('RATE_LIMIT_DELAY', '1.5'))
        
    def hex_to_bitcoin_address(self, hex_key: str) -> str:
        """Convert hex private key to Bitcoin address using bitcoin library"""
        try:
            # Validate hex key format
            if len(hex_key) != 64:
                raise ValueError(f"Invalid hex key length: {len(hex_key)}, expected 64")
            
            # Convert hex to integer
            private_key_int = int(hex_key, 16)
            
            # Convert to public key and then to address
            public_key = bitcoin.privkey_to_pubkey(private_key_int)
            address = bitcoin.pubkey_to_address(public_key)
            
            return address
            
        except Exception as e:
            logger.error(f"Error converting hex key {hex_key[:8]}...{hex_key[-8:]}: {e}")
            return None
    
    def check_balance_blockchain_info(self, address: str) -> float:
        """Check balance using blockchain.info API"""
        try:
            url = f"https://blockchain.info/q/addressbalance/{address}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                balance_satoshis = int(response.text.strip())
                return balance_satoshis
            else:
                logger.warning(f"API error for {address}: {response.status_code}")
                return 0
                
        except Exception as e:
            logger.error(f"Error checking balance for {address}: {e}")
            return 0
    
    def check_balance_blockstream(self, address: str) -> float:
        """Check balance using blockstream.info API (fallback)"""
        try:
            url = f"https://blockstream.info/api/address/{address}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Sum confirmed and unconfirmed balances
                chain_stats = data.get('chain_stats', {})
                mempool_stats = data.get('mempool_stats', {})
                
                confirmed_balance = chain_stats.get('funded_txo_sum', 0) - chain_stats.get('spent_txo_sum', 0)
                unconfirmed_balance = mempool_stats.get('funded_txo_sum', 0) - mempool_stats.get('spent_txo_sum', 0)
                
                total_balance = confirmed_balance + unconfirmed_balance
                return total_balance
            else:
                logger.warning(f"Blockstream API error for {address}: {response.status_code}")
                return 0
                
        except Exception as e:
            logger.error(f"Error checking balance with blockstream for {address}: {e}")
            return 0
    
    def scan_hex_keys_from_file(self, file_path: str, max_keys: int = 10) -> Dict[str, Any]:
        """Scan hex keys from file"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "source_file": file_path,
            "keys_scanned": 0,
            "funded_wallets": 0,
            "results": []
        }
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Filter valid hex keys (64 characters, valid hex)
            hex_keys = []
            for line in lines:
                clean_line = line.strip()
                if clean_line and len(clean_line) == 64:
                    try:
                        # Test if it's valid hex
                        int(clean_line, 16)
                        hex_keys.append(clean_line)
                    except ValueError:
                        continue
            
            logger.info(f"Found {len(hex_keys)} valid hex keys in file")
            
            # Process keys up to max_keys limit
            keys_to_process = hex_keys[:max_keys] if max_keys else hex_keys
            
            for i, hex_key in enumerate(keys_to_process):
                logger.info(f"Processing key {i+1}/{len(keys_to_process)}: {hex_key[:8]}...{hex_key[-8:]}")
                
                # Convert to Bitcoin address
                address = self.hex_to_bitcoin_address(hex_key)
                if not address:
                    continue
                
                logger.info(f"Generated address: {address}")
                
                # Check balance with primary API
                balance = self.check_balance_blockchain_info(address)
                
                # If primary API fails or returns 0, try fallback
                if balance == 0:
                    time.sleep(self.rate_limit_delay)
                    balance = self.check_balance_blockstream(address)
                
                results["keys_scanned"] += 1
                
                if balance > 0:
                    results["funded_wallets"] += 1
                    result_entry = {
                        "hex_key": hex_key,
                        "address": address,
                        "balance_satoshis": balance,
                        "balance_btc": balance / 100000000,
                        "timestamp": datetime.now().isoformat()
                    }
                    results["results"].append(result_entry)
                    logger.info(f"💰 FUNDED WALLET FOUND! Address: {address}, Balance: {balance/100000000:.8f} BTC")
                    print(f"\\n🎉💰 FUNDED WALLET DISCOVERED! 💰🎉")
                    print(f"Address: {address}")
                    print(f"Balance: {balance/100000000:.8f} BTC")
                    print(f"Private Key: {hex_key}")
                    print(f"═══════════════════════════════════════")
                else:
                    logger.info(f"⭕ No balance found for: {address}")
                
                # Rate limiting between requests
                if i < len(keys_to_process) - 1:
                    time.sleep(self.rate_limit_delay)
                
        except Exception as e:
            logger.error(f"Error scanning hex keys: {e}")
            
        return results
    
    def save_results(self, results: Dict[str, Any]) -> str:
        """Save scan results to file"""
        timestamp = int(time.time())
        filename = f"hex_scan_results_{timestamp}.json"
        filepath = self.results_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to: {filepath}")
        return str(filepath)

def main():
    """Main scanning function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple Hex Key Scanner")
    parser.add_argument('--input-file', required=True, help='Input file containing hex keys')
    parser.add_argument('--max-keys', type=int, default=10, help='Maximum number of keys to scan')
    
    args = parser.parse_args()
    
    scanner = SimpleHexScanner()
    
    logger.info(f"🚀 Starting Simple Hex Key Scanner")
    logger.info(f"📁 Input file: {args.input_file}")
    logger.info(f"🔢 Max keys to scan: {args.max_keys}")
    
    # Scan the keys
    results = scanner.scan_hex_keys_from_file(args.input_file, args.max_keys)
    
    # Save results
    results_file = scanner.save_results(results)
    
    # Print summary
    logger.info(f"✅ Scan complete: {results['keys_scanned']} keys checked, {results['funded_wallets']} funded wallets found")
    
    if results['funded_wallets'] > 0:
        print(f"\\n🎉 SUCCESS! FOUND {results['funded_wallets']} FUNDED WALLETS! 🎉")
        print("=" * 60)
        for result in results['results']:
            print(f"💰 Address: {result['address']}")
            print(f"💵 Balance: {result['balance_btc']:.8f} BTC ({result['balance_satoshis']} satoshis)")
            print(f"🔑 Private Key: {result['hex_key']}")
            print("-" * 60)
    else:
        print("\\n💰 No funded wallets found in this batch")
        print("🔄 Try scanning more keys or different key sets")

if __name__ == "__main__":
    main()
