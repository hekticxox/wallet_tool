"""
Repository Pattern Implementation
===============================
Clean data access layer with business logic separation,
caching, and optimized queries for wallet operations.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload

from .models import (
    PrivateKey, ScanSession, KeyTestResult, BalanceCheck,
    KeyStatus, ScanStatus
)

class BaseRepository(ABC):
    """Abstract base repository with common operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    @abstractmethod
    def get_by_id(self, id: UUID):
        pass
    
    @abstractmethod
    def create(self, **kwargs):
        pass
    
    @abstractmethod
    def update(self, id: UUID, **kwargs):
        pass
    
    @abstractmethod
    def delete(self, id: UUID):
        pass

class ScanSessionRepository(BaseRepository):
    """Repository for scan session operations"""
    
    def get_by_id(self, session_id: UUID) -> Optional[ScanSession]:
        """Get scan session by ID with relationships"""
        return (
            self.session.query(ScanSession)
            .options(
                selectinload(ScanSession.private_keys),
                selectinload(ScanSession.test_results)
            )
            .filter(ScanSession.id == session_id)
            .first()
        )
    
    def create(self, name: str, source_path: str, **kwargs) -> ScanSession:
        """Create new scan session"""
        session = ScanSession(
            name=name,
            source_path=source_path,
            **kwargs
        )
        self.session.add(session)
        self.session.flush()  # Get ID without committing
        return session
    
    def update(self, session_id: UUID, **kwargs) -> bool:
        """Update scan session"""
        result = (
            self.session.query(ScanSession)
            .filter(ScanSession.id == session_id)
            .update(kwargs)
        )
        return result > 0
    
    def delete(self, session_id: UUID) -> bool:
        """Delete scan session and related data"""
        result = (
            self.session.query(ScanSession)
            .filter(ScanSession.id == session_id)
            .delete()
        )
        return result > 0
    
    def get_active_sessions(self) -> List[ScanSession]:
        """Get all active/running scan sessions"""
        return (
            self.session.query(ScanSession)
            .filter(ScanSession.status.in_([ScanStatus.PENDING, ScanStatus.RUNNING]))
            .order_by(desc(ScanSession.created_at))
            .all()
        )
    
    def get_recent_sessions(self, limit: int = 10) -> List[ScanSession]:
        """Get recently created sessions"""
        return (
            self.session.query(ScanSession)
            .order_by(desc(ScanSession.created_at))
            .limit(limit)
            .all()
        )
    
    def get_session_stats(self, session_id: UUID) -> Dict[str, Any]:
        """Get comprehensive session statistics"""
        session = self.get_by_id(session_id)
        if not session:
            return {}
        
        # Query statistics in one go
        stats = (
            self.session.query(
                func.count(PrivateKey.id).label('total_keys'),
                func.count(func.nullif(PrivateKey.is_valid, False)).label('valid_keys'),
                func.count(KeyTestResult.id).label('tests_run'),
                func.count(func.nullif(KeyTestResult.success, False)).label('successful_tests')
            )
            .outerjoin(PrivateKey, PrivateKey.scan_session_id == session.id)
            .outerjoin(KeyTestResult, KeyTestResult.scan_session_id == session.id)
            .first()
        )
        
        return {
            'session_id': str(session.id),
            'name': session.name,
            'status': session.status.value,
            'total_keys': stats.total_keys or 0,
            'valid_keys': stats.valid_keys or 0,
            'tests_run': stats.tests_run or 0,
            'successful_tests': stats.successful_tests or 0,
            'duration_seconds': self._calculate_duration(session),
            'files_scanned': session.total_files_scanned,
            'keys_per_file': self._safe_divide(stats.total_keys, session.total_files_scanned)
        }
    
    def _calculate_duration(self, session: ScanSession) -> Optional[int]:
        """Calculate session duration in seconds"""
        if not session.started_at:
            return None
        
        end_time = session.completed_at or datetime.utcnow()
        return int((end_time - session.started_at).total_seconds())
    
    def _safe_divide(self, numerator: int, denominator: int) -> float:
        """Safe division with zero check"""
        return numerator / denominator if denominator > 0 else 0.0

