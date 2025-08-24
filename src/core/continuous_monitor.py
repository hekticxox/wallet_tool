#!/usr/bin/env python3
"""
Continuous Wallet Monitoring Service - Enhanced Wallet Tool
==========================================================

Production-grade continuous monitoring service that:
- Monitors database for new keys and checks their balances
- Performs periodic re-checks of existing keys  
- Integrates ERC-20 token and multi-chain checking
- Provides real-time notifications and alerts
- Scales automatically with configurable batch sizes and intervals
"""

import os
import sys
import time
import json
import logging
import asyncio
import signal
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import threading

# Add production paths
sys.path.append('/home/admin/wallet_tool_production')
sys.path.append('/home/admin/wallet_tool')

from database_integration import DatabaseIntegratedScanner
from erc20_checker import ERC20TokenChecker
from multichain_checker import MultiChainWalletChecker, BlockchainNetwork

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/admin/wallet_tool/monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MonitoringConfig:
    """Configuration for the monitoring service"""
    # Scanning intervals (seconds)
    new_keys_check_interval: int = 300  # 5 minutes
    balance_recheck_interval: int = 3600  # 1 hour
    token_check_interval: int = 7200  # 2 hours
    multichain_check_interval: int = 1800  # 30 minutes
    
    # Batch processing
    batch_size: int = 50
    max_concurrent_checks: int = 10
    
    # API rate limiting
    api_delay_seconds: float = 0.5
    max_api_retries: int = 3
    
    # Alerting
    alert_on_funded_wallets: bool = True
    alert_on_token_balances: bool = True
    alert_on_multichain_balances: bool = True
    
    # Persistence
    save_results_to_db: bool = True
    export_results_to_json: bool = True
    export_file_path: str = '/home/admin/wallet_tool/monitoring_results.json'

@dataclass
class MonitoringResult:
    """Result of a monitoring check"""
    key_id: str
    key_hex: str
    bitcoin_address: str
    ethereum_address: str
    timestamp: datetime
    
    # Balance results
    bitcoin_balance: float = 0.0
    ethereum_balance: float = 0.0
    erc20_tokens: List[Dict] = None
    multichain_balances: List[Dict] = None
    
    # Metadata
    check_type: str = "periodic"
    api_calls_made: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.erc20_tokens is None:
            self.erc20_tokens = []
        if self.multichain_balances is None:
            self.multichain_balances = []
        if self.errors is None:
            self.errors = []

