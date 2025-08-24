"""
Database Configuration and Connection Management
==============================================
Production-ready database connection handling with pooling,
health checks, and environment-based configuration.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings
from pydantic import validator
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

class DatabaseConfig(BaseSettings):
    """
    Database configuration with validation and environment support
    """
    
    # Core connection parameters
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "wallet_tool"
    DB_USER: str = "wallet_user"
    DB_PASSWORD: str = ""
    
    # Connection pool settings
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600  # 1 hour
    
    # Performance tuning
    DB_ECHO: bool = False  # SQL logging
    DB_ECHO_POOL: bool = False  # Connection pool logging
    
    # Health check settings
    HEALTH_CHECK_TIMEOUT: int = 5
    HEALTH_CHECK_INTERVAL: int = 60
    
    # Environment
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @validator("DB_PASSWORD")
    def validate_password(cls, v):
        if not v and os.getenv("ENVIRONMENT") == "production":
            raise ValueError("Database password required in production")
        return v
    
    @validator("DB_POOL_SIZE")
    def validate_pool_size(cls, v):
        if v < 1 or v > 50:
            raise ValueError("Pool size must be between 1 and 50")
        return v
    
    def get_database_url(self, async_driver: bool = False) -> str:
        """Generate database URL with proper escaping"""
        password = quote_plus(self.DB_PASSWORD) if self.DB_PASSWORD else ""
        
        if async_driver:
            driver = "postgresql+asyncpg"
        else:
            driver = "postgresql+psycopg2"
        
        if password:
            auth = f"{self.DB_USER}:{password}"
        else:
            auth = self.DB_USER
        
        return f"{driver}://{auth}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

class DatabaseManager:
    """
    Centralized database connection management with health monitoring
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._engine: Optional[Engine] = None
        self._async_engine = None
        self._session_factory = None
        self._async_session_factory = None
        self._is_healthy = False
    
    def initialize(self) -> None:
        """Initialize database engines and session factories"""
        try:
            # Create synchronous engine
            self._engine = create_engine(
                self.config.get_database_url(async_driver=False),
                poolclass=QueuePool,
                pool_size=self.config.DB_POOL_SIZE,
                max_overflow=self.config.DB_MAX_OVERFLOW,
                pool_timeout=self.config.DB_POOL_TIMEOUT,
                pool_recycle=self.config.DB_POOL_RECYCLE,
                echo=self.config.DB_ECHO,
                echo_pool=self.config.DB_ECHO_POOL,
                future=True
            )
            
            # Create async engine
            self._async_engine = create_async_engine(
                self.config.get_database_url(async_driver=True),
                pool_size=self.config.DB_POOL_SIZE,
                max_overflow=self.config.DB_MAX_OVERFLOW,
                pool_timeout=self.config.DB_POOL_TIMEOUT,
                pool_recycle=self.config.DB_POOL_RECYCLE,
                echo=self.config.DB_ECHO,
                future=True
            )
            
            # Create session factories
            self._session_factory = sessionmaker(
                bind=self._engine,
                expire_on_commit=False
            )
            
            self._async_session_factory = sessionmaker(
                bind=self._async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Set up event listeners
            self._setup_event_listeners()
            
            logger.info(f"Database manager initialized for {self.config.ENVIRONMENT}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database manager: {e}")
            raise
    
    def _setup_event_listeners(self) -> None:
        """Set up SQLAlchemy event listeners for monitoring"""
        
        @event.listens_for(self._engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            logger.debug("New database connection established")
        
        @event.listens_for(self._engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            logger.debug("Connection checked out from pool")
        
        @event.listens_for(self._engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            logger.debug("Connection returned to pool")
        
        @event.listens_for(self._engine, "invalid")
        def on_invalid(dbapi_connection, connection_record, exception):
            logger.warning(f"Connection invalidated: {exception}")
    
    async def health_check(self) -> bool:
        """Perform database health check"""
        try:
            if not self._async_engine:
                return False
            
            async with self._async_engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                success = result.scalar() == 1
                self._is_healthy = success
                return success
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            self._is_healthy = False
            return False
    
    def get_session(self):
        """Get synchronous database session"""
        if not self._session_factory:
            raise RuntimeError("Database manager not initialized")
        return self._session_factory()
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session with proper cleanup"""
        if not self._async_session_factory:
            raise RuntimeError("Database manager not initialized")
        
        async with self._async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    def get_engine_stats(self) -> dict:
        """Get connection pool statistics"""
        if not self._engine:
            return {}
        
        pool = self._engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
            "is_healthy": self._is_healthy
        }
    
    async def close(self) -> None:
        """Clean shutdown of database connections"""
        try:
            if self._async_engine:
                await self._async_engine.dispose()
            
            if self._engine:
                self._engine.dispose()
            
            logger.info("Database connections closed")
            
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")

# Global database manager instance
db_manager = DatabaseManager()

def get_db_session():
    """Dependency injection helper for synchronous sessions"""
    return db_manager.get_session()

async def get_async_db_session():
    """Dependency injection helper for async sessions"""
    async with db_manager.get_async_session() as session:
        yield session
