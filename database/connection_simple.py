"""
Database Configuration and Connection Management
==============================================
Simplified production-ready database connection handling
"""

import os
import logging
from contextlib import contextmanager
from typing import Optional
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Simple database configuration class"""
    
    def __init__(self):
        self.DB_HOST = os.getenv('DB_HOST', 'localhost')
        self.DB_PORT = int(os.getenv('DB_PORT', '5432'))
        self.DB_NAME = os.getenv('DB_NAME', 'wallet_tool')
        self.DB_USER = os.getenv('DB_USER', 'wallet_user')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD', 'your_secure_password')
        
        # Connection pool settings
        self.DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '10'))
        self.DB_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '20'))
        self.DB_POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))
        self.DB_POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '3600'))
        
        # Performance tuning
        self.DB_ECHO = os.getenv('DB_ECHO', 'false').lower() == 'true'
    
    @property
    def database_url(self) -> str:
        """Generate database URL"""
        password = quote_plus(self.DB_PASSWORD)
        return (
            f"postgresql://{self.DB_USER}:{password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._engine = None
        self._session_factory = None
        self._initialize()
    
    def _initialize(self):
        """Initialize database engine and session factory"""
        try:
            self._engine = create_engine(
                self.config.database_url,
                poolclass=QueuePool,
                pool_size=self.config.DB_POOL_SIZE,
                max_overflow=self.config.DB_MAX_OVERFLOW,
                pool_timeout=self.config.DB_POOL_TIMEOUT,
                pool_recycle=self.config.DB_POOL_RECYCLE,
                echo=self.config.DB_ECHO
            )
            
            self._session_factory = sessionmaker(bind=self._engine)
            
            logger.info(f"Database engine initialized: {self.config.DB_HOST}:{self.config.DB_PORT}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                logger.info("Database connection test successful")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_connection_info(self) -> dict:
        """Get connection information"""
        return {
            "host": self.config.DB_HOST,
            "port": self.config.DB_PORT,
            "database": self.config.DB_NAME,
            "user": self.config.DB_USER,
            "pool_size": self.config.DB_POOL_SIZE,
            "max_overflow": self.config.DB_MAX_OVERFLOW
        }
    
    def create_tables(self):
        """Create all tables"""
        try:
            from .models import Base
            Base.metadata.create_all(self._engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all tables (use with caution!)"""
        try:
            from .models import Base
            Base.metadata.drop_all(self._engine)
            logger.info("Database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise
    
    def get_table_info(self) -> dict:
        """Get information about database tables"""
        try:
            inspector = inspect(self._engine)
            tables = inspector.get_table_names()
            
            table_info = {}
            for table in tables:
                columns = inspector.get_columns(table)
                table_info[table] = {
                    'columns': [col['name'] for col in columns],
                    'column_count': len(columns)
                }
            
            return table_info
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return {}
    
    @property
    def engine(self):
        """Get database engine"""
        return self._engine
    
    def close(self):
        """Close database connections"""
        if self._engine:
            self._engine.dispose()
            logger.info("Database connections closed")
