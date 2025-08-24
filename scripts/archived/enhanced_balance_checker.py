#!/usr/bin/env python3
"""
Enhanced Balance Checker with Proper API Key Management
======================================================
Uses .env file for secure API key management and multiple fallback APIs.
"""

import json
import requests
import time
import logging
from typing import Dict, List, Optional, Tuple
from api_manager import api_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedBalanceChecker:
    """Enhanced balance checker with multiple APIs and proper key management"""
    
    def __init__(self):
        self.rate_limits = api_manager.get_rate_limits()
        self.last_api_call = 0
        self.api_call_count = 0
        
        # Validate API setup
        if not api_manager.has_valid_keys():
            logger.warning("⚠️  No valid API keys found. Some features may not work.")
    
    def _rate_limit(self, delay: float = None):
        """Apply rate limiting between API calls"""
        if delay is None:
            delay = 1.0 / self.rate_limits['default']
        
        current_time = time.time()
        time_since_last = current_time - self.last_api_call
        
        if time_since_last < delay:
            sleep_time = delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_api_call = time.time()
        self.api_call_count += 1
    
    def check_ethereum_balance_multiple_apis(self, address: str) -> Dict:
        """Check Ethereum balance using multiple APIs with fallbacks"""
        
        # Get available Ethereum API keys
        eth_apis = api_manager.get_ethereum_apis()
        
        # Try Etherscan first (most reliable)
        if eth_apis.get('etherscan'):
            result = self._check_ethereum_etherscan(address, eth_apis['etherscan'])
            if result['success']:
                return result
        
        # Try Alchemy as backup
        if eth_apis.get('alchemy'):
            result = self._check_ethereum_alchemy(address, eth_apis['alchemy'])
            if result['success']:
                return result
        
        # Try Infura as backup
        if eth_apis.get('infura'):
            result = self._check_ethereum_infura(address, eth_apis['infura'])
            if result['success']:
                return result
        
        # No working APIs found
        return {
            'success': False,
            'error': 'No working Ethereum APIs available',
            'address': address
        }
    
    def _check_ethereum_etherscan(self, address: str, api_key: str) -> Dict:
        """Check balance using Etherscan API"""
        try:
            self._rate_limit(0.2)  # Etherscan allows 5 calls per second
            
            url = "https://api.etherscan.io/api"
            params = {
                'module': 'account',
                'action': 'balance',
                'address': address,
                'tag': 'latest',
                'apikey': api_key
            }
            
            response = requests.get(
                url, 
                params=params, 
                timeout=self.rate_limits['timeout']
            )
            data = response.json()
            
            if data.get('status') == '1' and 'result' in data:
                balance_wei = int(data['result'])
                balance_eth = balance_wei / 10**18
                
                return {
                    'success': True,
                    'balance_wei': balance_wei,
                    'balance_eth': balance_eth,
                    'has_balance': balance_wei > 0,
                    'api': 'etherscan',
                    'address': address
                }
            else:
                return {
                    'success': False,
                    'error': data.get('message', 'Unknown Etherscan error'),
                    'address': address
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Etherscan API error: {str(e)}",
                'address': address
            }
    
    def _check_ethereum_alchemy(self, address: str, api_key: str) -> Dict:
        """Check balance using Alchemy API"""
        try:
            self._rate_limit(0.1)  # Conservative rate limiting
            
            url = f"https://eth-mainnet.g.alchemy.com/v2/{api_key}"
            
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_getBalance",
                "params": [address, "latest"]
            }
            
            response = requests.post(
                url, 
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=self.rate_limits['timeout']
            )
            data = response.json()
            
            if 'result' in data:
                balance_wei = int(data['result'], 16)  # Convert from hex
                balance_eth = balance_wei / 10**18
                
                return {
                    'success': True,
                    'balance_wei': balance_wei,
                    'balance_eth': balance_eth,
                    'has_balance': balance_wei > 0,
                    'api': 'alchemy',
                    'address': address
                }
            else:
                return {
                    'success': False,
                    'error': data.get('error', {}).get('message', 'Unknown Alchemy error'),
                    'address': address
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Alchemy API error: {str(e)}",
                'address': address
            }
    
    def _check_ethereum_infura(self, address: str, project_id: str) -> Dict:
        """Check balance using Infura API"""
        try:
            self._rate_limit(0.1)  # Conservative rate limiting
            
            url = f"https://mainnet.infura.io/v3/{project_id}"
            
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_getBalance",
                "params": [address, "latest"]
            }
            
            response = requests.post(
                url, 
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=self.rate_limits['timeout']
            )
            data = response.json()
            
            if 'result' in data:
                balance_wei = int(data['result'], 16)  # Convert from hex
                balance_eth = balance_wei / 10**18
                
                return {
                    'success': True,
                    'balance_wei': balance_wei,
                    'balance_eth': balance_eth,
                    'has_balance': balance_wei > 0,
                    'api': 'infura',
                    'address': address
                }
            else:
                return {
                    'success': False,
                    'error': data.get('error', {}).get('message', 'Unknown Infura error'),
                    'address': address
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Infura API error: {str(e)}",
                'address': address
            }
    
    def check_bitcoin_balance_multiple_apis(self, address: str) -> Dict:
        """Check Bitcoin balance using multiple APIs with fallbacks"""
        
        # Get available Bitcoin API keys
        btc_apis = api_manager.get_bitcoin_apis()
        
        # Try BlockCypher first (most reliable)
        if btc_apis.get('blockcypher'):
            result = self._check_bitcoin_blockcypher(address, btc_apis['blockcypher'])
            if result['success']:
                return result
        
        # Try Blockstream as backup (no API key needed)
        result = self._check_bitcoin_blockstream(address)
        if result['success']:
            return result
        
        # Try Blockchain.info as last resort
        if btc_apis.get('blockchain_info'):
            result = self._check_bitcoin_blockchaininfo(address, btc_apis['blockchain_info'])
            if result['success']:
                return result
        
        # No working APIs found
        return {
            'success': False,
            'error': 'No working Bitcoin APIs available',
            'address': address
        }
    
    def _check_bitcoin_blockcypher(self, address: str, api_token: str) -> Dict:
        """Check balance using BlockCypher API"""
        try:
            self._rate_limit(0.5)  # BlockCypher rate limiting
            
            url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance"
            params = {'token': api_token} if api_token else {}
            
            response = requests.get(
                url, 
                params=params,
                timeout=self.rate_limits['timeout']
            )
            data = response.json()
            
            if 'balance' in data:
                balance_satoshi = data['balance']
                balance_btc = balance_satoshi / 10**8
                
                return {
                    'success': True,
                    'balance_satoshi': balance_satoshi,
                    'balance_btc': balance_btc,
                    'has_balance': balance_satoshi > 0,
                    'api': 'blockcypher',
                    'address': address,
                    'unconfirmed_balance': data.get('unconfirmed_balance', 0)
                }
            else:
                return {
                    'success': False,
                    'error': data.get('error', 'Unknown BlockCypher error'),
                    'address': address
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"BlockCypher API error: {str(e)}",
                'address': address
            }
    
    def _check_bitcoin_blockstream(self, address: str) -> Dict:
        """Check balance using Blockstream API (no key required)"""
        try:
            self._rate_limit(1.0)  # Conservative rate limiting for free API
            
            url = f"https://blockstream.info/api/address/{address}"
            
            response = requests.get(url, timeout=self.rate_limits['timeout'])
            data = response.json()
            
            if 'chain_stats' in data:
                stats = data['chain_stats']
                balance_satoshi = stats.get('funded_txo_sum', 0) - stats.get('spent_txo_sum', 0)
                balance_btc = balance_satoshi / 10**8
                
                return {
                    'success': True,
                    'balance_satoshi': balance_satoshi,
                    'balance_btc': balance_btc,
                    'has_balance': balance_satoshi > 0,
                    'api': 'blockstream',
                    'address': address,
                    'tx_count': stats.get('tx_count', 0)
                }
            else:
                return {
                    'success': False,
                    'error': 'Invalid Blockstream response format',
                    'address': address
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Blockstream API error: {str(e)}",
                'address': address
            }
    
    def _check_bitcoin_blockchaininfo(self, address: str, api_key: str) -> Dict:
        """Check balance using Blockchain.info API"""
        try:
            self._rate_limit(1.0)  # Conservative rate limiting
            
            url = f"https://blockchain.info/rawaddr/{address}"
            headers = {'api-key': api_key} if api_key else {}
            
            response = requests.get(
                url, 
                headers=headers,
                timeout=self.rate_limits['timeout']
            )
            data = response.json()
            
            if 'final_balance' in data:
                balance_satoshi = data['final_balance']
                balance_btc = balance_satoshi / 10**8
                
                return {
                    'success': True,
                    'balance_satoshi': balance_satoshi,
                    'balance_btc': balance_btc,
                    'has_balance': balance_satoshi > 0,
                    'api': 'blockchain_info',
                    'address': address,
                    'tx_count': data.get('n_tx', 0)
                }
            else:
                return {
                    'success': False,
                    'error': 'Invalid Blockchain.info response format',
                    'address': address
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Blockchain.info API error: {str(e)}",
                'address': address
            }
    
    def check_address_balance(self, address: str, chain: str = None) -> Dict:
        """Check balance for any address with auto-detection or specified chain"""
        
        # Auto-detect chain if not specified
        if not chain:
            if address.startswith('0x') and len(address) == 42:
                chain = 'ethereum'
            elif address.startswith(('1', '3', 'bc1')):
                chain = 'bitcoin'
            else:
                return {
                    'success': False,
                    'error': 'Could not auto-detect blockchain type',
                    'address': address
                }
        
        # Route to appropriate checker
        if chain.lower() == 'ethereum':
            return self.check_ethereum_balance_multiple_apis(address)
        elif chain.lower() == 'bitcoin':
            return self.check_bitcoin_balance_multiple_apis(address)
        else:
            return {
                'success': False,
                'error': f'Unsupported blockchain: {chain}',
                'address': address
            }
    
    def check_multiple_addresses(self, addresses: List[str]) -> List[Dict]:
        """Check balances for multiple addresses"""
        results = []
        
        print(f"🔍 Checking balances for {len(addresses)} addresses...")
        
        for i, address in enumerate(addresses, 1):
            if i % 10 == 0 or i == len(addresses):
                print(f"   Progress: {i}/{len(addresses)}")
            
            result = self.check_address_balance(address)
            results.append(result)
            
            # Show funded addresses immediately
            if result.get('success') and result.get('has_balance'):
                balance = result.get('balance_eth', result.get('balance_btc', 0))
                currency = 'ETH' if 'balance_eth' in result else 'BTC'
                print(f"💎 FUNDED: {address} = {balance:.6f} {currency}")
        
        return results
    
    def get_api_status(self) -> Dict:
        """Get status of all configured APIs"""
        status = {
            'ethereum_apis': api_manager.get_ethereum_apis(),
            'bitcoin_apis': api_manager.get_bitcoin_apis(),
            'api_calls_made': self.api_call_count,
            'rate_limits': self.rate_limits
        }
        
        return status

