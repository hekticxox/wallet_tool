#!/usr/bin/env python3
"""
API Manager - Centralized API key and endpoint management
========================================================
Handles API keys for various blockchain services
"""

import os
from pathlib import Path

class APIManager:
    """Manages API keys and endpoints for various blockchain services"""
    
    def __init__(self):
        self.api_keys = self.load_api_keys()
    
    def load_api_keys(self):
        """Load API keys from .env file"""
        config_file = Path('.env')
        api_keys = {}
        
        if config_file.exists():
            with open(config_file) as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        api_keys[key] = value.strip('"\'')
        
        return api_keys
    
    def get_ethereum_apis(self):
        """Get Ethereum API configurations"""
        return {
            'etherscan': self.api_keys.get('ETHERSCAN_API_KEY'),
            'infura': self.api_keys.get('INFURA_API_KEY'), 
            'alchemy': self.api_keys.get('ALCHEMY_API_KEY'),
            'moralis': self.api_keys.get('MORALIS_API_KEY')
        }
    
    def get_bitcoin_apis(self):
        """Get Bitcoin API configurations"""
        return {
            'blockcypher': self.api_keys.get('BLOCKCYPHER_API_KEY'),
            'blockstream': None,  # Blockstream API doesn't require keys
            'blockchain_info': None  # Blockchain.info API doesn't require keys
        }
    
    def get_api_key(self, service):
        """Get API key for a specific service"""
        return self.api_keys.get(service)
    
    def has_api_key(self, service):
        """Check if API key exists for a service"""
        return service in self.api_keys and self.api_keys[service] is not None