class PrivateKeyRepository(BaseRepository):
    """Repository for private key operations with optimized queries"""
    
    def get_by_id(self, key_id: UUID) -> Optional[PrivateKey]:
        """Get private key by ID"""
        return (
            self.session.query(PrivateKey)
            .filter(PrivateKey.id == key_id)
            .first()
        )
    
    def create(self, key_hex: str, scan_session_id: UUID, **kwargs) -> PrivateKey:
        """Create new private key record"""
        key = PrivateKey(
            key_hex=key_hex,
            scan_session_id=scan_session_id,
            **kwargs
        )
        self.session.add(key)
        self.session.flush()
        return key
    
    def update(self, key_id: UUID, **kwargs) -> bool:
        """Update private key"""
        result = (
            self.session.query(PrivateKey)
            .filter(PrivateKey.id == key_id)
            .update(kwargs)
        )
        return result > 0
    
    def delete(self, key_id: UUID) -> bool:
        """Delete private key"""
        result = (
            self.session.query(PrivateKey)
            .filter(PrivateKey.id == key_id)
            .delete()
        )
        return result > 0
    
    def find_by_hex(self, key_hex: str) -> Optional[PrivateKey]:
        """Find private key by hex value"""
        return (
            self.session.query(PrivateKey)
            .filter(PrivateKey.key_hex == key_hex)
            .first()
        )
    
    def bulk_create(self, key_data_list: List[Dict[str, Any]]) -> List[PrivateKey]:
        """Efficiently create multiple private keys"""
        keys = []
        for key_data in key_data_list:
            key = PrivateKey(**key_data)
            keys.append(key)
        
        self.session.add_all(keys)
        self.session.flush()
        return keys
    
    def get_untested_keys(self, limit: int = 100) -> List[PrivateKey]:
        """Get private keys that haven't been tested yet"""
        return (
            self.session.query(PrivateKey)
            .filter(
                and_(
                    PrivateKey.is_valid == True,
                    PrivateKey.status == KeyStatus.VALIDATED,
                    PrivateKey.last_tested_at.is_(None)
                )
            )
            .limit(limit)
            .all()
        )
    
    def get_keys_by_session(self, session_id: UUID, status: Optional[KeyStatus] = None) -> List[PrivateKey]:
        """Get all keys for a specific session, optionally filtered by status"""
        query = (
            self.session.query(PrivateKey)
            .filter(PrivateKey.scan_session_id == session_id)
        )
        
        if status:
            query = query.filter(PrivateKey.status == status)
        
        return query.order_by(PrivateKey.created_at).all()
    
    def get_successful_keys(self) -> List[PrivateKey]:
        """Get all keys that have successful test results"""
        return (
            self.session.query(PrivateKey)
            .join(KeyTestResult)
            .filter(KeyTestResult.success == True)
            .distinct()
            .all()
        )
    
    def update_key_status_batch(self, key_ids: List[UUID], status: KeyStatus) -> int:
        """Update status for multiple keys efficiently"""
        result = (
            self.session.query(PrivateKey)
            .filter(PrivateKey.id.in_(key_ids))
            .update({PrivateKey.status: status}, synchronize_session=False)
        )
        return result

