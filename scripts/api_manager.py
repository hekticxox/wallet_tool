#!/usr/bin/env python3
"""
API Configuration Manager
=========================
Securely loads and manages API keys from .env file for wallet recovery tools.
"""

import os
from pathlib import Path
from typing import Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIManager:
    """Secure API key manager with fallback options"""
    
    def __init__(self, env_file: str = ".env"):
        self.env_file = Path(env_file)
        self.api_keys = {}
        self._load_environment()
    
    def _load_environment(self):
        """Load environment variables from .env file"""
        if self.env_file.exists():
            try:
                with open(self.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            # Also set as environment variable
                            os.environ[key.strip()] = value.strip()
                            self.api_keys[key.strip()] = value.strip()
                
                logger.info(f"✅ Loaded {len(self.api_keys)} configuration entries from {self.env_file}")
            except Exception as e:
                logger.error(f"❌ Error loading .env file: {e}")
        else:
            logger.warning(f"⚠️  .env file not found at {self.env_file}")
    
    def get_api_key(self, service: str, fallback: Optional[str] = None) -> Optional[str]:
        """Get API key for a service with fallback options"""
        # Try different key naming conventions
        possible_keys = [
            f"{service.upper()}_API_KEY",
            f"{service.upper()}_TOKEN", 
            f"{service.upper()}_KEY",
            service.upper()
        ]
        
        for key in possible_keys:
            # Check environment variables first
            value = os.getenv(key)
            if value and value != "YourApiKeyHere" and value != "":
                return value
            
            # Check loaded keys
            value = self.api_keys.get(key)
            if value and value != "YourApiKeyHere" and value != "":
                return value
        
        if fallback:
            logger.warning(f"⚠️  Using fallback API key for {service}")
            return fallback
        
        logger.warning(f"❌ No API key found for {service}")
        return None
    
    def get_ethereum_apis(self) -> Dict[str, Optional[str]]:
        """Get all available Ethereum API keys"""
        return {
            'etherscan': self.get_api_key('etherscan'),
            'infura': self.get_api_key('infura'),
            'alchemy': self.get_api_key('alchemy'),
            'moralis': self.get_api_key('moralis')
        }
    
    def get_bitcoin_apis(self) -> Dict[str, Optional[str]]:
        """Get all available Bitcoin API keys"""
        return {
            'blockcypher': self.get_api_key('blockcypher'),
            'blockstream': self.get_api_key('blockstream'),
            'blockchain_info': self.get_api_key('blockchain_info')
        }
    
    def get_multi_chain_apis(self) -> Dict[str, Optional[str]]:
        """Get all available multi-chain API keys"""
        return {
            'covalent': self.get_api_key('covalent'),
            'ankr': self.get_api_key('ankr'),
            'moralis': self.get_api_key('moralis')
        }
    
    def get_rpc_urls(self) -> Dict[str, str]:
        """Get RPC URLs for different networks"""
        return {
            'ethereum': os.getenv('ETHEREUM_RPC_URL', 'https://mainnet.infura.io/v3/'),
            'bitcoin': os.getenv('BITCOIN_RPC_URL', 'https://api.blockcypher.com/v1/btc/main'),
            'polygon': os.getenv('POLYGON_RPC_URL', 'https://polygon-rpc.com'),
            'bsc': os.getenv('BSC_RPC_URL', 'https://bsc-dataseed1.binance.org')
        }
    
    def get_rate_limits(self) -> Dict[str, int]:
        """Get API rate limiting configuration"""
        return {
            'default': int(os.getenv('DEFAULT_RATE_LIMIT', 5)),
            'premium': int(os.getenv('PREMIUM_RATE_LIMIT', 10)),
            'timeout': int(os.getenv('API_TIMEOUT', 30))
        }
    
    def has_valid_keys(self) -> bool:
        """Check if we have at least some valid API keys"""
        eth_keys = self.get_ethereum_apis()
        btc_keys = self.get_bitcoin_apis()
        
        # Check if we have at least one working key for each major chain
        has_eth = any(key for key in eth_keys.values() if key)
        has_btc = any(key for key in btc_keys.values() if key)
        
        return has_eth or has_btc
    
    def validate_setup(self) -> Dict[str, any]:
        """Validate API configuration and return status"""
        status = {
            'env_file_exists': self.env_file.exists(),
            'total_keys_loaded': len(self.api_keys),
            'ethereum_apis_available': len([k for k in self.get_ethereum_apis().values() if k]),
            'bitcoin_apis_available': len([k for k in self.get_bitcoin_apis().values() if k]),
            'has_sufficient_apis': self.has_valid_keys(),
            'issues': []
        }
        
        if not status['env_file_exists']:
            status['issues'].append(f".env file not found at {self.env_file}")
        
        if status['total_keys_loaded'] == 0:
            status['issues'].append("No API keys loaded from .env file")
        
        if not status['has_sufficient_apis']:
            status['issues'].append("No valid API keys found for major blockchain networks")
        
        return status

# Global API manager instance
api_manager = APIManager()

def get_api_key(service: str, fallback: Optional[str] = None) -> Optional[str]:
    """Convenience function to get API key"""
    return api_manager.get_api_key(service, fallback)

def get_ethereum_api_key() -> Optional[str]:
    """Get the best available Ethereum API key"""
    apis = api_manager.get_ethereum_apis()
    # Priority order: Etherscan > Alchemy > Infura > Moralis
    for service in ['etherscan', 'alchemy', 'infura', 'moralis']:
        if apis.get(service):
            return apis[service]
    return None

def get_bitcoin_api_key() -> Optional[str]:
    """Get the best available Bitcoin API key"""
    apis = api_manager.get_bitcoin_apis()
    # Priority order: BlockCypher > Blockstream > Blockchain.info
    for service in ['blockcypher', 'blockstream', 'blockchain_info']:
        if apis.get(service):
            return apis[service]
    return None

def validate_api_setup() -> None:
    """Validate and report API configuration status"""
    print("🔑 API CONFIGURATION VALIDATION")
    print("=" * 50)
    
    status = api_manager.validate_setup()
    
    print(f"📁 .env file exists: {'✅' if status['env_file_exists'] else '❌'}")
    print(f"📊 Total keys loaded: {status['total_keys_loaded']}")
    print(f"🔗 Ethereum APIs available: {status['ethereum_apis_available']}")
    print(f"₿  Bitcoin APIs available: {status['bitcoin_apis_available']}")
    print(f"✅ Sufficient APIs: {'Yes' if status['has_sufficient_apis'] else 'No'}")
    
    if status['issues']:
        print(f"\n⚠️  Issues found:")
        for issue in status['issues']:
            print(f"   • {issue}")
        print()
        print("💡 To fix these issues:")
        print(f"   1. Edit the .env file with your API keys")
        print(f"   2. Get free API keys from:")
        print(f"      • Etherscan.io (Ethereum)")
        print(f"      • BlockCypher.com (Bitcoin)")
        print(f"      • Infura.io (Ethereum)")
        print(f"      • Alchemy.com (Multi-chain)")
    else:
        print(f"\n🎉 API configuration looks good!")
    
    print("=" * 50)

if __name__ == '__main__':
    validate_api_setup()
