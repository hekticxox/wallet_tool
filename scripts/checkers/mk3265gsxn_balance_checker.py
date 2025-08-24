#!/usr/bin/env python3
"""
MK3265GSXN Multi-Blockchain Balance Checker
Check extracted keys against multiple blockchain networks
"""

import os
import json
import requests
import time
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'/home/admin/wallet_tool/MK3265GSXN_BALANCE_CHECK_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class MK3265GSXNBalanceChecker:
    def __init__(self):
        self.results_file = f"/home/admin/wallet_tool/MK3265GSXN_BALANCE_RESULTS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # API configuration
        try:
            with open('/home/admin/wallet_tool/api_config.json', 'r') as f:
                self.api_config = json.load(f)
        except:
            logger.warning("API config not found, using defaults")
            self.api_config = {}
        
        self.funded_wallets = []
        self.checked_count = 0
        
    def check_ethereum_balance(self, address):
        """Check Ethereum balance using Etherscan API."""
        try:
            api_key = self.api_config.get('etherscan_api_key', os.getenv('ETHERSCAN_API_KEY', 'REPLACE_WITH_YOUR_KEY'))
            url = f"https://api.etherscan.io/api"
            params = {
                'module': 'account',
                'action': 'balance',
                'address': address,
                'tag': 'latest',
                'apikey': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('status') == '1':
                balance_wei = int(data.get('result', '0'))
                balance_eth = balance_wei / 1e18
                return balance_eth
            else:
                logger.debug(f"Etherscan API error for {address}: {data.get('message', 'Unknown error')}")
                return 0
                
        except Exception as e:
            logger.debug(f"Error checking Ethereum balance for {address}: {e}")
            return 0

    def check_bitcoin_balance(self, address):
        """Check Bitcoin balance using BlockCypher API."""
        try:
            url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if 'balance' in data:
                balance_satoshi = data['balance']
                balance_btc = balance_satoshi / 1e8
                return balance_btc
            else:
                return 0
                
        except Exception as e:
            logger.debug(f"Error checking Bitcoin balance for {address}: {e}")
            return 0

    def derive_ethereum_address(self, private_key):
        """Derive Ethereum address from private key."""
        try:
            from eth_keys import keys
            # Remove 0x prefix if present
            if private_key.startswith('0x'):
                private_key = private_key[2:]
            
            # Convert to bytes
            private_key_bytes = bytes.fromhex(private_key)
            private_key_obj = keys.PrivateKey(private_key_bytes)
            public_key = private_key_obj.public_key
            address = public_key.to_checksum_address()
            return address
        except Exception as e:
            logger.debug(f"Error deriving Ethereum address: {e}")
            return None

    def derive_bitcoin_address(self, private_key):
        """Derive Bitcoin address from private key."""
        try:
            from bit import Key
            # Try to create Bitcoin key
            btc_key = Key.from_hex(private_key)
            return btc_key.address
        except Exception as e:
            logger.debug(f"Error deriving Bitcoin address: {e}")
            return None

    def check_key_balances(self, key_info):
        """Check balances for a single key across multiple networks."""
        key_value = key_info['key']
        results = {
            'key': key_value,
            'type': key_info.get('type', 'unknown'),
            'file': key_info.get('file', 'unknown'),
            'balances': {},
            'addresses': {},
            'total_value_usd': 0,
            'checked_at': datetime.now().isoformat()
        }
        
        # Try to derive and check Ethereum
        if key_info.get('type') in ['ethereum_private_key', 'bitcoin_private_key_hex'] and len(key_value) == 64:
            eth_address = self.derive_ethereum_address(key_value)
            if eth_address:
                results['addresses']['ethereum'] = eth_address
                eth_balance = self.check_ethereum_balance(eth_address)
                if eth_balance > 0:
                    results['balances']['ethereum'] = eth_balance
                    results['total_value_usd'] += eth_balance * 2000  # Rough ETH price
                    logger.info(f"💰 FUNDED ETH: {eth_address} = {eth_balance:.6f} ETH")
        
        # Try to derive and check Bitcoin
        if key_info.get('type') in ['bitcoin_private_key_hex', 'ethereum_private_key'] and len(key_value) == 64:
            btc_address = self.derive_bitcoin_address(key_value)
            if btc_address:
                results['addresses']['bitcoin'] = btc_address
                btc_balance = self.check_bitcoin_balance(btc_address)
                if btc_balance > 0:
                    results['balances']['bitcoin'] = btc_balance
                    results['total_value_usd'] += btc_balance * 30000  # Rough BTC price
                    logger.info(f"💰 FUNDED BTC: {btc_address} = {btc_balance:.8f} BTC")
        
        # Check if it's already a Bitcoin address
        if key_info.get('type') == 'bitcoin_address':
            btc_balance = self.check_bitcoin_balance(key_value)
            if btc_balance > 0:
                results['addresses']['bitcoin'] = key_value
                results['balances']['bitcoin'] = btc_balance
                results['total_value_usd'] += btc_balance * 30000
                logger.info(f"💰 FUNDED BTC ADDRESS: {key_value} = {btc_balance:.8f} BTC")
        
        # Check if it's already an Ethereum address
        if key_info.get('type') == 'ethereum_address':
            eth_balance = self.check_ethereum_balance(key_value)
            if eth_balance > 0:
                results['addresses']['ethereum'] = key_value
                results['balances']['ethereum'] = eth_balance
                results['total_value_usd'] += eth_balance * 2000
                logger.info(f"💰 FUNDED ETH ADDRESS: {key_value} = {eth_balance:.6f} ETH")
        
        return results

    def load_hunt_results(self):
        """Load the latest hunt results."""
        hunt_files = []
        for file in Path('/home/admin/wallet_tool/').glob('MK3265GSXN_HUNT_RESULTS_*.json'):
            hunt_files.append(file)
        
        if not hunt_files:
            logger.error("No hunt results found!")
            return []
        
        # Get the most recent file
        latest_file = max(hunt_files, key=os.path.getmtime)
        logger.info(f"Loading hunt results from: {latest_file}")
        
        try:
            with open(latest_file, 'r') as f:
                data = json.load(f)
            return data.get('keys_found', [])
        except Exception as e:
            logger.error(f"Error loading hunt results: {e}")
            return []

    def run_balance_check(self):
        """Run balance checking on all extracted keys."""
        logger.info("=== MK3265GSXN Balance Checker Started ===")
        
        # Load hunt results
        keys = self.load_hunt_results()
        if not keys:
            logger.error("No keys to check!")
            return
        
        logger.info(f"Checking balances for {len(keys)} keys...")
        
        # Sort keys by type (prioritize likely crypto keys)
        crypto_priorities = [
            'ethereum_private_key', 'bitcoin_private_key_hex', 'bitcoin_private_key_wif',
            'bitcoin_address', 'ethereum_address', 'xprv_key', 'base58_key'
        ]
        
        def key_priority(key_info):
            key_type = key_info.get('type', 'unknown')
            if key_type in crypto_priorities:
                return crypto_priorities.index(key_type)
            return 999
        
        keys.sort(key=key_priority)
        
        # Check each key
        all_results = []
        
        for i, key_info in enumerate(keys):
            try:
                logger.info(f"Checking key {i+1}/{len(keys)}: {key_info.get('type', 'unknown')} from {Path(key_info.get('file', 'unknown')).name}")
                
                result = self.check_key_balances(key_info)
                all_results.append(result)
                self.checked_count += 1
                
                # Track funded wallets
                if result['balances']:
                    self.funded_wallets.append(result)
                    logger.info(f"🎉 FUNDED WALLET FOUND! Total value: ${result['total_value_usd']:.2f}")
                
                # Rate limiting
                time.sleep(0.5)  # Be nice to APIs
                
                # Save progress periodically
                if i % 50 == 0:
                    self.save_results(all_results)
                
            except Exception as e:
                logger.error(f"Error checking key {i+1}: {e}")
        
        # Final save
        self.save_results(all_results)
        
        # Summary
        logger.info("=== Balance Check Complete ===")
        logger.info(f"Keys checked: {self.checked_count}")
        logger.info(f"Funded wallets found: {len(self.funded_wallets)}")
        
        if self.funded_wallets:
            total_value = sum(wallet['total_value_usd'] for wallet in self.funded_wallets)
            logger.info(f"💰 TOTAL ESTIMATED VALUE: ${total_value:.2f}")
            
            for wallet in self.funded_wallets:
                logger.info(f"  - {wallet['addresses']} = ${wallet['total_value_usd']:.2f}")
        
        logger.info(f"Results saved to: {self.results_file}")

    def save_results(self, results):
        """Save balance check results."""
        try:
            summary = {
                'drive': 'MK3265GSXN',
                'check_time': datetime.now().isoformat(),
                'total_keys_checked': len(results),
                'funded_wallets_count': len(self.funded_wallets),
                'total_estimated_value_usd': sum(wallet['total_value_usd'] for wallet in self.funded_wallets),
                'funded_wallets': self.funded_wallets,
                'all_results': results
            }
            
            with open(self.results_file, 'w') as f:
                json.dump(summary, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving results: {e}")

if __name__ == "__main__":
    checker = MK3265GSXNBalanceChecker()
    try:
        checker.run_balance_check()
        print(f"\n✅ Balance check completed!")
        print(f"📁 Results saved to: {checker.results_file}")
        if checker.funded_wallets:
            total_value = sum(wallet['total_value_usd'] for wallet in checker.funded_wallets)
            print(f"💰 TOTAL FOUND: ${total_value:.2f} across {len(checker.funded_wallets)} wallets!")
    except KeyboardInterrupt:
        logger.info("Balance check interrupted by user")
        print("\n⚠️ Balance check interrupted by user")
    except Exception as e:
        logger.error(f"Balance check failed: {e}")
        print(f"\n❌ Balance check failed: {e}")
