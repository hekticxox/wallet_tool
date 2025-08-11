#!/usr/bin/env python3
"""
Accessible Wallet Balance Checker
Check the balance of accessible wallets with private keys
"""

import json
import requests
import time
from typing import Dict, List
import logging

class AccessibleWalletBalanceChecker:
    """Check balances for accessible wallets"""
    
    def __init__(self):
        self.api_delays = {
            'bitcoin': 1,  # Seconds between API calls
            'ethereum': 0.5
        }
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def load_accessible_wallets(self, filename: str = 'accessible_wallets_report.json') -> List[Dict]:
        """Load accessible wallets from file"""
        with open(filename, 'r') as f:
            data = json.load(f)
        return data['accessible_wallets']
    
    def convert_private_key_to_address(self, private_key: str, chain: str = 'bitcoin') -> str:
        """Convert private key to address"""
        try:
            if chain == 'bitcoin':
                return self._bitcoin_private_key_to_address(private_key)
            elif chain == 'ethereum':
                return self._ethereum_private_key_to_address(private_key)
        except Exception as e:
            self.logger.warning(f"Error converting private key {private_key[:10]}...: {e}")
        return None
    
    def _bitcoin_private_key_to_address(self, private_key: str) -> str:
        """Convert Bitcoin private key to address (simplified)"""
        # This is a simplified version - in practice you'd use a Bitcoin library
        # For now, we'll work with the addresses already extracted
        return None
    
    def _ethereum_private_key_to_address(self, private_key: str) -> str:
        """Convert Ethereum private key to address"""
        try:
            from eth_keys import keys
            from eth_utils import to_checksum_address
            
            # Remove 0x prefix if present
            if private_key.startswith('0x'):
                private_key = private_key[2:]
            
            # Convert to private key object
            if len(private_key) == 64:  # Hex private key
                pk = keys.PrivateKey(bytes.fromhex(private_key))
                address = to_checksum_address(pk.public_key.to_address())
                return address
        except Exception as e:
            self.logger.warning(f"Error converting Ethereum private key: {e}")
        return None
    
    def check_bitcoin_address_balance(self, address: str) -> Dict:
        """Check Bitcoin address balance using BlockCypher API"""
        try:
            url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                balance_satoshi = data.get('balance', 0)
                balance_btc = balance_satoshi / 100000000  # Convert to BTC
                
                return {
                    'address': address,
                    'balance': balance_btc,
                    'balance_satoshi': balance_satoshi,
                    'has_funds': balance_btc > 0,
                    'api': 'blockcypher'
                }
        except Exception as e:
            self.logger.warning(f"Error checking Bitcoin balance for {address}: {e}")
        
        return {'address': address, 'balance': 0, 'has_funds': False, 'error': True}
    
    def check_ethereum_address_balance(self, address: str) -> Dict:
        """Check Ethereum address balance using Etherscan API"""
        try:
            # Try multiple APIs
            apis = [
                f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey=YourApiKeyToken",
                f"https://blockscout.com/eth/mainnet/api?module=account&action=balance&address={address}"
            ]
            
            for api_url in apis:
                try:
                    response = requests.get(api_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'result' in data:
                            balance_wei = int(data['result'])
                            balance_eth = balance_wei / 1000000000000000000  # Convert to ETH
                            
                            return {
                                'address': address,
                                'balance': balance_eth,
                                'balance_wei': balance_wei,
                                'has_funds': balance_eth > 0,
                                'api': 'etherscan' if 'etherscan' in api_url else 'blockscout'
                            }
                except Exception as e:
                    continue
        
        except Exception as e:
            self.logger.warning(f"Error checking Ethereum balance for {address}: {e}")
        
        return {'address': address, 'balance': 0, 'has_funds': False, 'error': True}
    
    def check_wallet_balances(self, max_wallets: int = 100) -> List[Dict]:
        """Check balances for accessible wallets"""
        accessible_wallets = self.load_accessible_wallets()
        
        print(f"🔍 Checking balances for top {max_wallets} accessible wallets...")
        print("="*70)
        
        funded_wallets = []
        checked_addresses = set()
        
        for i, wallet in enumerate(accessible_wallets[:max_wallets]):
            print(f"⏳ Checking wallet {i+1}/{min(max_wallets, len(accessible_wallets))}: {wallet['source'].split('/')[-1]}")
            
            # Check addresses from the wallet
            addresses = wallet.get('addresses', [])
            private_keys = wallet.get('private_keys', [])
            
            wallet_results = {
                'wallet': wallet,
                'address_balances': [],
                'total_btc': 0,
                'total_eth': 0,
                'has_funds': False
            }
            
            # Check existing addresses
            for address in addresses:
                if address in checked_addresses:
                    continue
                checked_addresses.add(address)
                
                # Determine if it's Bitcoin or Ethereum address
                if self._is_bitcoin_address(address):
                    result = self.check_bitcoin_address_balance(address)
                    if result['has_funds']:
                        wallet_results['total_btc'] += result['balance']
                        wallet_results['has_funds'] = True
                        print(f"   💰 Bitcoin address {address}: {result['balance']} BTC")
                    wallet_results['address_balances'].append(result)
                    time.sleep(self.api_delays['bitcoin'])
                
                elif self._is_ethereum_address(address):
                    result = self.check_ethereum_address_balance(address)
                    if result['has_funds']:
                        wallet_results['total_eth'] += result['balance']
                        wallet_results['has_funds'] = True
                        print(f"   💰 Ethereum address {address}: {result['balance']} ETH")
                    wallet_results['address_balances'].append(result)
                    time.sleep(self.api_delays['ethereum'])
            
            # Check addresses derived from private keys
            for private_key in private_keys:
                # Try to derive Ethereum address
                eth_address = self._ethereum_private_key_to_address(private_key)
                if eth_address and eth_address not in checked_addresses:
                    checked_addresses.add(eth_address)
                    result = self.check_ethereum_address_balance(eth_address)
                    if result['has_funds']:
                        wallet_results['total_eth'] += result['balance']
                        wallet_results['has_funds'] = True
                        print(f"   🔑 Derived Ethereum address {eth_address}: {result['balance']} ETH")
                        print(f"       Private Key: {private_key[:10]}...{private_key[-10:]}")
                    wallet_results['address_balances'].append(result)
                    time.sleep(self.api_delays['ethereum'])
            
            if wallet_results['has_funds']:
                funded_wallets.append(wallet_results)
                print(f"   ✅ FUNDED WALLET: {wallet_results['total_btc']} BTC + {wallet_results['total_eth']} ETH")
            
            print()
        
        return funded_wallets
    
    def _is_bitcoin_address(self, address: str) -> bool:
        """Check if address is Bitcoin format"""
        if len(address) < 26 or len(address) > 62:
            return False
        return address.startswith(('1', '3', 'bc1'))
    
    def _is_ethereum_address(self, address: str) -> bool:
        """Check if address is Ethereum format"""
        import re
        return bool(re.match(r'^0x[a-fA-F0-9]{40}$', address))
    
    def _ethereum_private_key_to_address(self, private_key: str) -> str:
        """Convert Ethereum private key to address"""
        try:
            from eth_keys import keys
            from eth_utils import to_checksum_address
            
            # Remove 0x prefix if present
            if private_key.startswith('0x'):
                private_key = private_key[2:]
            
            # Skip WIF format keys (Bitcoin)
            if len(private_key) in [51, 52] and private_key[0] in ['5', 'K', 'L']:
                return None
            
            # Only process 64-character hex keys
            if len(private_key) == 64 and all(c in '0123456789abcdefABCDEF' for c in private_key):
                pk = keys.PrivateKey(bytes.fromhex(private_key))
                address = to_checksum_address(pk.public_key.to_address())
                return address
        except Exception:
            pass
        return None
    
    def generate_report(self, funded_wallets: List[Dict]):
        """Generate final report"""
        if not funded_wallets:
            print("❌ No funded wallets found")
            return
        
        print("\n" + "="*70)
        print("💰 FUNDED ACCESSIBLE WALLETS REPORT")
        print("="*70)
        
        total_btc = sum(w['total_btc'] for w in funded_wallets)
        total_eth = sum(w['total_eth'] for w in funded_wallets)
        
        print(f"🎉 Found {len(funded_wallets)} funded wallets!")
        print(f"💰 Total value: {total_btc:.8f} BTC + {total_eth:.6f} ETH")
        print()
        
        for i, wallet in enumerate(funded_wallets, 1):
            print(f"{i}. Source: {wallet['wallet']['source']}")
            print(f"   Funds: {wallet['total_btc']:.8f} BTC + {wallet['total_eth']:.6f} ETH")
            print(f"   Private Keys: {len(wallet['wallet']['private_keys'])}")
            
            # Show funded addresses
            for addr_result in wallet['address_balances']:
                if addr_result.get('has_funds', False):
                    print(f"   💰 {addr_result['address']}: {addr_result['balance']} {'BTC' if 'satoshi' in addr_result else 'ETH'}")
            print()
        
        # Save report
        report_data = {
            'summary': {
                'funded_wallets_count': len(funded_wallets),
                'total_btc': total_btc,
                'total_eth': total_eth
            },
            'funded_wallets': funded_wallets
        }
        
        with open('funded_accessible_wallets.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"💾 Report saved to: funded_accessible_wallets.json")
        print("="*70)

def main():
    """Main function"""
    checker = AccessibleWalletBalanceChecker()
    
    print("🔍 ACCESSIBLE WALLET BALANCE CHECKER")
    print("="*50)
    print("Checking balances for wallets with private keys...")
    print()
    
    try:
        funded_wallets = checker.check_wallet_balances(max_wallets=50)  # Check top 50
        checker.generate_report(funded_wallets)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
