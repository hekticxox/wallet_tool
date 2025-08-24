"""
Wallet Tool Database Service Integration
======================================
High-level service layer that integrates existing wallet scanner
functionality with the database layer.
"""

import logging
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

from .connection import DatabaseManager
from .models import KeyStatus, ScanStatus, PrivateKey, ScanSession, KeyTestResult, BalanceCheck
from .repositories import (
    ScanSessionRepository, PrivateKeyRepository, 
    KeyTestResultRepository, BalanceCheckRepository
)

logger = logging.getLogger(__name__)

class WalletDatabaseService:
    """
    Main service class integrating wallet tool operations with database
    Provides transaction management, error handling, and business logic
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._session_cache = {}
    
    @contextmanager
    def get_repositories(self):
        """Context manager providing all repositories with shared session"""
        with self.db_manager.get_session() as session:
            try:
                repositories = {
                    'scan_sessions': ScanSessionRepository(session),
                    'private_keys': PrivateKeyRepository(session),
                    'test_results': KeyTestResultRepository(session),
                    'balance_checks': BalanceCheckRepository(session)
                }
                yield repositories
            except Exception as e:
                logger.error(f"Database operation failed: {e}")
                raise
    
    def start_scan_session(self, name: str, source_path: str, 
                          metadata: Optional[Dict] = None) -> UUID:
        """
        Start a new wallet scanning session
        
        Args:
            name: Human-readable session name
            source_path: Path being scanned
            metadata: Additional session metadata
            
        Returns:
            UUID of created session
        """
        with self.get_repositories() as repos:
            session = repos['scan_sessions'].create(
                name=name,
                source_path=source_path,
                status=ScanStatus.PENDING,
                metadata_json=str(metadata) if metadata else None
            )
            
            logger.info(f"Started scan session: {name} [{session.id}]")
            return session.id
    
    def update_scan_progress(self, session_id: UUID, 
                           files_scanned: int = 0,
                           keys_discovered: int = 0,
                           status: Optional[ScanStatus] = None) -> bool:
        """Update scan session progress"""
        
        update_data = {}
        
        if files_scanned > 0:
            update_data['total_files_scanned'] = files_scanned
        
        if keys_discovered > 0:
            update_data['keys_discovered'] = keys_discovered
        
        if status:
            update_data['status'] = status
            if status == ScanStatus.RUNNING and 'started_at' not in update_data:
                update_data['started_at'] = datetime.utcnow()
            elif status == ScanStatus.COMPLETED:
                update_data['completed_at'] = datetime.utcnow()
        
        with self.get_repositories() as repos:
            success = repos['scan_sessions'].update(session_id, **update_data)
            
        if success:
            logger.debug(f"Updated scan session {session_id}: {update_data}")
        
        return success
    
    def store_discovered_keys(self, session_id: UUID, 
                            key_data_list: List[Dict]) -> List[UUID]:
        """
        Store multiple discovered private keys efficiently
        
        Args:
            session_id: Associated scan session
            key_data_list: List of key dictionaries with required fields
            
        Returns:
            List of created key UUIDs
        """
        
        # Validate and enrich key data
        enriched_keys = []
        for key_data in key_data_list:
            if not self._validate_key_data(key_data):
                logger.warning(f"Skipping invalid key data: {key_data}")
                continue
            
            enriched_key = {
                'scan_session_id': session_id,
                'status': KeyStatus.DISCOVERED,
                'is_valid': False,  # Will be validated later
                **key_data
            }
            enriched_keys.append(enriched_key)
        
        if not enriched_keys:
            logger.warning("No valid keys to store")
            return []
        
        with self.get_repositories() as repos:
            # Check for duplicates
            existing_keys = set()
            for key_data in enriched_keys:
                existing = repos['private_keys'].find_by_hex(key_data['key_hex'])
                if existing:
                    existing_keys.add(key_data['key_hex'])
            
            # Filter out duplicates
            new_keys = [k for k in enriched_keys if k['key_hex'] not in existing_keys]
            
            if not new_keys:
                logger.info("All keys already exist in database")
                return []
            
            # Bulk create
            created_keys = repos['private_keys'].bulk_create(new_keys)
            key_ids = [key.id for key in created_keys]
            
            # Update session statistics
            self.update_scan_progress(
                session_id, 
                keys_discovered=len(created_keys)
            )
            
            logger.info(f"Stored {len(created_keys)} new keys for session {session_id}")
            return key_ids
    
    def validate_private_keys(self, session_id: Optional[UUID] = None, 
                            limit: int = 100) -> Tuple[int, int]:
        """
        Validate private keys cryptographically
        
        Args:
            session_id: Optional session filter
            limit: Maximum keys to process
            
        Returns:
            Tuple of (validated_count, valid_count)
        """
        
        with self.get_repositories() as repos:
            # Get unvalidated keys
            if session_id:
                keys = repos['private_keys'].get_keys_by_session(
                    session_id, KeyStatus.DISCOVERED
                )[:limit]
            else:
                # Get from any session with DISCOVERED status
                keys = (
                    repos['private_keys'].session
                    .query(repos['private_keys'].session.query(PrivateKey))
                    .filter(PrivateKey.status == KeyStatus.DISCOVERED)
                    .limit(limit)
                    .all()
                )
            
            validated_count = 0
            valid_count = 0
            
            for key in keys:
                is_valid = self._validate_private_key_crypto(key.key_hex)
                
                # Update key status
                repos['private_keys'].update(
                    key.id,
                    is_valid=is_valid,
                    status=KeyStatus.VALIDATED if is_valid else KeyStatus.FAILED
                )
                
                validated_count += 1
                if is_valid:
                    valid_count += 1
            
            logger.info(f"Validated {validated_count} keys, {valid_count} valid")
            return validated_count, valid_count
    
    def run_key_tests(self, session_id: UUID, test_messages: List[str],
                     max_keys: int = 100) -> Dict[str, Any]:
        """
        Test private keys against BIE1 messages
        
        Args:
            session_id: Session to test keys from
            test_messages: List of BIE1 messages to test
            max_keys: Maximum keys to test
            
        Returns:
            Dictionary with test results summary
        """
        
        with self.get_repositories() as repos:
            # Get untested valid keys
            keys = repos['private_keys'].get_untested_keys(limit=max_keys)
            
            if not keys:
                logger.info("No untested keys available")
                return {'tested': 0, 'successful': 0, 'results': []}
            
            tested_count = 0
            successful_count = 0
            results = []
            
            for key in keys:
                for message in test_messages:
                    start_time = time.time()
                    
                    # Perform actual test (integrate with existing logic)
                    success, decrypted_content, error = self._test_key_against_message(
                        key.key_hex, message
                    )
                    
                    execution_time = int((time.time() - start_time) * 1000)
                    
                    # Store test result
                    test_result = repos['test_results'].create(
                        private_key_id=key.id,
                        scan_session_id=session_id,
                        test_type='bie1_decrypt',
                        success=success,
                        test_message=message,
                        decrypted_content=decrypted_content if success else None,
                        error_message=error if not success else None,
                        execution_time_ms=execution_time
                    )
                    
                    tested_count += 1
                    if success:
                        successful_count += 1
                        results.append({
                            'key_id': str(key.id),
                            'key_hex': key.key_hex,
                            'decrypted_content': decrypted_content,
                            'test_result_id': str(test_result.id)
                        })
                
                # Update key status
                repos['private_keys'].update(
                    key.id,
                    status=KeyStatus.SUCCESS if any(r['key_id'] == str(key.id) for r in results) else KeyStatus.TESTED,
                    last_tested_at=datetime.utcnow()
                )
            
            logger.info(f"Tested {tested_count} key-message combinations, {successful_count} successful")
            
            return {
                'tested': tested_count,
                'successful': successful_count,
                'results': results,
                'session_id': str(session_id)
            }
    
    def check_balances(self, session_id: UUID, api_source: str = 'blockchain_info') -> Dict[str, Any]:
        """
        Check Bitcoin balances for successful keys
        
        Args:
            session_id: Session to check balances for
            api_source: API service to use for balance checks
            
        Returns:
            Dictionary with balance check results
        """
        
        with self.get_repositories() as repos:
            # Get successful keys that need balance checks
            successful_keys = (
                repos['private_keys']
                .get_keys_by_session(session_id, KeyStatus.SUCCESS)
            )
            
            if not successful_keys:
                logger.info("No successful keys to check balances for")
                return {'checked': 0, 'positive_balances': 0, 'results': []}
            
            checked_count = 0
            positive_count = 0
            results = []
            
            for key in successful_keys:
                if not key.bitcoin_address:
                    # Generate address if not present
                    address = self._generate_bitcoin_address(key.key_hex)
                    repos['private_keys'].update(key.id, bitcoin_address=address)
                    key.bitcoin_address = address
                
                # Check balance
                start_time = time.time()
                balance_btc, tx_count, error = self._check_address_balance(
                    key.bitcoin_address, api_source
                )
                response_time = int((time.time() - start_time) * 1000)
                
                if error:
                    logger.warning(f"Balance check failed for {key.bitcoin_address}: {error}")
                    continue
                
                # Store balance check
                balance_check = repos['balance_checks'].create(
                    private_key_id=key.id,
                    bitcoin_address=key.bitcoin_address,
                    balance_btc=balance_btc,
                    transaction_count=tx_count,
                    api_source=api_source,
                    response_time_ms=response_time
                )
                
                checked_count += 1
                if balance_btc > 0:
                    positive_count += 1
                    results.append({
                        'key_id': str(key.id),
                        'address': key.bitcoin_address,
                        'balance_btc': balance_btc,
                        'balance_check_id': str(balance_check.id)
                    })
            
            logger.info(f"Checked {checked_count} balances, {positive_count} with positive balance")
            
            return {
                'checked': checked_count,
                'positive_balances': positive_count,
                'results': results,
                'session_id': str(session_id)
            }
    
    def get_session_dashboard(self, session_id: UUID) -> Dict[str, Any]:
        """Get comprehensive dashboard data for a session"""
        
        with self.get_repositories() as repos:
            session_stats = repos['scan_sessions'].get_session_stats(session_id)
            test_stats = repos['test_results'].get_session_results_summary(session_id)
            
            # Get positive balance results
            positive_balances = repos['balance_checks'].get_positive_balances()
            session_balances = [
                b for b in positive_balances 
                if str(b.private_key.scan_session_id) == str(session_id)
            ]
            
            return {
                'session': session_stats,
                'testing': test_stats,
                'balances': {
                    'positive_count': len(session_balances),
                    'total_btc': sum(b.balance_btc for b in session_balances),
                    'addresses': [
                        {
                            'address': b.bitcoin_address,
                            'balance_btc': b.balance_btc,
                            'key_hex': b.private_key.key_hex[:16] + '...'
                        }
                        for b in session_balances
                    ]
                }
            }
    
    # Private helper methods
    
    def _validate_key_data(self, key_data: Dict) -> bool:
        """Validate required fields in key data"""
        required_fields = ['key_hex', 'source_file', 'discovery_pattern']
        return all(field in key_data for field in required_fields)
    
    def _validate_private_key_crypto(self, key_hex: str) -> bool:
        """Perform cryptographic validation of private key"""
        try:
            # Basic hex validation
            if len(key_hex) != 64:
                return False
            
            int(key_hex, 16)
            
            # Additional crypto validation would go here
            # (e.g., check if key is in valid range for secp256k1)
            
            return True
        except ValueError:
            return False
    
    def _test_key_against_message(self, key_hex: str, message: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Test private key against BIE1 message
        This integrates with existing electrum decrypt logic
        """
        try:
            # This would integrate with your existing logic
            # from robust_key_tester.py or lightning_key_tester.py
            
            # Placeholder implementation
            # In production, this would call electrum decrypt
            return False, None, "Integration pending"
            
        except Exception as e:
            return False, None, str(e)
    
    def _generate_bitcoin_address(self, key_hex: str) -> str:
        """Generate Bitcoin address from private key"""
        try:
            # This would integrate with your existing key-to-address logic
            # Placeholder implementation
            return f"1BitcoinAddress{key_hex[:8]}"  # Placeholder
            
        except Exception as e:
            logger.error(f"Address generation failed: {e}")
            return ""
    
    def _check_address_balance(self, address: str, api_source: str) -> Tuple[float, int, Optional[str]]:
        """
        Check Bitcoin address balance using API
        This integrates with existing balance checker logic
        """
        try:
            # This would integrate with your existing balance checking logic
            # from balance_checker_with_apis.py or enhanced_api_balance_checker.py
            
            # Placeholder implementation
            return 0.0, 0, None
            
        except Exception as e:
            return 0.0, 0, str(e)
