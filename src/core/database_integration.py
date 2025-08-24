#!/usr/bin/env python3
"""
Wallet Tool Database Integration
===============================
Production-ready integration of existing wallet scanner with database
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import DatabaseManager
from database.service import WalletDatabaseService
from database.models import ScanStatus, KeyStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/home/admin/wallet_tool/logs/database_integration.log')
    ]
)
logger = logging.getLogger(__name__)

class DatabaseIntegratedScanner:
    """
    Enhanced scanner that integrates existing functionality with database storage
    """
    
    def __init__(self, db_service: Optional[WalletDatabaseService] = None):
        if db_service is None:
            # Create default database service
            db_manager = DatabaseManager()
            self.db_service = WalletDatabaseService(db_manager)
        else:
            self.db_service = db_service
        self.current_scan_id = None
        
    def start_scan_session(self, 
                          scan_type: str,
                          source_path: str,
                          scan_params: Optional[Dict] = None) -> str:
        """
        Initialize a new scan session in the database
        
        Returns:
            scan_session_id: UUID for tracking this scan
        """
        try:
            with self.db_service.get_repositories() as repos:
                # Generate session name from timestamp and scan type
                session_name = f"{scan_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Create session with required parameters
                import json
                scan_session = repos['scan_sessions'].create(
                    name=session_name,
                    source_path=source_path,
                    metadata_json=json.dumps({
                        'scan_type': scan_type,
                        'parameters': scan_params or {}
                    }),
                    status=ScanStatus.PENDING
                )
                self.current_scan_id = str(scan_session.id)
                
                logger.info(f"Started scan session {self.current_scan_id} ({session_name}) for {source_path}")
                return self.current_scan_id
                
        except Exception as e:
            logger.error(f"Failed to start scan session: {e}")
            raise

    def update_scan_progress(self, 
                           files_scanned: int,
                           keys_found: int,
                           errors_count: int = 0):
        """Update scan progress in database"""
        
        if not self.current_scan_id:
            logger.warning("No active scan session to update")
            return
            
        try:
            with self.db_service.get_repositories() as repos:
                repos['scan_sessions'].update_progress(
                    session_id=self.current_scan_id,
                    files_processed=files_scanned,
                    keys_discovered=keys_found,
                    errors_encountered=errors_count
                )
                
        except Exception as e:
            logger.error(f"Failed to update scan progress: {e}")

    def store_discovered_keys(self, keys_data: List[Dict]) -> int:
        """
        Store discovered keys in database
        
        Args:
            keys_data: List of key dictionaries with format:
                {
                    'private_key': 'hex_string',
                    'key_type': 'hex|wif|mnemonic',
                    'source_file': 'file_path',
                    'discovery_method': 'method_name'
                }
        
        Returns:
            Number of keys successfully stored
        """
        if not self.current_scan_id:
            logger.error("No active scan session")
            return 0
        
        stored_count = 0
        
        try:
            with self.db_service.get_repositories() as repos:
                for key_data in keys_data:
                    try:
                        # Add scan session reference
                        key_data['scan_session_id'] = self.current_scan_id
                        key_data['status'] = KeyStatus.DISCOVERED
                        
                        repos['private_keys'].create(**key_data)
                        stored_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to store key {key_data.get('private_key', 'unknown')}: {e}")
                        
            logger.info(f"Stored {stored_count}/{len(keys_data)} discovered keys")
            return stored_count
            
        except Exception as e:
            logger.error(f"Failed to store discovered keys: {e}")
            return 0
    
    def add_private_key(self, 
                       session_id: str, 
                       private_key: str,
                       source_file: str = "unknown",
                       discovery_pattern: str = "manual") -> bool:
        """Add a single private key to the database"""
        
        try:
            if not private_key or not isinstance(private_key, str):
                return False
                
            key_data = [{
                'key_hex': private_key if len(private_key) == 64 else '',
                'key_wif': private_key if len(private_key) < 64 else '',
                'source_file': source_file,
                'discovery_pattern': discovery_pattern
                # Note: scan_session_id will be added by store_discovered_keys
            }]
            
            # Temporarily store the original session ID
            original_session = self.current_scan_id
            self.current_scan_id = session_id
            
            result = self.store_discovered_keys(key_data) > 0
            
            # Restore original session ID
            self.current_scan_id = original_session
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to add private key: {e}")
            return False
    
    def validate_private_key(self, private_key: str) -> bool:
        """Validate a private key format"""
        
        try:
            if not private_key or not isinstance(private_key, str):
                return False
                
            # Basic validation for hex keys (64 chars)
            if len(private_key) == 64:
                int(private_key, 16)  # Test if valid hex
                return True
                
            # Basic validation for WIF keys (51-52 chars starting with 5, K, or L)
            if 51 <= len(private_key) <= 52 and private_key[0] in '5KL':
                return True
                
            return False
            
        except (ValueError, TypeError):
            return False
    
    def generate_bitcoin_address(self, private_key: str) -> Optional[str]:
        """Generate Bitcoin address from private key (simplified version)"""
        
        try:
            if not self.validate_private_key(private_key):
                return None
                
            # This is a simplified mock - in production you'd use proper crypto libraries
            # For beta testing, we'll generate a placeholder address
            import hashlib
            hash_obj = hashlib.sha256(private_key.encode())
            hash_hex = hash_obj.hexdigest()
            
            # Generate a mock Bitcoin address format
            return f"1{hash_hex[:25]}MockAddr"
            
        except Exception as e:
            logger.error(f"Failed to generate address: {e}")
            return None
    
    def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a specific session"""
        
        try:
            with self.db_service.get_repositories() as repos:
                session = repos['scan_sessions'].get_by_id(session_id)
                if not session:
                    return {}
                
                return {
                    'session_id': session_id,
                    'status': session.status.value if session.status else 'unknown',
                    'keys_discovered': getattr(session, 'keys_discovered', 0),
                    'total_files_scanned': getattr(session, 'total_files_scanned', 0),
                    'started_at': getattr(session, 'started_at', None),
                    'completed_at': getattr(session, 'completed_at', None)
                }
                
        except Exception as e:
            logger.error(f"Failed to get session statistics: {e}")
            return {}

    def store_test_results(self, test_results: List[Dict]) -> int:
        """
        Store key test results in database
        
        Args:
            test_results: List of test result dictionaries with format:
                {
                    'private_key': 'hex_string',
                    'test_message': 'BIE1_message',
                    'success': True/False,
                    'decrypted_content': 'content' or None,
                    'error_message': 'error' or None,
                    'test_duration_ms': float
                }
        
        Returns:
            Number of results successfully stored
        """
        if not self.current_scan_id:
            logger.error("No active scan session")
            return 0
        
        stored_count = 0
        
        try:
            with self.db_service.get_repositories() as repos:
                for result in test_results:
                    try:
                        # Add scan session reference
                        result['scan_session_id'] = self.current_scan_id
                        
                        repos['test_results'].create_test_result(**result)
                        stored_count += 1
                        
                        # Update key status if successful
                        if result.get('success'):
                            repos['private_keys'].update_key_status(
                                private_key=result['private_key'],
                                status=KeyStatus.SUCCESS
                            )
                        
                    except Exception as e:
                        logger.error(f"Failed to store test result for {result.get('private_key', 'unknown')}: {e}")
                        
            logger.info(f"Stored {stored_count}/{len(test_results)} test results")
            return stored_count
            
        except Exception as e:
            logger.error(f"Failed to store test results: {e}")
            return 0

    def complete_scan_session(self, 
                            success: bool = False,
                            working_key: Optional[str] = None,
                            error_message: Optional[str] = None):
        """Complete the current scan session"""
        
        if not self.current_scan_id:
            logger.warning("No active scan session to complete")
            return
        
        try:
            with self.db_service.get_repositories() as repos:
                status = ScanStatus.COMPLETED if success else ScanStatus.FAILED
                
                completion_data = {
                    'status': status,
                    'completed_at': datetime.utcnow(),
                    'error_message': error_message
                }
                
                repos['scan_sessions'].update(
                    session_id=self.current_scan_id,
                    **completion_data
                )
                
                logger.info(f"Completed scan session {self.current_scan_id} with status: {status.value}")
                
        except Exception as e:
            logger.error(f"Failed to complete scan session: {e}")
        finally:
            self.current_scan_id = None

    def get_scan_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive scan statistics"""
        
        try:
            with self.db_service.get_repositories() as repos:
                stats = repos['scan_sessions'].get_scan_statistics(days=days)
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get scan statistics: {e}")
            return {}

    def check_balances_for_all_keys(self, batch_size: int = 20, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Check balances for all discovered keys in the database using Ultimate Balance Checker
        """
        try:
            # Import the ultimate balance checker
            sys.path.append('/home/admin/wallet_tool')
            from ultimate_balance_checker import UltimateBalanceChecker
            
            # Initialize the ultimate balance checker
            balance_checker = UltimateBalanceChecker(db_service=self.db_service)
            
            # Get all discovered keys from database using proper repository pattern
            with self.db_service.get_repositories() as repos:
                
                # Get keys using the repository
                keys_repo = repos['private_keys']
                
                # Query keys directly through the repository's session
                from database.models import PrivateKey, KeyStatus
                
                # Use the repository session to query
                if hasattr(keys_repo, 'session'):
                    session = keys_repo.session
                else:
                    # Fallback to getting session from service
                    from database.connection import Session
                    session = Session()
                
                try:
                    query = session.query(PrivateKey).filter(
                        PrivateKey.status == KeyStatus.DISCOVERED
                    )
                    
                    if limit:
                        query = query.limit(limit)
                    
                    keys = query.all()
                    
                    total_keys = len(keys)
                    print(f"Starting balance checks for {total_keys} keys using Ultimate Balance Checker...")
                    
                    # Extract private keys for batch processing
                    private_keys = []
                    for key in keys:
                        if key.key_hex and len(key.key_hex) == 64:
                            private_keys.append(key.key_hex)
                    
                    print(f"Valid private keys for checking: {len(private_keys)}")
                    
                    # Use Ultimate Balance Checker for batch processing
                    results = balance_checker.batch_check_private_keys(
                        private_keys, 
                        max_workers=min(8, len(private_keys))
                    )
                    
                    # Process results and update database
                    funded_results = []
                    for result in results:
                        if result.has_balance:
                            print(f"🎉 FUNDED WALLET FOUND!")
                            print(f"   Chain: {result.chain.upper()}")
                            print(f"   Address: {result.address}")
                            print(f"   Balance: {result.balance_native:.8f}")
                            print(f"   Private Key: {result.private_key}")
                            
                            if result.token_balances:
                                print(f"   Token Balances:")
                                for token, balance in result.token_balances.items():
                                    print(f"     💎 {token}: {balance:.6f}")
                            
                            funded_results.append({
                                'private_key': result.private_key,
                                'chain': result.chain,
                                'address': result.address,
                                'balance_native': result.balance_native,
                                'balance_wei': result.balance_wei,
                                'token_balances': result.token_balances,
                                'api_used': result.api_used,
                                'transaction_count': result.transaction_count,
                                'timestamp': result.timestamp
                            })
                            
                            # Update key status to funded
                            for key in keys:
                                if key.key_hex == result.private_key:
                                    key.status = KeyStatus.SUCCESS
                                    break
                    
                    # Commit database updates
                    session.commit()
                    
                    # Generate comprehensive statistics
                    stats = balance_checker.get_statistics(results)
                    
                    # Save results using Ultimate Balance Checker
                    results_file = balance_checker.save_results(results)
                    
                    # Create summary for return
                    result_summary = {
                        'total_keys_checked': len(private_keys),
                        'total_results': len(results),
                        'funded_keys_found': len(funded_results),
                        'funded_keys': funded_results,
                        'statistics': stats,
                        'results_file': results_file,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    print(f"\n✅ Ultimate Balance Check completed!")
                    print(f"   Total keys checked: {len(private_keys)}")
                    print(f"   Total addresses checked: {len(results)}")
                    print(f"   Funded wallets found: {len(funded_results)}")
                    print(f"   Success rate: {stats.get('funding_rate', 0):.2f}%")
                    print(f"   API calls made: {stats.get('total_api_calls', 0)}")
                    print(f"   Results saved to: {results_file}")
                    
                    return result_summary
                    
                except Exception as e:
                    session.rollback()
                    raise
                finally:
                    if 'session' in locals():
                        session.close()
                    
        except Exception as e:
            logger.error(f"Failed to check balances: {e}")
            return {'error': str(e)}

class EnhancedMegaDatasetScanner(DatabaseIntegratedScanner):
    """
    Enhanced version of mega_dataset_scanner.py with database integration
    """
    
    def run_mega_scan(self, 
                     dataset_path: str,
                     max_directories: int = 50,
                     parallel_workers: int = 8) -> Dict[str, Any]:
        """
        Run mega dataset scan with database integration
        """
        
        # Start scan session
        scan_params = {
            'max_directories': max_directories,
            'parallel_workers': parallel_workers,
            'scan_method': 'mega_dataset'
        }
        
        scan_id = self.start_scan_session(
            scan_type='mega_dataset',
            source_path=dataset_path,
            scan_params=scan_params
        )
        
        try:
            # Update scan status to running
            with self.db_service.get_repositories() as repos:
                repos['scan_sessions'].update(scan_id, status=ScanStatus.RUNNING)
            
            # Import and run existing mega scanner logic
            from mega_dataset_scanner import MegaDatasetScanner
            
            scanner = MegaDatasetScanner()
            results = scanner.scan_net607_dataset()
            
            # Store discovered keys
            keys_data = []
            for key_info in results:
                keys_data.append({
                    'private_key': key_info['key'],
                    'key_type': key_info['type'],
                    'source_file': key_info.get('file', ''),
                    'discovery_method': 'mega_dataset_scan'
                })
            
            stored_keys = self.store_discovered_keys(keys_data)
            
            # Complete scan session
            self.complete_scan_session(
                success=True,
                working_key=None  # Set working key if found
            )
            
            return {
                'scan_id': scan_id,
                'keys_found': len(keys_data),
                'keys_stored': stored_keys,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Mega scan failed: {e}")
            self.complete_scan_session(
                success=False,
                error_message=str(e)
            )
            raise

def main():
    """Main integration function"""
    
    print("🚀 WALLET TOOL DATABASE INTEGRATION")
    print("=" * 50)
    
    # Initialize database connection
    try:
        # Create logs directory if it doesn't exist
        os.makedirs('/home/admin/wallet_tool/logs', exist_ok=True)
        
        db_manager = DatabaseManager()
        db_service = WalletDatabaseService(db_manager)
        
        # Test database connection
        if not db_manager.test_connection():
            print("❌ Database connection failed")
            return
        
        print("✅ Database connection successful")
        
        # Initialize enhanced scanner
        scanner = EnhancedMegaDatasetScanner(db_service)
        
        # Get recent statistics
        stats = scanner.get_scan_statistics(days=7)
        print(f"📊 Recent scan statistics (7 days):")
        print(f"   Scans completed: {stats.get('total_scans', 0)}")
        print(f"   Keys discovered: {stats.get('total_keys', 0)}")
        print(f"   Success rate: {stats.get('success_rate', 0):.1f}%")
        
        # Example: Run a small test scan
        test_scan_id = scanner.start_scan_session(
            scan_type='test',
            source_path='/home/admin/wallet_tool/test_data',
            scan_params={'test': True}
        )
        
        # Simulate some progress
        scanner.update_scan_progress(files_scanned=10, keys_found=5)
        
        # Complete test scan
        scanner.complete_scan_session(success=True)
        
        print(f"✅ Test scan completed: {test_scan_id}")
        
    except Exception as e:
        logger.error(f"Integration failed: {e}")
        print(f"❌ Integration failed: {e}")

if __name__ == "__main__":
    main()
