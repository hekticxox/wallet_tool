#!/usr/bin/env python3
"""
Multi-Blockchain Wallet Hunter
Support for Bitcoin, Ethereum, and major altcoins
"""

import json
import time
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
import random
import hashlib
import base58
from typing import Dict, List, Any, Optional, Tuple
import re

# Crypto libraries
from web3 import Web3
from eth_keys import keys as eth_keys
from eth_utils import to_checksum_address

# Bitcoin library imports
try:
    import bitcoin
    from bitcoin import privkey_to_address, encode_privkey
    BITCOIN_SUPPORT = True
except ImportError:
    BITCOIN_SUPPORT = False
    print("⚠️  Bitcoin library not available - Bitcoin support disabled")

try:
    import base58
    BASE58_SUPPORT = True
except ImportError:
    BASE58_SUPPORT = False
    print("⚠️  Base58 library not available")

class MultiBlockchainHunter:
    def __init__(self):
        self.session = None
        self.api_keys = {}
        self.results_file = f"MULTI_BLOCKCHAIN_RESULTS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.funded_wallets = []
        self.checked_count = 0
        self.start_time = time.time()
        
        # Supported networks and their configurations
        self.networks = {
            'bitcoin': {
                'name': 'Bitcoin',
                'symbol': 'BTC',
                'api_urls': [
                    'https://blockstream.info/api',
                    'https://api.blockcypher.com/v1/btc/main',
                    'https://api.blockchair.com/bitcoin'
                ],
                'unit_divisor': 100000000,  # Satoshi to BTC
                'address_prefixes': ['1', '3', 'bc1'],
                'private_key_formats': ['WIF', 'hex']
            },
            'ethereum': {
                'name': 'Ethereum',
                'symbol': 'ETH',
                'api_urls': [
                    'https://api.etherscan.io/api',
                    'https://eth-mainnet.alchemyapi.io/v2',
                    'https://mainnet.infura.io/v3'
                ],
                'unit_divisor': 1000000000000000000,  # Wei to ETH
                'address_prefixes': ['0x'],
                'private_key_formats': ['hex']
            },
            'litecoin': {
                'name': 'Litecoin',
                'symbol': 'LTC',
                'api_urls': [
                    'https://api.blockcypher.com/v1/ltc/main',
                    'https://api.blockchair.com/litecoin'
                ],
                'unit_divisor': 100000000,  # Litoshi to LTC
                'address_prefixes': ['L', 'M', '3', 'ltc1'],
                'private_key_formats': ['WIF', 'hex']
            },
            'dogecoin': {
                'name': 'Dogecoin',
                'symbol': 'DOGE',
                'api_urls': [
                    'https://api.blockcypher.com/v1/doge/main',
                    'https://api.blockchair.com/dogecoin'
                ],
                'unit_divisor': 100000000,  # Koinu to DOGE
                'address_prefixes': ['D', '9', 'A'],
                'private_key_formats': ['WIF', 'hex']
            },
            'bitcoin_cash': {
                'name': 'Bitcoin Cash',
                'symbol': 'BCH',
                'api_urls': [
                    'https://api.blockchair.com/bitcoin-cash',
                    'https://rest.bitcoin.com/v2'
                ],
                'unit_divisor': 100000000,  # Satoshi to BCH
                'address_prefixes': ['1', '3', 'q', 'p'],
                'private_key_formats': ['WIF', 'hex']
            }
        }
        
        # Load API configuration
        self.load_api_config()
        
    def load_api_config(self):
        """Load API keys for different blockchain services"""
        try:
            with open('api_config.json', 'r') as f:
                config = json.load(f)
                
            # Extract API keys for different services
            self.api_keys = {
                'etherscan': config.get('etherscan', {}).get('keys', []),
                'blockcypher': config.get('blockcypher', {}).get('keys', []),
                'blockchair': config.get('blockchair', {}).get('keys', []),
                'alchemy': config.get('alchemy', {}).get('keys', []),
                'infura': config.get('infura', {}).get('keys', [])
            }
            
            total_keys = sum(len(keys) for keys in self.api_keys.values())
            print(f"✅ Loaded {total_keys} API keys across {len(self.api_keys)} services")
            
        except Exception as e:
            print(f"⚠️  API config error: {e}")
            # Set up demo keys (replace with real ones)
            self.api_keys = {
                'etherscan': ['demo_etherscan_key'],
                'blockcypher': ['demo_blockcypher_key'],
                'blockchair': ['demo_blockchair_key'],
                'alchemy': ['demo_alchemy_key'],
                'infura': ['demo_infura_key']
            }
    
    def get_api_key(self, service: str) -> str:
        """Get a random API key for a specific service"""
        keys = self.api_keys.get(service, [])
        if not keys or keys == [f'demo_{service}_key']:
            return ""
        return random.choice(keys)
    
    def detect_key_type(self, key: str) -> Tuple[str, str]:
        """Detect the cryptocurrency and format of a private key"""
        key = key.strip()
        
        # Bitcoin WIF format detection
        if len(key) in [51, 52] and key[0] in '5KL':
            return 'bitcoin', 'WIF'
        
        # Litecoin WIF format
        if len(key) in [51, 52] and key[0] in '6T':
            return 'litecoin', 'WIF'
        
        # Dogecoin WIF format
        if len(key) in [51, 52] and key[0] in '6Q':
            return 'dogecoin', 'WIF'
        
        # Ethereum hex format (with or without 0x)
        clean_key = key[2:] if key.startswith('0x') else key
        if len(clean_key) == 64 and all(c in '0123456789abcdefABCDEF' for c in clean_key):
            return 'ethereum', 'hex'
        
        # Generic hex format (could be any crypto)
        if len(clean_key) == 64 and all(c in '0123456789abcdefABCDEF' for c in clean_key):
            return 'bitcoin', 'hex'  # Default to bitcoin for generic hex
        
        return 'unknown', 'unknown'
    
    def private_key_to_address(self, private_key: str, network: str) -> Optional[str]:
        """Convert private key to address for specified network"""
        try:
            network_type, key_format = self.detect_key_type(private_key)
            
            if network == 'bitcoin':
                return self.bitcoin_key_to_address(private_key, key_format)
            elif network == 'ethereum':
                return self.ethereum_key_to_address(private_key, key_format)
            elif network == 'litecoin':
                return self.litecoin_key_to_address(private_key, key_format)
            elif network == 'dogecoin':
                return self.dogecoin_key_to_address(private_key, key_format)
            elif network == 'bitcoin_cash':
                return self.bitcoin_cash_key_to_address(private_key, key_format)
            
            return None
            
        except Exception as e:
            return None
    
    def bitcoin_key_to_address(self, private_key: str, key_format: str) -> Optional[str]:
        """Convert private key to Bitcoin address"""
        if not BITCOIN_SUPPORT:
            return None
        
        try:
            if key_format == 'WIF':
                # WIF to address
                return bitcoin.privkey_to_address(private_key)
            elif key_format == 'hex':
                # Hex to WIF to address
                if private_key.startswith('0x'):
                    private_key = private_key[2:]
                # Convert hex to WIF format
                wif = bitcoin.encode_privkey(private_key, 'wif')
                return bitcoin.privkey_to_address(wif)
            return None
        except Exception:
            return None
    
    def ethereum_key_to_address(self, private_key: str, key_format: str) -> Optional[str]:
        """Convert private key to Ethereum address"""
        try:
            if key_format == 'hex':
                if private_key.startswith('0x'):
                    pk_bytes = bytes.fromhex(private_key[2:])
                else:
                    pk_bytes = bytes.fromhex(private_key)
                
                if len(pk_bytes) != 32:
                    return None
                
                private_key_obj = eth_keys.PrivateKey(pk_bytes)
                return to_checksum_address(private_key_obj.public_key.to_address())
            return None
        except Exception:
            return None
    
    def litecoin_key_to_address(self, private_key: str, key_format: str) -> Optional[str]:
        """Convert private key to Litecoin address"""
        if not BITCOIN_SUPPORT:
            return None
        
        try:
            # Similar to Bitcoin but with different parameters
            if key_format == 'WIF':
                # Use bitcoin library with Litecoin parameters
                return bitcoin.privkey_to_address(private_key, 48)  # Litecoin version byte
            elif key_format == 'hex':
                if private_key.startswith('0x'):
                    private_key = private_key[2:]
                wif = bitcoin.encode_privkey(private_key, 'wif', 176)  # Litecoin WIF version
                return bitcoin.privkey_to_address(wif, 48)
            return None
        except Exception:
            return None
    
    def dogecoin_key_to_address(self, private_key: str, key_format: str) -> Optional[str]:
        """Convert private key to Dogecoin address"""
        if not BITCOIN_SUPPORT:
            return None
        
        try:
            if key_format == 'WIF':
                return bitcoin.privkey_to_address(private_key, 30)  # Dogecoin version byte
            elif key_format == 'hex':
                if private_key.startswith('0x'):
                    private_key = private_key[2:]
                wif = bitcoin.encode_privkey(private_key, 'wif', 158)  # Dogecoin WIF version
                return bitcoin.privkey_to_address(wif, 30)
            return None
        except Exception:
            return None
    
    def bitcoin_cash_key_to_address(self, private_key: str, key_format: str) -> Optional[str]:
        """Convert private key to Bitcoin Cash address"""
        if not BITCOIN_SUPPORT:
            return None
        
        try:
            # Bitcoin Cash uses same format as Bitcoin initially
            if key_format == 'WIF':
                return bitcoin.privkey_to_address(private_key)
            elif key_format == 'hex':
                if private_key.startswith('0x'):
                    private_key = private_key[2:]
                wif = bitcoin.encode_privkey(private_key, 'wif')
                return bitcoin.privkey_to_address(wif)
            return None
        except Exception:
            return None
    
    async def check_bitcoin_balance(self, session: aiohttp.ClientSession, address: str) -> Optional[Dict]:
        """Check Bitcoin balance using multiple APIs"""
        try:
            # Try Blockstream API first
            url = f"https://blockstream.info/api/address/{address}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    balance_satoshi = data.get('chain_stats', {}).get('funded_txo_sum', 0)
                    if balance_satoshi > 0:
                        balance_btc = balance_satoshi / 100000000
                        return {
                            'network': 'bitcoin',
                            'address': address,
                            'balance_native': balance_satoshi,
                            'balance_decimal': balance_btc,
                            'unit': 'BTC',
                            'api_source': 'blockstream'
                        }
            
            await asyncio.sleep(0.2)
            return None
            
        except Exception:
            return None
    
    async def check_ethereum_balance(self, session: aiohttp.ClientSession, address: str) -> Optional[Dict]:
        """Check Ethereum balance using Etherscan API"""
        try:
            api_key = self.get_api_key('etherscan')
            url = "https://api.etherscan.io/api"
            params = {
                'module': 'account',
                'action': 'balance',
                'address': address,
                'tag': 'latest'
            }
            
            if api_key:
                params['apikey'] = api_key
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == '1' and 'result' in data:
                        balance_wei = int(data['result'])
                        if balance_wei > 0:
                            balance_eth = balance_wei / 10**18
                            return {
                                'network': 'ethereum',
                                'address': address,
                                'balance_native': balance_wei,
                                'balance_decimal': balance_eth,
                                'unit': 'ETH',
                                'api_source': 'etherscan'
                            }
            
            await asyncio.sleep(0.2)
            return None
            
        except Exception:
            return None
    
    async def check_litecoin_balance(self, session: aiohttp.ClientSession, address: str) -> Optional[Dict]:
        """Check Litecoin balance using BlockCypher API"""
        try:
            api_key = self.get_api_key('blockcypher')
            url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}/balance"
            params = {}
            
            if api_key:
                params['token'] = api_key
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    balance_litoshi = data.get('balance', 0)
                    if balance_litoshi > 0:
                        balance_ltc = balance_litoshi / 100000000
                        return {
                            'network': 'litecoin',
                            'address': address,
                            'balance_native': balance_litoshi,
                            'balance_decimal': balance_ltc,
                            'unit': 'LTC',
                            'api_source': 'blockcypher'
                        }
            
            await asyncio.sleep(0.2)
            return None
            
        except Exception:
            return None
    
    async def check_dogecoin_balance(self, session: aiohttp.ClientSession, address: str) -> Optional[Dict]:
        """Check Dogecoin balance using BlockCypher API"""
        try:
            api_key = self.get_api_key('blockcypher')
            url = f"https://api.blockcypher.com/v1/doge/main/addrs/{address}/balance"
            params = {}
            
            if api_key:
                params['token'] = api_key
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    balance_koinu = data.get('balance', 0)
                    if balance_koinu > 0:
                        balance_doge = balance_koinu / 100000000
                        return {
                            'network': 'dogecoin',
                            'address': address,
                            'balance_native': balance_koinu,
                            'balance_decimal': balance_doge,
                            'unit': 'DOGE',
                            'api_source': 'blockcypher'
                        }
            
            await asyncio.sleep(0.2)
            return None
            
        except Exception:
            return None
    
    async def check_multi_blockchain_balance(self, session: aiohttp.ClientSession, private_key: str) -> List[Dict]:
        """Check balance across multiple blockchain networks"""
        results = []
        
        # Try each supported network
        for network_name in self.networks.keys():
            try:
                address = self.private_key_to_address(private_key, network_name)
                if not address:
                    continue
                
                balance_result = None
                
                if network_name == 'bitcoin':
                    balance_result = await self.check_bitcoin_balance(session, address)
                elif network_name == 'ethereum':
                    balance_result = await self.check_ethereum_balance(session, address)
                elif network_name == 'litecoin':
                    balance_result = await self.check_litecoin_balance(session, address)
                elif network_name == 'dogecoin':
                    balance_result = await self.check_dogecoin_balance(session, address)
                
                if balance_result:
                    balance_result['private_key'] = private_key
                    balance_result['checked_at'] = datetime.now().isoformat()
                    results.append(balance_result)
                    
                    print(f"\n💰 FUNDED WALLET FOUND!")
                    print(f"    Network: {balance_result['network'].upper()}")
                    print(f"    Address: {balance_result['address']}")
                    print(f"    Balance: {balance_result['balance_decimal']:.8f} {balance_result['unit']}")
                    print(f"    Private Key: {private_key[:20]}...")
                
            except Exception as e:
                continue
        
        return results
    
    async def hunt_multi_blockchain(self, keys_to_check: List[str], max_keys: int = 1000):
        """Hunt for funded wallets across multiple blockchains"""
        if not keys_to_check:
            print("❌ No keys to check")
            return
        
        # Limit keys
        keys_to_process = keys_to_check[:max_keys]
        
        print(f"🚀 Starting multi-blockchain hunt for {len(keys_to_process)} keys")
        print(f"🌐 Networks: {', '.join(self.networks.keys())}")
        
        connector = aiohttp.TCPConnector(limit=30, limit_per_host=15)
        timeout = aiohttp.ClientTimeout(total=120)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            batch_size = 10  # Smaller batches for multi-network checking
            
            for i in range(0, len(keys_to_process), batch_size):
                batch = keys_to_process[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(keys_to_process) + batch_size - 1) // batch_size
                
                print(f"\n🔍 Checking batch {batch_num}/{total_batches} ({len(batch)} keys)...")
                
                # Create tasks for this batch
                tasks = []
                for private_key in batch:
                    task = self.check_multi_blockchain_balance(session, private_key)
                    tasks.append(task)
                
                # Execute batch
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for results_list in batch_results:
                    if isinstance(results_list, list):
                        self.funded_wallets.extend(results_list)
                        if results_list:  # Save immediately when found
                            self.save_results()
                
                self.checked_count += len(batch)
                
                # Progress update
                elapsed = time.time() - self.start_time
                rate = self.checked_count / elapsed if elapsed > 0 else 0
                
                print(f"📊 Progress: {self.checked_count}/{len(keys_to_process)} keys checked")
                print(f"⚡ Rate: {rate:.1f} keys/sec")
                print(f"💰 Funded wallets found: {len(self.funded_wallets)}")
                
                # Longer pause for multi-network checking
                await asyncio.sleep(3)
    
    def load_keys_from_net607(self, limit: int = 1000) -> List[str]:
        """Load keys from NET607 extraction results"""
        try:
            # Find the latest extraction file
            extraction_files = list(Path('.').glob('NET607_COMPREHENSIVE_KEYS_*.json'))
            if not extraction_files:
                print("❌ No NET607 extraction results found")
                return []
            
            latest_file = max(extraction_files, key=lambda x: x.stat().st_mtime)
            print(f"📂 Loading keys from: {latest_file}")
            
            with open(latest_file, 'r') as f:
                data = json.load(f)
            
            # Get high priority keys
            keys = []
            high_priority = data.get('prioritized_keys', {}).get('high_priority', [])
            
            for key_data in high_priority[:limit]:
                key = key_data.get('key', '').strip()
                if key:
                    keys.append(key)
            
            print(f"✅ Loaded {len(keys)} keys for multi-blockchain checking")
            return keys
            
        except Exception as e:
            print(f"❌ Failed to load keys: {e}")
            return []
    
    def save_results(self):
        """Save current results to file"""
        # Organize results by network
        by_network = {}
        total_value_usd = 0  # Placeholder - would need price APIs
        
        for wallet in self.funded_wallets:
            network = wallet['network']
            if network not in by_network:
                by_network[network] = []
            by_network[network].append(wallet)
        
        results = {
            'scan_info': {
                'scan_type': 'multi_blockchain_hunt',
                'started_at': datetime.fromtimestamp(self.start_time).isoformat(),
                'completed_at': datetime.now().isoformat(),
                'keys_checked': self.checked_count,
                'networks_checked': list(self.networks.keys()),
                'funded_wallets_found': len(self.funded_wallets),
                'networks_with_funds': list(by_network.keys())
            },
            'results_by_network': by_network,
            'all_funded_wallets': self.funded_wallets
        }
        
        with open(self.results_file, 'w') as f:
            json.dump(results, f, indent=2)
    
    def print_summary(self):
        """Print final summary"""
        elapsed = time.time() - self.start_time
        
        print(f"\n🎉 MULTI-BLOCKCHAIN HUNT COMPLETE!")
        print(f"==================================================")
        print(f"⏱️  Total Time: {elapsed:.1f} seconds")
        print(f"🔍 Keys Checked: {self.checked_count:,}")
        print(f"⚡ Average Rate: {self.checked_count/elapsed:.1f} keys/sec")
        print(f"🌐 Networks Scanned: {', '.join(self.networks.keys())}")
        print(f"💰 Funded Wallets Found: {len(self.funded_wallets)}")
        
        if self.funded_wallets:
            print(f"\n🏆 FUNDED WALLETS BY NETWORK:")
            by_network = {}
            for wallet in self.funded_wallets:
                network = wallet['network']
                if network not in by_network:
                    by_network[network] = []
                by_network[network].append(wallet)
            
            for network, wallets in by_network.items():
                total_balance = sum(w['balance_decimal'] for w in wallets)
                unit = wallets[0]['unit'] if wallets else ''
                print(f"\n  📊 {network.upper()}: {len(wallets)} wallets, {total_balance:.8f} {unit}")
                
                for wallet in wallets:
                    print(f"    💎 {wallet['address']}: {wallet['balance_decimal']:.8f} {wallet['unit']}")
        
        print(f"\n💾 Results saved to: {self.results_file}")

async def main():
    """Main execution function"""
    hunter = MultiBlockchainHunter()
    
    # Load keys from NET607 results
    keys = hunter.load_keys_from_net607(limit=1000)  # Check top 1000 keys
    
    if not keys:
        print("❌ No keys loaded for checking")
        return
    
    try:
        await hunter.hunt_multi_blockchain(keys, max_keys=1000)
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"❌ Error during hunting: {e}")
    finally:
        hunter.save_results()
        hunter.print_summary()

if __name__ == "__main__":
    print("🌐 MULTI-BLOCKCHAIN WALLET HUNTER")
    print("=" * 50)
    print("🔗 Supported Networks: Bitcoin, Ethereum, Litecoin, Dogecoin, Bitcoin Cash")
    asyncio.run(main())
