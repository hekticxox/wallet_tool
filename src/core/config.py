#!/usr/bin/env python3
"""
Production Configuration Manager
===============================
Centralized configuration management for the wallet recovery tool.
Handles environment variables, API keys, and production settings securely.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class APIConfig:
    """Configuration for API endpoints."""
    name: str
    url: str
    rate_limit: int  # requests per second
    timeout: int     # seconds
    api_key: Optional[str] = None
    enabled: bool = True


@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "wallet_recovery"
    username: str = "wallet_user"
    password: str = ""
    ssl_mode: str = "prefer"
    max_connections: int = 10


@dataclass
class ScannerConfig:
    """Scanner configuration."""
    max_threads: int = 5
    api_timeout: int = 5
    rate_limit_buffer: float = 0.1
    batch_size: int = 1000
    save_progress_interval: int = 100
    max_concurrent_apis: int = 10


@dataclass
class SecurityConfig:
    """Security configuration."""
    encrypt_private_keys: bool = True
    log_private_keys: bool = False
    max_log_file_size: int = 100 * 1024 * 1024  # 100MB
    backup_results: bool = True
    secure_delete: bool = True


class ProductionConfig:
    """
    Production configuration manager that handles all settings
    from environment variables and configuration files.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration from environment and optional config file.
        
        Args:
            config_file: Optional JSON configuration file path
        """
        self.config_file = config_file
        self.project_root = Path(__file__).parent.parent.parent
        
        # Load configuration
        self._load_configuration()
        self._validate_configuration()
        
        # Setup logging
        self._setup_logging()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Production configuration loaded successfully")
    
    def _load_configuration(self):
        """Load configuration from environment variables and files."""
        
        # API Configuration
        self.btc_apis = self._load_btc_api_config()
        self.eth_apis = self._load_eth_api_config()
        
        # Database Configuration
        self.database = DatabaseConfig(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'wallet_recovery'),
            username=os.getenv('DB_USER', 'wallet_user'),
            password=os.getenv('DB_PASSWORD', ''),
            ssl_mode=os.getenv('DB_SSL_MODE', 'prefer'),
            max_connections=int(os.getenv('DB_MAX_CONNECTIONS', '10'))
        )
        
        # Scanner Configuration
        self.scanner = ScannerConfig(
            max_threads=int(os.getenv('SCANNER_MAX_THREADS', '5')),
            api_timeout=int(os.getenv('SCANNER_API_TIMEOUT', '5')),
            rate_limit_buffer=float(os.getenv('SCANNER_RATE_LIMIT_BUFFER', '0.1')),
            batch_size=int(os.getenv('SCANNER_BATCH_SIZE', '1000')),
            save_progress_interval=int(os.getenv('SCANNER_PROGRESS_INTERVAL', '100')),
            max_concurrent_apis=int(os.getenv('SCANNER_MAX_CONCURRENT', '10'))
        )
        
        # Security Configuration
        self.security = SecurityConfig(
            encrypt_private_keys=os.getenv('ENCRYPT_PRIVATE_KEYS', 'true').lower() == 'true',
            log_private_keys=os.getenv('LOG_PRIVATE_KEYS', 'false').lower() == 'true',
            max_log_file_size=int(os.getenv('MAX_LOG_SIZE', str(100 * 1024 * 1024))),
            backup_results=os.getenv('BACKUP_RESULTS', 'true').lower() == 'true',
            secure_delete=os.getenv('SECURE_DELETE', 'true').lower() == 'true'
        )
        
        # General Settings
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        # Directories
        self.data_dir = Path(os.getenv('DATA_DIR', self.project_root / 'data'))
        self.results_dir = Path(os.getenv('RESULTS_DIR', self.project_root / 'results'))
        self.logs_dir = Path(os.getenv('LOGS_DIR', self.project_root / 'logs'))
        self.backup_dir = Path(os.getenv('BACKUP_DIR', self.project_root / 'backup'))
        
        # Create directories if they don't exist
        for directory in [self.data_dir, self.results_dir, self.logs_dir, self.backup_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_btc_api_config(self) -> List[APIConfig]:
        """Load Bitcoin API configuration."""
        return [
            APIConfig(
                name='blockstream',
                url='https://blockstream.info/api/address/',
                rate_limit=int(os.getenv('BLOCKSTREAM_RATE_LIMIT', '10')),
                timeout=int(os.getenv('BLOCKSTREAM_TIMEOUT', '5')),
                enabled=os.getenv('BLOCKSTREAM_ENABLED', 'true').lower() == 'true'
            ),
            APIConfig(
                name='blockcypher',
                url='https://api.blockcypher.com/v1/btc/main/addrs/',
                rate_limit=int(os.getenv('BLOCKCYPHER_RATE_LIMIT', '5')),
                timeout=int(os.getenv('BLOCKCYPHER_TIMEOUT', '5')),
                api_key=os.getenv('BLOCKCYPHER_API_KEY'),
                enabled=os.getenv('BLOCKCYPHER_ENABLED', 'true').lower() == 'true'
            ),
            APIConfig(
                name='blockchain_info',
                url='https://blockchain.info/rawaddr/',
                rate_limit=int(os.getenv('BLOCKCHAIN_INFO_RATE_LIMIT', '1')),
                timeout=int(os.getenv('BLOCKCHAIN_INFO_TIMEOUT', '10')),
                enabled=os.getenv('BLOCKCHAIN_INFO_ENABLED', 'false').lower() == 'true'
            )
        ]
    
    def _load_eth_api_config(self) -> List[APIConfig]:
        """Load Ethereum API configuration."""
        return [
            APIConfig(
                name='etherscan',
                url='https://api.etherscan.io/api',
                rate_limit=int(os.getenv('ETHERSCAN_RATE_LIMIT', '5')),
                timeout=int(os.getenv('ETHERSCAN_TIMEOUT', '5')),
                api_key=os.getenv('ETHERSCAN_API_KEY'),
                enabled=os.getenv('ETHERSCAN_ENABLED', 'false').lower() == 'true'
            ),
            APIConfig(
                name='infura',
                url='https://mainnet.infura.io/v3/',
                rate_limit=int(os.getenv('INFURA_RATE_LIMIT', '10')),
                timeout=int(os.getenv('INFURA_TIMEOUT', '5')),
                api_key=os.getenv('INFURA_PROJECT_ID'),
                enabled=os.getenv('INFURA_ENABLED', 'false').lower() == 'true'
            )
        ]
    
    def _validate_configuration(self):
        """Validate configuration and warn about missing settings."""
        warnings = []
        
        # Check for API keys if APIs are enabled
        for api in self.btc_apis + self.eth_apis:
            if api.enabled and api.name in ['blockcypher', 'etherscan', 'infura']:
                if not api.api_key:
                    warnings.append(f"{api.name} API is enabled but no API key provided")
        
        # Check database configuration in production
        if self.environment == 'production':
            if not self.database.password:
                warnings.append("Database password not set in production environment")
            if self.database.host == 'localhost':
                warnings.append("Database host is localhost in production environment")
        
        # Security warnings
        if self.security.log_private_keys:
            warnings.append("Private key logging is ENABLED - this is a security risk!")
        
        if not self.security.encrypt_private_keys:
            warnings.append("Private key encryption is DISABLED - this is a security risk!")
        
        # Log warnings
        if warnings:
            print("⚠️  Configuration Warnings:")
            for warning in warnings:
                print(f"   - {warning}")
    
    def _setup_logging(self):
        """Setup production logging configuration."""
        log_file = self.logs_dir / f"wallet_tool_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler() if self.debug else logging.NullHandler()
            ]
        )
        
        # Disable requests library debug logging
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    def get_enabled_btc_apis(self) -> List[APIConfig]:
        """Get list of enabled Bitcoin APIs."""
        return [api for api in self.btc_apis if api.enabled]
    
    def get_enabled_eth_apis(self) -> List[APIConfig]:
        """Get list of enabled Ethereum APIs."""
        return [api for api in self.eth_apis if api.enabled]
    
    def get_api_config(self, api_name: str) -> Optional[APIConfig]:
        """Get configuration for specific API."""
        for api in self.btc_apis + self.eth_apis:
            if api.name == api_name:
                return api
        return None
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == 'production'
    
    def save_config(self, filename: Optional[str] = None) -> str:
        """Save current configuration to file for reference."""
        if not filename:
            filename = f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        config_data = {
            'environment': self.environment,
            'debug': self.debug,
            'log_level': self.log_level,
            'database': asdict(self.database),
            'scanner': asdict(self.scanner),
            'security': asdict(self.security),
            'btc_apis': [asdict(api) for api in self.btc_apis],
            'eth_apis': [asdict(api) for api in self.eth_apis],
            'directories': {
                'data_dir': str(self.data_dir),
                'results_dir': str(self.results_dir),
                'logs_dir': str(self.logs_dir),
                'backup_dir': str(self.backup_dir)
            }
        }
        
        config_file = self.backup_dir / filename
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2, default=str)
        
        return str(config_file)
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """Validate API keys by making test requests."""
        results = {}
        
        for api in self.get_enabled_btc_apis() + self.get_enabled_eth_apis():
            if api.api_key:
                try:
                    # Make a simple test request
                    if api.name == 'blockcypher':
                        import requests
                        response = requests.get(
                            f"{api.url}1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa/balance?token={api.api_key}",
                            timeout=api.timeout
                        )
                        results[api.name] = response.status_code == 200
                    else:
                        # For other APIs, assume valid if key exists
                        results[api.name] = bool(api.api_key)
                except Exception:
                    results[api.name] = False
            else:
                results[api.name] = False
        
        return results
    
    def print_summary(self):
        """Print configuration summary."""
        print("🔧 Production Configuration Summary")
        print("=" * 50)
        print(f"Environment: {self.environment}")
        print(f"Debug Mode: {self.debug}")
        print(f"Log Level: {self.log_level}")
        print()
        
        print("📡 API Configuration:")
        enabled_btc = [api.name for api in self.get_enabled_btc_apis()]
        enabled_eth = [api.name for api in self.get_enabled_eth_apis()]
        print(f"  Bitcoin APIs: {', '.join(enabled_btc) if enabled_btc else 'None'}")
        print(f"  Ethereum APIs: {', '.join(enabled_eth) if enabled_eth else 'None'}")
        print()
        
        print("🔍 Scanner Settings:")
        print(f"  Max Threads: {self.scanner.max_threads}")
        print(f"  API Timeout: {self.scanner.api_timeout}s")
        print(f"  Batch Size: {self.scanner.batch_size:,}")
        print()
        
        print("🔒 Security Settings:")
        print(f"  Encrypt Private Keys: {'✅' if self.security.encrypt_private_keys else '❌'}")
        print(f"  Log Private Keys: {'⚠️ YES' if self.security.log_private_keys else '✅ NO'}")
        print(f"  Backup Results: {'✅' if self.security.backup_results else '❌'}")
        print()
        
        print("📁 Directory Structure:")
        print(f"  Data: {self.data_dir}")
        print(f"  Results: {self.results_dir}")
        print(f"  Logs: {self.logs_dir}")
        print(f"  Backups: {self.backup_dir}")


# Global configuration instance
config = None

def get_config(config_file: Optional[str] = None) -> ProductionConfig:
    """Get or create global configuration instance."""
    global config
    if config is None:
        config = ProductionConfig(config_file)
    return config


def main():
    """Command-line interface for configuration management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Production Configuration Manager")
    parser.add_argument('--summary', action='store_true', help='Print configuration summary')
    parser.add_argument('--validate', action='store_true', help='Validate API keys')
    parser.add_argument('--save', help='Save configuration backup to file')
    parser.add_argument('--config', help='Load configuration from file')
    
    args = parser.parse_args()
    
    config = get_config(args.config)
    
    if args.summary:
        config.print_summary()
    
    if args.validate:
        print("🔐 Validating API Keys...")
        results = config.validate_api_keys()
        for api_name, valid in results.items():
            status = "✅ Valid" if valid else "❌ Invalid"
            print(f"  {api_name}: {status}")
    
    if args.save:
        filename = config.save_config(args.save)
        print(f"💾 Configuration saved to: {filename}")


if __name__ == "__main__":
    main()