class ContinuousWalletMonitor:
    """
    Continuous wallet monitoring service
    """
    
    def __init__(self, config: MonitoringConfig = None):
        """Initialize monitoring service"""
        self.config = config or MonitoringConfig()
        self.running = False
        self.shutdown_requested = False
        
        # Core components
        self.db_scanner = DatabaseIntegratedScanner()
        self.erc20_checker = ERC20TokenChecker()
        self.multichain_checker = MultiChainWalletChecker()
        
        # Monitoring state
        self.last_key_check = None
        self.last_balance_check = None
        self.last_token_check = None
        self.last_multichain_check = None
        
        # Results storage
        self.recent_results = []
        self.stats = {
            'total_keys_monitored': 0,
            'funded_wallets_found': 0,
            'token_wallets_found': 0,
            'multichain_wallets_found': 0,
            'total_api_calls': 0,
            'uptime_start': datetime.now()
        }
        
        # Thread pool for concurrent processing
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_checks)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("🔧 Continuous Wallet Monitor initialized")
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown_requested = True
    
    async def check_new_keys(self) -> List[MonitoringResult]:
        """Check for new keys added to database since last check"""
        logger.info("🆕 Checking for new keys in database...")
        
        results = []
        
        try:
            # Get keys that haven't been balance-checked recently
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            # Get a batch of unchecked keys
            with self.db_scanner.db_service.db_manager.get_session() as session:
                from sqlalchemy import text
                query = text("""
                    SELECT id, key_hex, bitcoin_address 
                    FROM private_keys 
                    WHERE last_tested_at IS NULL OR last_tested_at < :cutoff
                    LIMIT :batch_size
                """)
                
                rows = session.execute(query, {
                    'cutoff': cutoff_time,
                    'batch_size': self.config.batch_size
                }).fetchall()
                
                logger.info(f"Found {len(rows)} keys to check")
                
                for row in rows:
                    try:
                        result = await self._check_single_key(
                            key_id=str(row[0]),
                            key_hex=row[1],
                            check_type="new_key"
                        )
                        if result:
                            results.append(result)
                            
                        # Rate limiting
                        await asyncio.sleep(self.config.api_delay_seconds)
                        
                    except Exception as e:
                        logger.error(f"Error checking key {row[0]}: {e}")
                        
        except Exception as e:
            logger.error(f"Error in new key check: {e}")
        
        self.last_key_check = datetime.now()
        logger.info(f"✅ Completed new key check: {len(results)} results")
        return results
    
    async def periodic_balance_recheck(self) -> List[MonitoringResult]:
        """Perform periodic re-check of existing keys"""
        logger.info("🔄 Performing periodic balance recheck...")
        
        results = []
        
        try:
            # Get keys that were last tested more than recheck interval ago
            cutoff_time = datetime.now() - timedelta(seconds=self.config.balance_recheck_interval)
            
            with self.db_scanner.db_service.db_manager.get_session() as session:
                from sqlalchemy import text
                query = text("""
                    SELECT id, key_hex, bitcoin_address
                    FROM private_keys 
                    WHERE last_tested_at < :cutoff
                    ORDER BY last_tested_at ASC
                    LIMIT :batch_size
                """)
                
                rows = session.execute(query, {
                    'cutoff': cutoff_time,
                    'batch_size': self.config.batch_size // 2  # Smaller batches for rechecks
                }).fetchall()
                
                logger.info(f"Found {len(rows)} keys for recheck")
                
                for row in rows:
                    try:
                        result = await self._check_single_key(
                            key_id=str(row[0]),
                            key_hex=row[1],
                            check_type="recheck"
                        )
                        if result:
                            results.append(result)
                            
                        await asyncio.sleep(self.config.api_delay_seconds)
                        
                    except Exception as e:
                        logger.error(f"Error rechecking key {row[0]}: {e}")
                        
        except Exception as e:
            logger.error(f"Error in periodic recheck: {e}")
        
        self.last_balance_check = datetime.now()
        logger.info(f"✅ Completed periodic recheck: {len(results)} results")
        return results
    
    async def _check_single_key(self, key_id: str, key_hex: str, check_type: str) -> Optional[MonitoringResult]:
        """Check a single key across all supported methods"""
        try:
            result = MonitoringResult(
                key_id=key_id,
                key_hex=key_hex,
                bitcoin_address="",
                ethereum_address="",
                timestamp=datetime.now(),
                check_type=check_type
            )
            
            # Generate addresses
            btc_addr = self.multichain_checker.private_key_to_bitcoin_address(key_hex)
            eth_addr = self.multichain_checker.private_key_to_ethereum_address(key_hex)
            
            result.bitcoin_address = btc_addr or ""
            result.ethereum_address = eth_addr or ""
            
            # Check Bitcoin balance
            if btc_addr:
                btc_balance = await self.multichain_checker.check_balance_for_network(
                    key_hex, BlockchainNetwork.BITCOIN
                )
                if btc_balance and btc_balance.balance > 0:
                    result.bitcoin_balance = btc_balance.balance
                    self.stats['funded_wallets_found'] += 1
                    logger.info(f"💰 FUNDED BTC WALLET: {btc_addr} = {btc_balance.balance:.8f} BTC")
            
            # Check Ethereum balance  
            if eth_addr:
                eth_balance = await self.multichain_checker.check_balance_for_network(
                    key_hex, BlockchainNetwork.ETHEREUM
                )
                if eth_balance and eth_balance.balance > 0:
                    result.ethereum_balance = eth_balance.balance
                    self.stats['funded_wallets_found'] += 1
                    logger.info(f"💰 FUNDED ETH WALLET: {eth_addr} = {eth_balance.balance:.8f} ETH")
            
            # Check ERC-20 tokens (if enabled and Ethereum has balance or randomly)
            if self.config.alert_on_token_balances and eth_addr:
                if result.ethereum_balance > 0 or (int(key_id[-2:], 16) % 10 == 0):  # Check 10% randomly
                    try:
                        tokens = await self.erc20_checker.check_address_for_tokens(eth_addr)
                        if tokens:
                            result.erc20_tokens = [asdict(token) for token in tokens]
                            self.stats['token_wallets_found'] += 1
                            logger.info(f"🪙 TOKENS FOUND: {eth_addr} has {len(tokens)} token types")
                    except Exception as e:
                        result.errors.append(f"ERC-20 check failed: {e}")
            
            # Check multichain (sample check)
            if self.config.alert_on_multichain_balances and (int(key_id[-2:], 16) % 20 == 0):  # Check 5% randomly
                try:
                    multichain_results = await self.multichain_checker.check_all_networks(key_hex)
                    if multichain_results:
                        result.multichain_balances = [asdict(balance) for balance in multichain_results]
                        self.stats['multichain_wallets_found'] += 1
                        logger.info(f"🌍 MULTICHAIN BALANCES: Found on {len(multichain_results)} networks")
                except Exception as e:
                    result.errors.append(f"Multichain check failed: {e}")
            
            # Update database with check timestamp
            if self.config.save_results_to_db:
                try:
                    with self.db_scanner.db_service.db_manager.get_session() as session:
                        from sqlalchemy import text
                        session.execute(text("""
                            UPDATE private_keys 
                            SET last_tested_at = :timestamp
                            WHERE id = :key_id
                        """), {
                            'timestamp': datetime.now(),
                            'key_id': key_id
                        })
                        session.commit()
                except Exception as e:
                    result.errors.append(f"DB update failed: {e}")
            
            self.stats['total_keys_monitored'] += 1
            self.stats['total_api_calls'] += 3  # Approximate
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking key {key_id}: {e}")
            return None
    
    def _process_results(self, results: List[MonitoringResult]):
        """Process and store monitoring results"""
        if not results:
            return
            
        # Add to recent results
        self.recent_results.extend(results)
        
        # Keep only recent results (last 1000)
        if len(self.recent_results) > 1000:
            self.recent_results = self.recent_results[-1000:]
        
        # Export to JSON if enabled
        if self.config.export_results_to_json:
            try:
                export_data = {
                    'timestamp': datetime.now().isoformat(),
                    'stats': self.stats,
                    'recent_results': [asdict(result) for result in results]
                }
                
                with open(self.config.export_file_path, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
                    
            except Exception as e:
                logger.error(f"Failed to export results: {e}")
        
        # Generate alerts for significant finds
        funded_results = [r for r in results if r.bitcoin_balance > 0 or r.ethereum_balance > 0]
        token_results = [r for r in results if r.erc20_tokens]
        multichain_results = [r for r in results if r.multichain_balances]
        
        if funded_results or token_results or multichain_results:
            self._generate_alert(funded_results, token_results, multichain_results)
    
    def _generate_alert(self, funded_results, token_results, multichain_results):
        """Generate alert for significant findings"""
        alert_msg = []
        alert_msg.append("🚨 WALLET MONITORING ALERT 🚨")
        alert_msg.append("=" * 50)
        
        if funded_results:
            alert_msg.append(f"💰 Found {len(funded_results)} funded wallets:")
            for result in funded_results:
                if result.bitcoin_balance > 0:
                    alert_msg.append(f"  • BTC: {result.bitcoin_address} = {result.bitcoin_balance:.8f} BTC")
                if result.ethereum_balance > 0:
                    alert_msg.append(f"  • ETH: {result.ethereum_address} = {result.ethereum_balance:.8f} ETH")
        
        if token_results:
            alert_msg.append(f"\\n🪙 Found {len(token_results)} wallets with tokens:")
            for result in token_results:
                token_count = len(result.erc20_tokens)
                alert_msg.append(f"  • {result.ethereum_address}: {token_count} token types")
        
        if multichain_results:
            alert_msg.append(f"\\n🌍 Found {len(multichain_results)} multichain wallets:")
            for result in multichain_results:
                network_count = len(result.multichain_balances)
                alert_msg.append(f"  • {result.key_hex[:16]}...: {network_count} networks")
        
        alert_msg.append(f"\\nTimestamp: {datetime.now()}")
        
        alert_text = "\\n".join(alert_msg)
        logger.critical(alert_text)
        
        # Write to alert file
        try:
            with open('/home/admin/wallet_tool/alerts.log', 'a') as f:
                f.write(alert_text + "\\n\\n")
        except Exception as e:
            logger.error(f"Failed to write alert: {e}")
    
    def print_status(self):
        """Print current monitoring status"""
        uptime = datetime.now() - self.stats['uptime_start']
        
        status = []
        status.append("📊 MONITORING STATUS")
        status.append("=" * 50)
        status.append(f"⏱️  Uptime: {uptime}")
        status.append(f"🔑 Keys monitored: {self.stats['total_keys_monitored']}")
        status.append(f"💰 Funded wallets: {self.stats['funded_wallets_found']}")
        status.append(f"🪙 Token wallets: {self.stats['token_wallets_found']}")
        status.append(f"🌍 Multichain wallets: {self.stats['multichain_wallets_found']}")
        status.append(f"📡 API calls made: {self.stats['total_api_calls']}")
        status.append("")
        status.append(f"Last new key check: {self.last_key_check or 'Never'}")
        status.append(f"Last balance recheck: {self.last_balance_check or 'Never'}")
        status.append(f"Recent results: {len(self.recent_results)}")
        
        print("\\n".join(status))
    
    async def run_monitoring_cycle(self):
        """Run one complete monitoring cycle"""
        logger.info("🔄 Starting monitoring cycle...")
        
        try:
            all_results = []
            
            # Check for new keys
            if (not self.last_key_check or 
                (datetime.now() - self.last_key_check).seconds >= self.config.new_keys_check_interval):
                results = await self.check_new_keys()
                all_results.extend(results)
            
            # Periodic balance recheck
            if (not self.last_balance_check or
                (datetime.now() - self.last_balance_check).seconds >= self.config.balance_recheck_interval):
                results = await self.periodic_balance_recheck()
                all_results.extend(results)
            
            # Process all results
            if all_results:
                self._process_results(all_results)
                logger.info(f"✅ Monitoring cycle complete: {len(all_results)} results processed")
            else:
                logger.info("✅ Monitoring cycle complete: No new results")
                
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
    
    async def run(self):
        """Run the continuous monitoring service"""
        logger.info("🚀 Starting Continuous Wallet Monitor...")
        self.running = True
        
        try:
            cycle_count = 0
            while self.running and not self.shutdown_requested:
                cycle_count += 1
                logger.info(f"🔄 Monitoring Cycle #{cycle_count}")
                
                await self.run_monitoring_cycle()
                
                # Print status every 10 cycles
                if cycle_count % 10 == 0:
                    self.print_status()
                
                # Sleep before next cycle
                sleep_time = min(
                    self.config.new_keys_check_interval,
                    self.config.balance_recheck_interval
                ) // 4  # Check 4x more frequently than the shortest interval
                
                logger.info(f"😴 Sleeping for {sleep_time} seconds...")
                await asyncio.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Error in monitoring service: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down Continuous Wallet Monitor...")
        self.running = False
        
        # Final status report
        self.print_status()
        
        # Export final results
        if self.recent_results and self.config.export_results_to_json:
            try:
                final_export = {
                    'shutdown_timestamp': datetime.now().isoformat(),
                    'final_stats': self.stats,
                    'all_results': [asdict(result) for result in self.recent_results]
                }
                
                with open('/home/admin/wallet_tool/final_monitoring_results.json', 'w') as f:
                    json.dump(final_export, f, indent=2, default=str)
                    
                logger.info("📄 Final results exported")
            except Exception as e:
                logger.error(f"Failed to export final results: {e}")
        
        # Cleanup
        self.executor.shutdown(wait=True)
        logger.info("✅ Shutdown complete")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Continuous Wallet Monitoring Service')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--batch-size', type=int, default=50, help='Batch size for processing')
    parser.add_argument('--check-interval', type=int, default=300, help='Check interval in seconds')
    parser.add_argument('--test-cycle', action='store_true', help='Run a single test cycle')
    
    args = parser.parse_args()
    
    # Create configuration
    config = MonitoringConfig()
    if args.batch_size:
        config.batch_size = args.batch_size
    if args.check_interval:
        config.new_keys_check_interval = args.check_interval
    
    # Create and run monitor
    monitor = ContinuousWalletMonitor(config)
    
    async def run_service():
        if args.test_cycle:
            logger.info("🧪 Running test cycle...")
            await monitor.run_monitoring_cycle()
            monitor.print_status()
        else:
            await monitor.run()
    
    try:
        asyncio.run(run_service())
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")

if __name__ == "__main__":
    main()
