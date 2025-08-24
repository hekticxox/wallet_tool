"""
Database Models for Wallet Tool
==============================
Production-ready SQLAlchemy models with proper relationships,
constraints, and indexing for optimal performance.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean, DateTime, Enum as SQLEnum, Float, ForeignKey, Index, Integer, 
    String, Text, UniqueConstraint, event
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class KeyStatus(str, Enum):
    """Status enumeration for private keys"""
    DISCOVERED = "discovered"
    VALIDATED = "validated"
    TESTED = "tested"
    SUCCESS = "success"
    FAILED = "failed"
    ARCHIVED = "archived"

class ScanStatus(str, Enum):
    """Status enumeration for scan operations"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BaseModel:
    """Base model with common fields and utilities"""
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid4,
        comment="Primary key UUID"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Record creation timestamp"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Record last update timestamp"
    )

class ScanSession(Base, BaseModel):
    """
    Represents a wallet scanning session
    Tracks high-level scan operations with metadata
    """
    __tablename__ = "scan_sessions"
    
    name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        comment="Human-readable session name"
    )
    
    status: Mapped[ScanStatus] = mapped_column(
        SQLEnum(ScanStatus),
        default=ScanStatus.PENDING,
        index=True,
        comment="Current session status"
    )
    
    source_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Source directory or file path"
    )
    
    total_files_scanned: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Total number of files processed"
    )
    
    keys_discovered: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Total keys found in this session"
    )
    
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        comment="Session start time"
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        comment="Session completion time"
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Error details if session failed"
    )
    
    metadata_json: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Additional metadata as JSON"
    )
    
    # Relationships
    private_keys: Mapped[list["PrivateKey"]] = relationship(
        "PrivateKey",
        back_populates="scan_session",
        cascade="all, delete-orphan"
    )
    
    test_results: Mapped[list["KeyTestResult"]] = relationship(
        "KeyTestResult",
        back_populates="scan_session"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_scan_sessions_status_created", "status", "created_at"),
        Index("idx_scan_sessions_name", "name"),
    )

class PrivateKey(Base, BaseModel):
    """
    Stores discovered private keys with validation and metadata
    """
    __tablename__ = "private_keys"
    
    key_hex: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="Private key in hexadecimal format"
    )
    
    key_wif: Mapped[Optional[str]] = mapped_column(
        String(52),
        comment="Private key in WIF format if convertible"
    )
    
    status: Mapped[KeyStatus] = mapped_column(
        SQLEnum(KeyStatus),
        default=KeyStatus.DISCOVERED,
        index=True,
        comment="Current key processing status"
    )
    
    source_file: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="File where key was discovered"
    )
    
    source_line: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="Line number in source file"
    )
    
    discovery_pattern: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Regex pattern that matched this key"
    )
    
    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        comment="Whether key passes cryptographic validation"
    )
    
    bitcoin_address: Mapped[Optional[str]] = mapped_column(
        String(62),
        comment="Generated Bitcoin address"
    )
    
    last_tested_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        comment="When key was last tested against BIE1 messages"
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Additional notes or context"
    )
    
    # Foreign Keys
    scan_session_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scan_sessions.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to scan session"
    )
    
    # Relationships
    scan_session: Mapped["ScanSession"] = relationship(
        "ScanSession",
        back_populates="private_keys"
    )
    
    test_results: Mapped[list["KeyTestResult"]] = relationship(
        "KeyTestResult",
        back_populates="private_key",
        cascade="all, delete-orphan"
    )
    
    balance_checks: Mapped[list["BalanceCheck"]] = relationship(
        "BalanceCheck",
        back_populates="private_key",
        cascade="all, delete-orphan"
    )
    
    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint("key_hex", name="uq_private_keys_hex"),
        Index("idx_private_keys_status_valid", "status", "is_valid"),
        Index("idx_private_keys_session_status", "scan_session_id", "status"),
        Index("idx_private_keys_source_file", "source_file"),
    )

class KeyTestResult(Base, BaseModel):
    """
    Results from testing keys against BIE1 messages
    """
    __tablename__ = "key_test_results"
    
    test_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of test performed (bie1_decrypt, etc.)"
    )
    
    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        index=True,
        comment="Whether the test was successful"
    )
    
    test_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Original message/data tested against"
    )
    
    decrypted_content: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Decrypted content if test succeeded"
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Error details if test failed"
    )
    
    execution_time_ms: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Test execution time in milliseconds"
    )
    
    # Foreign Keys
    private_key_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("private_keys.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to tested private key"
    )
    
    scan_session_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scan_sessions.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to scan session"
    )
    
    # Relationships
    private_key: Mapped["PrivateKey"] = relationship(
        "PrivateKey",
        back_populates="test_results"
    )
    
    scan_session: Mapped["ScanSession"] = relationship(
        "ScanSession",
        back_populates="test_results"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_test_results_success", "success"),
        Index("idx_test_results_key_type", "private_key_id", "test_type"),
        Index("idx_test_results_session_success", "scan_session_id", "success"),
    )

class BalanceCheck(Base, BaseModel):
    """
    Bitcoin balance checks for discovered addresses
    """
    __tablename__ = "balance_checks"
    
    bitcoin_address: Mapped[str] = mapped_column(
        String(62),
        nullable=False,
        comment="Bitcoin address checked"
    )
    
    balance_btc: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        comment="Balance in Bitcoin"
    )
    
    balance_usd: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Balance in USD at time of check"
    )
    
    transaction_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Number of transactions for this address"
    )
    
    api_source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="API source used for balance check"
    )
    
    response_time_ms: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="API response time in milliseconds"
    )
    
    # Foreign Keys
    private_key_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("private_keys.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to associated private key"
    )
    
    # Relationships
    private_key: Mapped["PrivateKey"] = relationship(
        "PrivateKey",
        back_populates="balance_checks"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_balance_checks_address", "bitcoin_address"),
        Index("idx_balance_checks_balance", "balance_btc"),
        Index("idx_balance_checks_key_created", "private_key_id", "created_at"),
    )

# Event listeners for automatic timestamp updates
@event.listens_for(Base.metadata, 'before_create')
def receive_before_create(target, connection, **kw):
    """Log table creation events"""
    pass

# Model validation functions
def validate_private_key_hex(key_hex: str) -> bool:
    """Validate hexadecimal private key format"""
    if not key_hex or len(key_hex) != 64:
        return False
    try:
        int(key_hex, 16)
        return True
    except ValueError:
        return False

def validate_bitcoin_address(address: str) -> bool:
    """Basic Bitcoin address validation"""
    if not address:
        return False
    
    # Basic length and character validation
    if len(address) < 26 or len(address) > 62:
        return False
    
    # Check for valid starting characters
    valid_starts = ['1', '3', 'bc1']
    return any(address.startswith(start) for start in valid_starts)
