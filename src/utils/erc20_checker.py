#!/usr/bin/env python3
"""
ERC-20 Token Balance Checker - Enhanced Wallet Tool
==================================================

Production-grade ERC-20 token balance checking with multi-API support and database integration.
"""

import os
import sys
import time
import json
import logging
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from Crypto.Hash import keccak
from eth_keys import keys
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TokenInfo:
    """Token information structure"""
    symbol: str
    name: str
    decimals: int
    contract_address: str

@dataclass
class TokenBalance:
    """Token balance result structure"""
    token: TokenInfo
    balance: float
    balance_wei: int
    usd_value: Optional[float] = None

class ERC20TokenChecker:
    """
    Production-grade ERC-20 token balance checker with multi-API fallback
    """
    
    def __init__(self):
        """Initialize with API keys from environment"""
        self.etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')
        self.alchemy_api_key = os.getenv('ALCHEMY_API_KEY') 
        self.infura_project_id = os.getenv('INFURA_PROJECT_ID')
        
        # Popular ERC-20 tokens to check
        self.popular_tokens = {
            'USDT': TokenInfo('USDT', 'Tether USD', 6, '0xdAC17F958D2ee523a2206206994597C13D831ec7'),
            'USDC': TokenInfo('USDC', 'USD Coin', 6, '0xA0b86a33E6441E99bD8ee4C89C98ac02CdDf7b0B'),
            'BNB': TokenInfo('BNB', 'Binance Coin', 18, '0xB8c77482e45F1F44dE1745F52C74426C631bDD52'),
            'LINK': TokenInfo('LINK', 'Chainlink', 18, '0x514910771AF9Ca656af840dff83E8264EcF986CA'),
            'UNI': TokenInfo('UNI', 'Uniswap', 18, '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984'),
            'WETH': TokenInfo('WETH', 'Wrapped Ethereum', 18, '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'),
            'DAI': TokenInfo('DAI', 'Dai Stablecoin', 18, '0x6B175474E89094C44Da98b954EedeAC495271d0F'),
            'SHIB': TokenInfo('SHIB', 'Shiba Inu', 18, '0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE'),
            'MATIC': TokenInfo('MATIC', 'Polygon', 18, '0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0'),
            'CRO': TokenInfo('CRO', 'Cronos', 8, '0xA0b73E1Ff0B80914AB6fe0444E65848C4C34450b')
        }
        
        self.session_timeout = aiohttp.ClientTimeout(total=10)
        
    def private_key_to_address(self, private_key_hex: str) -> str:
        """
        Convert private key to Ethereum address
        """
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
            logger.error(f"Error converting private key to address: {e}")
            return None
    
    async def check_token_balance_etherscan(self, address: str, token: TokenInfo) -> Optional[int]:
        """Check token balance using Etherscan API"""
        if not self.etherscan_api_key:
            return None
            
        try:
            url = f"https://api.etherscan.io/api"
            params = {
                'module': 'account',
                'action': 'tokenbalance', 
                'contractaddress': token.contract_address,
                'address': address,
                'tag': 'latest',
                'apikey': self.etherscan_api_key
            }
            
            async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    
                    if data.get('status') == '1' and data.get('result'):
                        return int(data['result'])
                    return 0
                        
        except Exception as e:
            logger.warning(f"Etherscan API error for {token.symbol}: {e}")
            return None
    
    async def check_token_balance_alchemy(self, address: str, token: TokenInfo) -> Optional[int]:
        """Check token balance using Alchemy API"""
        if not self.alchemy_api_key:
            return None
            
        try:
            url = f"https://eth-mainnet.alchemyapi.io/v2/{self.alchemy_api_key}"
            
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_call",
                "params": [
                    {
                        "to": token.contract_address,
                        "data": f"0x70a08231000000000000000000000000{address[2:].lower()}"  # balanceOf(address)
                    },
                    "latest"
                ],
                "id": 1
            }
            
            async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
                async with session.post(url, json=payload) as response:
                    data = await response.json()
                    
                    if 'result' in data and data['result'] != '0x':
                        return int(data['result'], 16)
                    return 0
                        
        except Exception as e:
            logger.warning(f"Alchemy API error for {token.symbol}: {e}")
            return None
    
    async def check_token_balance_infura(self, address: str, token: TokenInfo) -> Optional[int]:
        """Check token balance using Infura API"""
        if not self.infura_project_id:
            return None
            
        try:
            url = f"https://mainnet.infura.io/v3/{self.infura_project_id}"
            
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_call",
                "params": [
                    {
                        "to": token.contract_address,
                        "data": f"0x70a08231000000000000000000000000{address[2:].lower()}"
                    },
                    "latest"
                ],
                "id": 1
            }
            
            async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
                async with session.post(url, json=payload) as response:
                    data = await response.json()
                    
                    if 'result' in data and data['result'] != '0x':
                        return int(data['result'], 16)
                    return 0
                        
        except Exception as e:
            logger.warning(f"Infura API error for {token.symbol}: {e}")
            return None
    
    async def check_address_for_tokens(self, address: str, private_key_hex: str = None) -> List[TokenBalance]:
        """
        Check all popular tokens for an Ethereum address
        """
        results = []
        
        logger.info(f"🔍 Checking tokens for address: {address}")
        
        for symbol, token in self.popular_tokens.items():
            try:
                # Try multiple APIs for reliability
                balance_wei = None
                
                # Try Etherscan first
                balance_wei = await self.check_token_balance_etherscan(address, token)
                
                # If Etherscan fails, try Alchemy
                if balance_wei is None:
                    balance_wei = await self.check_token_balance_alchemy(address, token)
                
                # If Alchemy fails, try Infura
                if balance_wei is None:
                    balance_wei = await self.check_token_balance_infura(address, token)
                
                if balance_wei is not None and balance_wei > 0:
                    balance = balance_wei / (10 ** token.decimals)
                    results.append(TokenBalance(
                        token=token,
                        balance=balance,
                        balance_wei=balance_wei
                    ))
                    logger.info(f"  💰 Found {balance:.6f} {symbol}")
                
                # Rate limiting
                await asyncio.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Error checking {symbol}: {e}")
                continue
        
        return results
    
    async def check_private_key_for_tokens(self, private_key_hex: str) -> tuple[str, List[TokenBalance]]:
        """
        Check a private key for ERC-20 tokens
        """
        address = self.private_key_to_address(private_key_hex)
        if not address:
            logger.error(f"Could not derive address from private key")
            return None, []
        
        token_balances = await self.check_address_for_tokens(address, private_key_hex)
        return address, token_balances

