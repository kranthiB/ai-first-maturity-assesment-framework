"""
H2 Database Adapter for AFS Assessment Framework

This module provides H2 database support with fallback to SQLite
for development and testing environments.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from sqlalchemy import MetaData, text, inspect
from sqlalchemy.exc import SQLAlchemyError

from .adapters import DatabaseAdapter, DatabaseFactory


logger = logging.getLogger(__name__)


class H2Adapter(DatabaseAdapter):
    """
    H2 Database Adapter with SQLite fallback
    
    This adapter provides H2 database support for production environments
    and automatically falls back to SQLite for development/testing.
    """
    
    def __init__(self, connection_string: str, **kwargs):
        """
        Initialize H2 adapter
        
        Args:
            connection_string: H2 connection string
            **kwargs: Additional configuration options
        """
        super().__init__(connection_string, **kwargs)
        self.is_h2 = self._is_h2_connection()
        self.database_file = self._extract_database_file()
        
    def _is_h2_connection(self) -> bool:
        """Check if connection string is for H2 database"""
        return self.connection_string.startswith(('h2:', 'jdbc:h2:'))
    
    def _extract_database_file(self) -> Optional[str]:
        """Extract database file path from connection string"""
        if self.is_h2:
            # H2 connection string format: h2:file:/path/to/db
            if ':file:' in self.connection_string:
                return self.connection_string.split(':file:')[1].split(';')[0]
        elif self.connection_string.startswith('sqlite:'):
            # SQLite connection string format: sqlite:///path/to/db
            if ':///' in self.connection_string:
                return self.connection_string.split('///')[1]
        return None
    
    def connect(self) -> bool:
        """
        Establish connection to H2 database
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Create database directory if needed
            if self.database_file:
                db_dir = Path(self.database_file).parent
                db_dir.mkdir(parents=True, exist_ok=True)
            
            # Configure engine options based on database type
            engine_options = self._get_engine_options()
            
            # Create engine
            self.engine = self._create_engine(**engine_options)
            
            # Create session factory
            self.session_factory = self._create_session_factory()
            
            # Test connection
            if self.test_connection():
                logger.info(f"Successfully connected to {'H2' if self.is_h2 else 'SQLite'} database")
                return True
            else:
                logger.error("Connection test failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            return False
    
    def disconnect(self) -> None:
        """Close database connection"""
        try:
            if self.engine:
                self.engine.dispose()
                logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")
        finally:
            self.engine = None
            self.session_factory = None
    
    def test_connection(self) -> bool:
        """
        Test if database connection is working
        
        Returns:
            bool: True if connection is working, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                # Test with a simple query
                if self.is_h2:
                    result = conn.execute(text("SELECT 1 FROM DUAL"))
                else:
                    result = conn.execute(text("SELECT 1"))
                result.fetchone()
                return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def create_tables(self, metadata: MetaData) -> bool:
        """
        Create all tables defined in metadata
        
        Args:
            metadata: SQLAlchemy metadata containing table definitions
            
        Returns:
            bool: True if tables created successfully, False otherwise
        """
        try:
            metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to create tables: {str(e)}")
            return False
    
    def drop_tables(self, metadata: MetaData) -> bool:
        """
        Drop all tables defined in metadata
        
        Args:
            metadata: SQLAlchemy metadata containing table definitions
            
        Returns:
            bool: True if tables dropped successfully, False otherwise
        """
        try:
            metadata.drop_all(self.engine)
            logger.info("Database tables dropped successfully")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to drop tables: {str(e)}")
            return False
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> Any:
        """
        Execute a raw SQL query
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query result
        """
        try:
            with self.engine.connect() as conn:
                if params:
                    result = conn.execute(text(query), params)
                else:
                    result = conn.execute(text(query))
                
                # Return fetchall for SELECT queries, rowcount for others
                if query.strip().upper().startswith('SELECT'):
                    return result.fetchall()
                else:
                    conn.commit()
                    return result.rowcount
                    
        except SQLAlchemyError as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    def execute_script(self, script_path: str) -> bool:
        """
        Execute a SQL script file
        
        Args:
            script_path: Path to SQL script file
            
        Returns:
            bool: True if script executed successfully, False otherwise
        """
        try:
            if not os.path.exists(script_path):
                logger.error(f"SQL script not found: {script_path}")
                return False
            
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            # Split script into individual statements
            statements = self._split_sql_statements(script_content)
            
            with self.engine.connect() as conn:
                for statement in statements:
                    if statement.strip():
                        conn.execute(text(statement))
                conn.commit()
            
            logger.info(f"SQL script executed successfully: {script_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute SQL script {script_path}: {str(e)}")
            return False
    
    def get_table_names(self) -> List[str]:
        """
        Get list of all table names in the database
        
        Returns:
            List of table names
        """
        try:
            inspector = inspect(self.engine)
            return inspector.get_table_names()
        except Exception as e:
            logger.error(f"Failed to get table names: {str(e)}")
            return []
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            bool: True if table exists, False otherwise
        """
        try:
            inspector = inspect(self.engine)
            return table_name in inspector.get_table_names()
        except Exception as e:
            logger.error(f"Failed to check table existence: {str(e)}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get database information (version, etc.)
        
        Returns:
            Dictionary containing database information
        """
        info = {
            'type': 'H2' if self.is_h2 else 'SQLite',
            'connection_string': self.connection_string,
            'database_file': self.database_file,
        }
        
        try:
            with self.engine.connect() as conn:
                if self.is_h2:
                    # H2 version query
                    result = conn.execute(text("SELECT H2VERSION() as version"))
                    version_row = result.fetchone()
                    info['version'] = version_row[0] if version_row else 'Unknown'
                else:
                    # SQLite version query
                    result = conn.execute(text("SELECT sqlite_version() as version"))
                    version_row = result.fetchone()
                    info['version'] = version_row[0] if version_row else 'Unknown'
                    
        except Exception as e:
            logger.error(f"Failed to get database version: {str(e)}")
            info['version'] = 'Unknown'
        
        return info
    
    def _get_engine_options(self) -> Dict[str, Any]:
        """Get database-specific engine options"""
        options = {
            'echo': self.config.get('echo', False),
            'pool_pre_ping': True,
        }
        
        if self.is_h2:
            # H2-specific options
            options.update({
                'pool_size': self.config.get('pool_size', 10),
                'max_overflow': self.config.get('max_overflow', 20),
                'pool_timeout': self.config.get('pool_timeout', 30),
                'pool_recycle': self.config.get('pool_recycle', 3600),
            })
        else:
            # SQLite-specific options
            options.update({
                'connect_args': {'check_same_thread': False},
                'poolclass': None,  # Disable pooling for SQLite
            })
        
        return options
    
    def _split_sql_statements(self, script_content: str) -> List[str]:
        """
        Split SQL script into individual statements
        
        Args:
            script_content: SQL script content
            
        Returns:
            List of SQL statements
        """
        # Simple statement splitting - can be enhanced for complex cases
        statements = []
        current_statement = []
        
        for line in script_content.split('\n'):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('--') or line.startswith('/*'):
                continue
            
            current_statement.append(line)
            
            # Check for statement terminator
            if line.endswith(';'):
                statement = ' '.join(current_statement)
                if statement.strip() != ';':
                    statements.append(statement)
                current_statement = []
        
        # Add any remaining statement
        if current_statement:
            statement = ' '.join(current_statement)
            if statement.strip():
                statements.append(statement)
        
        return statements


# Register the adapter with the factory
DatabaseFactory.register_adapter('h2', H2Adapter)
DatabaseFactory.register_adapter('sqlite', H2Adapter)


__all__ = ['H2Adapter']
