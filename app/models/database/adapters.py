"""
Database Adapter Abstract Base Classes and Factory

This module defines the abstract interface for database adapters and provides
a factory for creating database-specific adapters.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, Union
from contextlib import contextmanager

from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError


logger = logging.getLogger(__name__)


class DatabaseAdapter(ABC):
    """
    Abstract base class for database adapters
    
    This class defines the interface that all database adapters must implement
    to provide a consistent API across different database backends.
    """
    
    def __init__(self, connection_string: str, **kwargs):
        """
        Initialize the database adapter
        
        Args:
            connection_string: Database connection string
            **kwargs: Additional configuration options
        """
        self.connection_string = connection_string
        self.config = kwargs
        self.engine: Optional[Engine] = None
        self.session_factory: Optional[sessionmaker] = None
        self.metadata = MetaData()
        
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the database
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if database connection is working
        
        Returns:
            bool: True if connection is working, False otherwise
        """
        pass
    
    @abstractmethod
    def create_tables(self, metadata: MetaData) -> bool:
        """
        Create all tables defined in metadata
        
        Args:
            metadata: SQLAlchemy metadata containing table definitions
            
        Returns:
            bool: True if tables created successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def drop_tables(self, metadata: MetaData) -> bool:
        """
        Drop all tables defined in metadata
        
        Args:
            metadata: SQLAlchemy metadata containing table definitions
            
        Returns:
            bool: True if tables dropped successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def execute_query(self, query: str, params: Optional[Dict] = None) -> Any:
        """
        Execute a raw SQL query
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query result
        """
        pass
    
    @abstractmethod
    def execute_script(self, script_path: str) -> bool:
        """
        Execute a SQL script file
        
        Args:
            script_path: Path to SQL script file
            
        Returns:
            bool: True if script executed successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_table_names(self) -> List[str]:
        """
        Get list of all table names in the database
        
        Returns:
            List of table names
        """
        pass
    
    @abstractmethod
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            bool: True if table exists, False otherwise
        """
        pass
    
    @abstractmethod
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get database information (version, etc.)
        
        Returns:
            Dictionary containing database information
        """
        pass
    
    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions
        
        Yields:
            SQLAlchemy session
        """
        if not self.session_factory:
            raise RuntimeError("Database not connected")
            
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_engine(self) -> Engine:
        """
        Get the SQLAlchemy engine
        
        Returns:
            SQLAlchemy engine instance
        """
        if not self.engine:
            raise RuntimeError("Database not connected")
        return self.engine
    
    def _create_engine(self, **engine_options) -> Engine:
        """
        Create SQLAlchemy engine with adapter-specific options
        
        Args:
            **engine_options: Additional engine options
            
        Returns:
            SQLAlchemy engine
        """
        default_options = {
            'echo': self.config.get('echo', False),
            'echo_pool': self.config.get('echo_pool', False),
            'pool_pre_ping': True,
        }
        
        # Merge with provided options
        default_options.update(engine_options)
        
        try:
            engine = create_engine(self.connection_string, **default_options)
            logger.info(f"Database engine created for {self.__class__.__name__}")
            return engine
        except Exception as e:
            logger.error(f"Failed to create database engine: {str(e)}")
            raise
    
    def _create_session_factory(self) -> sessionmaker:
        """
        Create session factory
        
        Returns:
            SQLAlchemy session factory
        """
        if not self.engine:
            raise RuntimeError("Engine not created")
            
        session_factory = sessionmaker(bind=self.engine)
        logger.info("Session factory created")
        return session_factory


class DatabaseFactory:
    """
    Factory class for creating database adapters
    """
    
    _adapters: Dict[str, Type[DatabaseAdapter]] = {}
    
    @classmethod
    def register_adapter(cls, name: str, adapter_class: Type[DatabaseAdapter]):
        """
        Register a database adapter
        
        Args:
            name: Adapter name (e.g., 'h2', 'postgresql', 'mysql')
            adapter_class: Adapter class
        """
        cls._adapters[name.lower()] = adapter_class
        logger.info(f"Registered database adapter: {name}")
    
    @classmethod
    def create_adapter(
        cls, 
        database_type: str, 
        connection_string: str, 
        **kwargs
    ) -> DatabaseAdapter:
        """
        Create a database adapter instance
        
        Args:
            database_type: Type of database ('h2', 'postgresql', 'mysql', etc.)
            connection_string: Database connection string
            **kwargs: Additional configuration options
            
        Returns:
            DatabaseAdapter instance
            
        Raises:
            ValueError: If database type is not supported
        """
        database_type = database_type.lower()
        
        if database_type not in cls._adapters:
            available = ', '.join(cls._adapters.keys())
            raise ValueError(
                f"Unsupported database type: {database_type}. "
                f"Available adapters: {available}"
            )
        
        adapter_class = cls._adapters[database_type]
        adapter = adapter_class(connection_string, **kwargs)
        
        logger.info(f"Created {database_type} adapter")
        return adapter
    
    @classmethod
    def get_supported_databases(cls) -> List[str]:
        """
        Get list of supported database types
        
        Returns:
            List of supported database type names
        """
        return list(cls._adapters.keys())
    
    @classmethod
    def is_supported(cls, database_type: str) -> bool:
        """
        Check if a database type is supported
        
        Args:
            database_type: Database type to check
            
        Returns:
            bool: True if supported, False otherwise
        """
        return database_type.lower() in cls._adapters


def get_database_adapter(app_config: Dict[str, Any]) -> DatabaseAdapter:
    """
    Get database adapter from Flask application configuration
    
    Args:
        app_config: Flask application configuration
        
    Returns:
        DatabaseAdapter instance
        
    Raises:
        ValueError: If database configuration is invalid
    """
    database_uri = app_config.get('SQLALCHEMY_DATABASE_URI')
    if not database_uri:
        raise ValueError("SQLALCHEMY_DATABASE_URI not configured")
    
    database_type = app_config.get('DATABASE_TYPE')
    if not database_type:
        # Try to detect from URI
        if database_uri.startswith('sqlite'):
            database_type = 'sqlite'
        elif database_uri.startswith('postgresql'):
            database_type = 'postgresql'
        elif database_uri.startswith('mysql'):
            database_type = 'mysql'
        elif database_uri.startswith('h2'):
            database_type = 'h2'
        else:
            raise ValueError("Could not determine database type from URI")
    
    # Extract additional configuration
    adapter_config = {
        'echo': app_config.get('SQLALCHEMY_ECHO', False),
        'pool_size': app_config.get('SQLALCHEMY_ENGINE_OPTIONS', {}).get('pool_size'),
        'max_overflow': app_config.get('SQLALCHEMY_ENGINE_OPTIONS', {}).get('max_overflow'),
        'pool_timeout': app_config.get('SQLALCHEMY_ENGINE_OPTIONS', {}).get('pool_timeout'),
        'pool_recycle': app_config.get('SQLALCHEMY_ENGINE_OPTIONS', {}).get('pool_recycle')
    }
    
    # Remove None values
    adapter_config = {k: v for k, v in adapter_config.items() if v is not None}
    
    return DatabaseFactory.create_adapter(
        database_type, 
        database_uri, 
        **adapter_config
    )


__all__ = ['DatabaseAdapter', 'DatabaseFactory', 'get_database_adapter']