def main():
    """Main function for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ERC-20 Token Balance Checker')
    parser.add_argument('--private-key', '-k', help='Private key to check (hex)')
    parser.add_argument('--address', '-a', help='Ethereum address to check')
    parser.add_argument('--test', action='store_true', help='Run with test data')
    
    args = parser.parse_args()
    
    checker = ERC20TokenChecker()
    
    async def run_check():
        if args.private_key:
            address, tokens = await checker.check_private_key_for_tokens(args.private_key)
            print(f"\n🔍 Address: {address}")
            if tokens:
                print(f"💰 Found {len(tokens)} tokens with balance:")
                for token_balance in tokens:
                    print(f"  • {token_balance.balance:.6f} {token_balance.token.symbol} ({token_balance.token.name})")
            else:
                print("  No token balances found")
                
        elif args.address:
            tokens = await checker.check_address_for_tokens(args.address)
            print(f"\n🔍 Address: {args.address}")
            if tokens:
                print(f"💰 Found {len(tokens)} tokens with balance:")
                for token_balance in tokens:
                    print(f"  • {token_balance.balance:.6f} {token_balance.token.symbol} ({token_balance.token.name})")
            else:
                print("  No token balances found")
                
        elif args.test:
            # Test with a known address that has tokens (Vitalik's address)
            test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
            print(f"🧪 Testing with address: {test_address}")
            tokens = await checker.check_address_for_tokens(test_address)
            if tokens:
                print(f"💰 Found {len(tokens)} tokens with balance:")
                for token_balance in tokens:
                    print(f"  • {token_balance.balance:.6f} {token_balance.token.symbol}")
            else:
                print("  No token balances found")
        else:
            print("Please provide --private-key, --address, or --test")
    
    asyncio.run(run_check())

if __name__ == "__main__":
    main()