def main():
    """Test the enhanced balance checker"""
    print("🔍 ENHANCED BALANCE CHECKER TEST")
    print("=" * 50)
    
    # Validate API setup first
    from api_manager import validate_api_setup
    validate_api_setup()
    
    checker = EnhancedBalanceChecker()
    
    # Test with some known addresses (these should be empty test addresses)
    test_addresses = [
        "0x0000000000000000000000000000000000000000",  # Ethereum burn address
        "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",          # Bitcoin Genesis address
    ]
    
    print(f"\n🧪 Testing balance checker with {len(test_addresses)} addresses...")
    
    results = checker.check_multiple_addresses(test_addresses)
    
    print(f"\n📊 Test Results:")
    for result in results:
        if result['success']:
            print(f"✅ {result['address']}: Success via {result.get('api', 'unknown')} API")
        else:
            print(f"❌ {result['address']}: {result.get('error', 'Unknown error')}")
    
    print(f"\n📈 API Status:")
    status = checker.get_api_status()
    print(f"   • API calls made: {status['api_calls_made']}")
    print(f"   • Ethereum APIs available: {len([k for k in status['ethereum_apis'].values() if k])}")
    print(f"   • Bitcoin APIs available: {len([k for k in status['bitcoin_apis'].values() if k])}")

if __name__ == '__main__':
    main()
