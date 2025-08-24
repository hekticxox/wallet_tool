#!/usr/bin/env python3
"""
Main Unified Wallet Scanner
==========================
Production-ready, modular, async wallet scanner integrating:
- Database integration
- Bitcoin, Ethereum, ERC-20, multi-chain balance checking
- Continuous monitoring
- Advanced reporting
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Set up environment variables (can be loaded from .env in production)
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_PORT', '5432')
os.environ.setdefault('DB_NAME', 'wallet_recovery')
os.environ.setdefault('DB_USER', 'wallet_admin')
os.environ.setdefault('DB_PASSWORD', 'secure_wallet_pass_2024')
os.environ.setdefault('ETHERSCAN_API_KEY', 'YourEtherscanAPIKey')
os.environ.setdefault('ALCHEMY_API_KEY', 'YourAlchemyAPIKey')
os.environ.setdefault('INFURA_API_KEY', 'YourInfuraAPIKey')
os.environ.setdefault('BLOCKCYPHER_API_KEY', 'YourBlockCypherAPIKey')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('main_scanner.log')
    ]
)
logger = logging.getLogger(__name__)

# Import core modules
from database_integration import DatabaseIntegratedScanner
from erc20_checker import ERC20TokenChecker
from multichain_checker import MultiChainWalletChecker
from continuous_monitor import ContinuousWalletMonitor

class MainUnifiedWalletScanner:
    """
    Unified wallet scanner with all features integrated
    """
    def __init__(self):
        self.db_scanner = DatabaseIntegratedScanner()
        self.erc20_checker = ERC20TokenChecker()
        self.multichain_checker = MultiChainWalletChecker()
        self.monitor = ContinuousWalletMonitor()
        logger.info("🚀 Main Unified Wallet Scanner initialized")

    async def run_comprehensive_scan(self, batch_size: int = 50, max_keys: Optional[int] = None) -> Dict[str, Any]:
        """
        Run comprehensive scan: DB, multi-chain, ERC-20, reporting
        """
        logger.info("💎 COMPREHENSIVE SCAN - All Networks + Tokens")
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_keys_checked': 0,
            'funded_bitcoin_wallets': [],
            'funded_ethereum_wallets': [],
            'token_wallets': [],
            'multichain_wallets': [],
            'api_calls_made': 0,
            'errors': []
        }
        try:
            # Get keys from database
            with self.db_scanner.db_service.db_manager.engine.connect() as conn:
                from sqlalchemy import text
                query = text("SELECT id, key_hex FROM private_keys")
                if max_keys:
                    query = text(f"SELECT id, key_hex FROM private_keys LIMIT {max_keys}")
                else:
                    query = text(f"SELECT id, key_hex FROM private_keys LIMIT {batch_size}")
                key_rows = conn.execute(query).fetchall()
                keys = [(row[0], row[1]) for row in key_rows]
            results['total_keys_checked'] = len(keys)
            logger.info(f"📊 Checking {len(keys)} keys from database...")
            # Multi-chain and ERC-20 checks
            for key_id, key_hex in keys:
                try:
                    btc_result = self.multichain_checker.check_bitcoin_balance(key_hex)
                    eth_result = self.multichain_checker.check_ethereum_balance(key_hex)
                    erc20_result = self.erc20_checker.check_erc20_balances(key_hex)
                    results['funded_bitcoin_wallets'].append(btc_result)
                    results['funded_ethereum_wallets'].append(eth_result)
                    results['token_wallets'].append(erc20_result)
                    results['api_calls_made'] += 3
                except Exception as e:
                    logger.error(f"Error checking key {key_id}: {e}")
                    results['errors'].append(str(e))
            # Monitoring (optional)
            self.monitor.run_monitoring_cycle()
            logger.info("✅ Comprehensive scan complete.")
        except Exception as e:
            logger.error(f"❌ Scan failed: {e}")
            results['errors'].append(str(e))
        return results

async def main():
    scanner = MainUnifiedWalletScanner()
    results = await scanner.run_comprehensive_scan()
    logger.info(f"Scan results: {results}")

if __name__ == "__main__":
    asyncio.run(main())