class KeyTestResultRepository(BaseRepository):
    """Repository for key test result operations"""
    
    def get_by_id(self, result_id: UUID) -> Optional[KeyTestResult]:
        """Get test result by ID"""
        return (
            self.session.query(KeyTestResult)
            .filter(KeyTestResult.id == result_id)
            .first()
        )
    
    def create(self, private_key_id: UUID, scan_session_id: UUID, **kwargs) -> KeyTestResult:
        """Create new test result"""
        result = KeyTestResult(
            private_key_id=private_key_id,
            scan_session_id=scan_session_id,
            **kwargs
        )
        self.session.add(result)
        self.session.flush()
        return result
    
    def update(self, result_id: UUID, **kwargs) -> bool:
        """Update test result"""
        result = (
            self.session.query(KeyTestResult)
            .filter(KeyTestResult.id == result_id)
            .update(kwargs)
        )
        return result > 0
    
    def delete(self, result_id: UUID) -> bool:
        """Delete test result"""
        result = (
            self.session.query(KeyTestResult)
            .filter(KeyTestResult.id == result_id)
            .delete()
        )
        return result > 0
    
    def get_successful_results(self, limit: int = 100) -> List[KeyTestResult]:
        """Get successful test results with key details"""
        return (
            self.session.query(KeyTestResult)
            .options(selectinload(KeyTestResult.private_key))
            .filter(KeyTestResult.success == True)
            .order_by(desc(KeyTestResult.created_at))
            .limit(limit)
            .all()
        )
    
    def get_results_by_key(self, private_key_id: UUID) -> List[KeyTestResult]:
        """Get all test results for a specific key"""
        return (
            self.session.query(KeyTestResult)
            .filter(KeyTestResult.private_key_id == private_key_id)
            .order_by(KeyTestResult.created_at)
            .all()
        )
    
    def get_session_results_summary(self, session_id: UUID) -> Dict[str, Any]:
        """Get test results summary for a session"""
        results = (
            self.session.query(
                func.count(KeyTestResult.id).label('total_tests'),
                func.count(func.nullif(KeyTestResult.success, False)).label('successful_tests'),
                func.avg(KeyTestResult.execution_time_ms).label('avg_execution_time')
            )
            .filter(KeyTestResult.scan_session_id == session_id)
            .first()
        )
        
        return {
            'session_id': str(session_id),
            'total_tests': results.total_tests or 0,
            'successful_tests': results.successful_tests or 0,
            'success_rate': self._calculate_success_rate(results.successful_tests, results.total_tests),
            'average_execution_time_ms': float(results.avg_execution_time or 0)
        }
    
    def _calculate_success_rate(self, successful: int, total: int) -> float:
        """Calculate success rate as percentage"""
        return (successful / total * 100) if total > 0 else 0.0

class BalanceCheckRepository(BaseRepository):
    """Repository for balance check operations"""
    
    def get_by_id(self, check_id: UUID) -> Optional[BalanceCheck]:
        """Get balance check by ID"""
        return (
            self.session.query(BalanceCheck)
            .filter(BalanceCheck.id == check_id)
            .first()
        )
    
    def create(self, private_key_id: UUID, **kwargs) -> BalanceCheck:
        """Create new balance check"""
        check = BalanceCheck(
            private_key_id=private_key_id,
            **kwargs
        )
        self.session.add(check)
        self.session.flush()
        return check
    
    def update(self, check_id: UUID, **kwargs) -> bool:
        """Update balance check"""
        result = (
            self.session.query(BalanceCheck)
            .filter(BalanceCheck.id == check_id)
            .update(kwargs)
        )
        return result > 0
    
    def delete(self, check_id: UUID) -> bool:
        """Delete balance check"""
        result = (
            self.session.query(BalanceCheck)
            .filter(BalanceCheck.id == check_id)
            .delete()
        )
        return result > 0
    
    def get_positive_balances(self, min_balance: float = 0.0001) -> List[BalanceCheck]:
        """Get balance checks with positive balances"""
        return (
            self.session.query(BalanceCheck)
            .options(selectinload(BalanceCheck.private_key))
            .filter(BalanceCheck.balance_btc >= min_balance)
            .order_by(desc(BalanceCheck.balance_btc))
            .all()
        )
    
    def get_latest_balance_by_key(self, private_key_id: UUID) -> Optional[BalanceCheck]:
        """Get most recent balance check for a key"""
        return (
            self.session.query(BalanceCheck)
            .filter(BalanceCheck.private_key_id == private_key_id)
            .order_by(desc(BalanceCheck.created_at))
            .first()
        )
    
    def get_stale_balances(self, hours: int = 24) -> List[BalanceCheck]:
        """Get balance checks older than specified hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return (
            self.session.query(BalanceCheck)
            .filter(BalanceCheck.created_at < cutoff_time)
            .all()
        )
