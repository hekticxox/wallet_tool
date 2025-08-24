#!/usr/bin/env python3
"""
Multi-Chain Wallet Balance Checker - Enhanced Wallet Tool
========================================================

Production-grade multi-blockchain balance checking with API fallbacks.
Supports: Bitcoin, Ethereum, Polygon, Binance Smart Chain, Avalanche, Arbitrum
"""

import os
import sys
import json
import logging
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import requests
import hashlib
import base58
from Crypto.Hash import keccak
from eth_keys import keys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BlockchainNetwork(Enum):
    """Supported blockchain networks"""
    BITCOIN = "bitcoin"
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    BSC = "bsc"  # Binance Smart Chain
    AVALANCHE = "avalanche"
    ARBITRUM = "arbitrum"

@dataclass
class NetworkConfig:
    """Network configuration"""
    name: str
    symbol: str
    decimal_places: int
    api_endpoints: List[str]
    address_format: str
    
    # API-specific settings
    etherscan_api_key_var: Optional[str] = None
    custom_api_key_var: Optional[str] = None

@dataclass
class WalletBalance:
    """Wallet balance result"""
    network: BlockchainNetwork
    address: str
    balance: float
    balance_wei: Optional[int] = None
    usd_value: Optional[float] = None

class MultiChainWalletChecker:
    """
    Production-grade multi-chain wallet balance checker
    """
    
    def __init__(self):
        """Initialize with API keys and network configurations"""
        self.session_timeout = aiohttp.ClientTimeout(total=15)
        
        # Network configurations
        self.networks = {
            BlockchainNetwork.BITCOIN: NetworkConfig(
                name="Bitcoin",
                symbol="BTC", 
                decimal_places=8,
                api_endpoints=[
                    "https://blockstream.info/api",
                    "https://blockchair.com/bitcoin/api",
                    "https://api.blockcypher.com/v1/btc/main"
                ],
                address_format="base58",
                custom_api_key_var="BLOCKCYPHER_TOKEN"
            ),
            BlockchainNetwork.ETHEREUM: NetworkConfig(
                name="Ethereum",
                symbol="ETH",
                decimal_places=18,
                api_endpoints=[
                    "https://api.etherscan.io/api",
                    "https://eth-mainnet.alchemyapi.io/v2",
                    "https://mainnet.infura.io/v3"
                ],
                address_format="ethereum",
                etherscan_api_key_var="ETHERSCAN_API_KEY"
            ),
            BlockchainNetwork.POLYGON: NetworkConfig(
                name="Polygon",
                symbol="MATIC",
                decimal_places=18,
                api_endpoints=[
                    "https://api.polygonscan.com/api",
                    "https://polygon-mainnet.g.alchemy.com/v2"
                ],
                address_format="ethereum",
                etherscan_api_key_var="POLYGONSCAN_API_KEY"
            ),
            BlockchainNetwork.BSC: NetworkConfig(
                name="Binance Smart Chain",
                symbol="BNB",
                decimal_places=18,
                api_endpoints=[
                    "https://api.bscscan.com/api",
                    "https://bsc-dataseed1.binance.org"
                ],
                address_format="ethereum",
                etherscan_api_key_var="BSCSCAN_API_KEY"
            ),
            BlockchainNetwork.AVALANCHE: NetworkConfig(
                name="Avalanche",
                symbol="AVAX",
                decimal_places=18,
                api_endpoints=[
                    "https://api.avax.network/ext/bc/C/rpc",
                    "https://api.snowtrace.io/api"
                ],
                address_format="ethereum",
                etherscan_api_key_var="SNOWTRACE_API_KEY"
            ),
            BlockchainNetwork.ARBITRUM: NetworkConfig(
                name="Arbitrum",
                symbol="ARB",
                decimal_places=18,
                api_endpoints=[
                    "https://api.arbiscan.io/api",
                    "https://arb1.arbitrum.io/rpc"
                ],
                address_format="ethereum",
                etherscan_api_key_var="ARBISCAN_API_KEY"
            )
        }
        
        # Load API keys
        self.api_keys = {
            'ETHERSCAN_API_KEY': os.getenv('ETHERSCAN_API_KEY'),
            'POLYGONSCAN_API_KEY': os.getenv('POLYGONSCAN_API_KEY'),
            'BSCSCAN_API_KEY': os.getenv('BSCSCAN_API_KEY'),
            'SNOWTRACE_API_KEY': os.getenv('SNOWTRACE_API_KEY'),
            'ARBISCAN_API_KEY': os.getenv('ARBISCAN_API_KEY'),
            'BLOCKCYPHER_TOKEN': os.getenv('BLOCKCYPHER_TOKEN'),
            'ALCHEMY_API_KEY': os.getenv('ALCHEMY_API_KEY'),
            'INFURA_PROJECT_ID': os.getenv('INFURA_PROJECT_ID')
        }
    
    def private_key_to_bitcoin_address(self, private_key_hex: str) -> str:
        """Convert private key to Bitcoin address (P2PKH)"""
        try:
            # Remove '0x' prefix if present
            if private_key_hex.startswith('0x'):
                private_key_hex = private_key_hex[2:]
            
            # Create private key
            private_key_int = int(private_key_hex, 16)
            
            # Generate public key (compressed)
            import ecdsa
            sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key_hex), curve=ecdsa.SECP256k1)
            public_key = b'\\x03' + sk.get_verifying_key().to_string()[:32]  # Compressed
            
            # Hash public key
            sha256_hash = hashlib.sha256(public_key).digest()
            ripemd160 = hashlib.new('ripemd160')
            ripemd160.update(sha256_hash)
            public_key_hash = ripemd160.digest()
            
            # Add version byte (0x00 for mainnet P2PKH)
            versioned_payload = b'\\x00' + public_key_hash
            
            # Calculate checksum
            checksum = hashlib.sha256(hashlib.sha256(versioned_payload).digest()).digest()[:4]
            
            # Create final address
            address_bytes = versioned_payload + checksum
            bitcoin_address = base58.b58encode(address_bytes).decode('utf-8')
            
            return bitcoin_address
            
        except Exception as e:
            logger.error(f"Error converting private key to Bitcoin address: {e}")
            return None
    
    def private_key_to_ethereum_address(self, private_key_hex: str) -> str:
        """Convert private key to Ethereum address"""
        try:
            # Remove '0x' prefix if present
            if private_key_hex.startswith('0x'):
                private_key_hex = private_key_hex[2:]
            
            # Create private key object
            private_key_bytes = bytes.fromhex(private_key_hex)
            private_key = keys.PrivateKey(private_key_bytes)
            
            # Get public key and address
            public_key = private_key.public_key
            eth_address = public_key.to_checksum_address()
            
            return eth_address
            
        except Exception as e:
            logger.error(f"Error converting private key to Ethereum address: {e}")
            return None
    
    async def check_bitcoin_balance_blockstream(self, address: str) -> Optional[int]:
        """Check Bitcoin balance using Blockstream API"""
        try:
            url = f"https://blockstream.info/api/address/{address}"
            
            async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('chain_stats', {}).get('funded_txo_sum', 0) - data.get('chain_stats', {}).get('spent_txo_sum', 0)
            return 0
            
        except Exception as e:
            logger.warning(f"Blockstream API error: {e}")
            return None
    
    async def check_bitcoin_balance_blockcypher(self, address: str) -> Optional[int]:
        """Check Bitcoin balance using BlockCypher API"""
        try:
            token = self.api_keys.get('BLOCKCYPHER_TOKEN')
            url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance"
            params = {'token': token} if token else {}
            
            async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('balance', 0)
            return 0
            
        except Exception as e:
            logger.warning(f"BlockCypher API error: {e}")
            return None
    
    async def check_ethereum_balance_etherscan(self, address: str, network: BlockchainNetwork) -> Optional[int]:
        """Check Ethereum-compatible balance using Etherscan-like API"""
        try:
            config = self.networks[network]
            api_key_var = config.etherscan_api_key_var
            api_key = self.api_keys.get(api_key_var) if api_key_var else None
            
            if network == BlockchainNetwork.ETHEREUM:
                base_url = "https://api.etherscan.io/api"
            elif network == BlockchainNetwork.POLYGON:
                base_url = "https://api.polygonscan.com/api"
            elif network == BlockchainNetwork.BSC:
                base_url = "https://api.bscscan.com/api"
            elif network == BlockchainNetwork.AVALANCHE:
                base_url = "https://api.snowtrace.io/api"
            elif network == BlockchainNetwork.ARBITRUM:
                base_url = "https://api.arbiscan.io/api"
            else:
                return None
            
            params = {
                'module': 'account',
                'action': 'balance',
                'address': address,
                'tag': 'latest'
            }
            
            if api_key:
                params['apikey'] = api_key
            
            async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == '1' and data.get('result'):
                            return int(data['result'])
            return 0
            
        except Exception as e:
            logger.warning(f"{network.value} API error: {e}")
            return None
    
    async def check_balance_for_network(self, private_key_hex: str, network: BlockchainNetwork) -> Optional[WalletBalance]:
        """Check balance for a specific network"""
        try:
            config = self.networks[network]
            
            # Generate address based on network
            if network == BlockchainNetwork.BITCOIN:
                address = self.private_key_to_bitcoin_address(private_key_hex)
                if not address:
                    return None
                
                # Try multiple Bitcoin APIs
                balance_satoshi = await self.check_bitcoin_balance_blockstream(address)
                if balance_satoshi is None:
                    balance_satoshi = await self.check_bitcoin_balance_blockcypher(address)
                
                if balance_satoshi is not None and balance_satoshi > 0:
                    balance_btc = balance_satoshi / (10 ** config.decimal_places)
                    return WalletBalance(
                        network=network,
                        address=address,
                        balance=balance_btc,
                        balance_wei=balance_satoshi
                    )
            
            else:  # Ethereum-compatible networks
                address = self.private_key_to_ethereum_address(private_key_hex)
                if not address:
                    return None
                
                # Try Etherscan-like API
                balance_wei = await self.check_ethereum_balance_etherscan(address, network)
                
                if balance_wei is not None and balance_wei > 0:
                    balance = balance_wei / (10 ** config.decimal_places)
                    return WalletBalance(
                        network=network,
                        address=address,
                        balance=balance,
                        balance_wei=balance_wei
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking {network.value}: {e}")
            return None
    
    async def check_all_networks(self, private_key_hex: str) -> List[WalletBalance]:
        """Check balance across all supported networks"""
        logger.info(f"🔍 Checking private key across all networks...")
        
        results = []
        
        # Create tasks for all networks
        tasks = []
        for network in self.networks.keys():
            task = self.check_balance_for_network(private_key_hex, network)
            tasks.append((network, task))
        
        # Execute all tasks concurrently
        for network, task in tasks:
            try:
                result = await task
                if result and result.balance > 0:
                    results.append(result)
                    logger.info(f"  💰 {network.value.upper()}: {result.balance:.6f} {self.networks[network].symbol}")
                await asyncio.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.warning(f"Error checking {network.value}: {e}")
        
        return results
    
    def format_results(self, results: List[WalletBalance]) -> str:
        """Format results for display"""
        if not results:
            return "No balances found across all networks"
        
        output = []
        output.append(f"🌍 MULTI-CHAIN BALANCE RESULTS")
        output.append("=" * 50)
        
        total_networks = len(results)
        output.append(f"Found balances on {total_networks} network(s):")
        output.append("")
        
        for result in results:
            config = self.networks[result.network]
            output.append(f"  🔗 {config.name} ({config.symbol})")
            output.append(f"     Address: {result.address}")
            output.append(f"     Balance: {result.balance:.8f} {config.symbol}")
            output.append("")
        
        return "\\n".join(output)

def main():
    """Main function for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Multi-Chain Wallet Balance Checker')
    parser.add_argument('--private-key', '-k', help='Private key to check (hex)')
    parser.add_argument('--network', '-n', choices=[net.value for net in BlockchainNetwork], help='Specific network to check')
    parser.add_argument('--test', action='store_true', help='Run with test data')
    
    args = parser.parse_args()
    
    checker = MultiChainWalletChecker()
    
    async def run_check():
        if args.private_key:
            if args.network:
                network = BlockchainNetwork(args.network)
                result = await checker.check_balance_for_network(args.private_key, network)
                if result:
                    print(f"💰 Found balance: {result.balance:.8f} {checker.networks[network].symbol}")
                    print(f"   Address: {result.address}")
                else:
                    print(f"No balance found on {network.value}")
            else:
                results = await checker.check_all_networks(args.private_key)
                print(checker.format_results(results))
                
        elif args.test:
            # Test with a sample private key (this won't have real funds)
            test_key = "0123456789abcdef" * 4  # Sample 64-char hex
            print(f"🧪 Testing with sample private key...")
            results = await checker.check_all_networks(test_key)
            print(checker.format_results(results))
            
        else:
            print("Please provide --private-key or --test")
    
    asyncio.run(run_check())

if __name__ == "__main__":
    main()
