"""
MySQL Database Adapter for AFS Assessment Framework

This module provides MySQL/MariaDB database support with connection pooling
and MySQL-specific optimizations.
"""

import logging
from typing import Dict, Any, List, Optional

from sqlalchemy import MetaData, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool

from .adapters import DatabaseAdapter, DatabaseFactory


logger = logging.getLogger(__name__)


class MySQLAdapter(DatabaseAdapter):
    """
    MySQL Database Adapter
    
    This adapter provides full MySQL/MariaDB support with connection pooling,
    MySQL-specific optimizations, and production-ready configurations.
    """
    
    def connect(self) -> bool:
        """
        Establish connection to MySQL database
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Configure MySQL-specific engine options
            engine_options = self._get_engine_options()
            
            # Create engine
            self.engine = self._create_engine(**engine_options)
            
            # Create session factory
            self.session_factory = self._create_session_factory()
            
            # Test connection
            if self.test_connection():
                logger.info("Successfully connected to MySQL database")
                return True
            else:
                logger.error("MySQL connection test failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to MySQL: {str(e)}")
            return False
    
    def disconnect(self) -> None:
        """Close MySQL database connection"""
        try:
            if self.engine:
                self.engine.dispose()
                logger.info("MySQL connection closed")
        except Exception as e:
            logger.error(f"Error closing MySQL connection: {str(e)}")
        finally:
            self.engine = None
            self.session_factory = None
    
    def test_connection(self) -> bool:
        """
        Test if MySQL connection is working
        
        Returns:
            bool: True if connection is working, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT VERSION()"))
                version_info = result.fetchone()
                logger.debug(f"MySQL version: {version_info[0]}")
                return True
        except Exception as e:
            logger.error(f"MySQL connection test failed: {str(e)}")
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
            logger.info("MySQL tables created successfully")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to create MySQL tables: {str(e)}")
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
            logger.info("MySQL tables dropped successfully")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to drop MySQL tables: {str(e)}")
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
            logger.error(f"MySQL query execution failed: {str(e)}")
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
            import os
            if not os.path.exists(script_path):
                logger.error(f"SQL script not found: {script_path}")
                return False
            
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            # Split script into individual statements for MySQL
            statements = self._split_sql_statements(script_content)
            
            with self.engine.connect() as conn:
                with conn.begin():
                    for statement in statements:
                        if statement.strip():
                            conn.execute(text(statement))
            
            logger.info(f"MySQL script executed: {script_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute MySQL script {script_path}: {str(e)}")
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
            logger.error(f"Failed to get MySQL table names: {str(e)}")
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
            logger.error(f"Failed to check MySQL table existence: {str(e)}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get MySQL database information
        
        Returns:
            Dictionary containing database information
        """
        info = {
            'type': 'MySQL',
            'connection_string': self._sanitize_connection_string(),
        }
        
        try:
            with self.engine.connect() as conn:
                # Get MySQL version
                result = conn.execute(text("SELECT VERSION()"))
                version_row = result.fetchone()
                info['version'] = version_row[0] if version_row else 'Unknown'
                
                # Get database name
                result = conn.execute(text("SELECT DATABASE()"))
                db_row = result.fetchone()
                info['database'] = db_row[0] if db_row else 'Unknown'
                
                # Get current user
                result = conn.execute(text("SELECT USER()"))
                user_row = result.fetchone()
                info['user'] = user_row[0] if user_row else 'Unknown'
                
                # Get connection count
                result = conn.execute(text("SHOW STATUS LIKE 'Threads_connected'"))
                conn_row = result.fetchone()
                info['active_connections'] = conn_row[1] if conn_row else 0
                
                # Get engine type
                result = conn.execute(text("SHOW ENGINES"))
                engines = result.fetchall()
                default_engine = next((e[0] for e in engines if e[1] == 'DEFAULT'), 'Unknown')
                info['default_engine'] = default_engine
                
        except Exception as e:
            logger.error(f"Failed to get MySQL info: {str(e)}")
            info['version'] = 'Unknown'
        
        return info
    
    def create_indexes(self, table_name: str, indexes: List[Dict[str, Any]]) -> bool:
        """
        Create indexes on a MySQL table
        
        Args:
            table_name: Name of the table
            indexes: List of index definitions
            
        Returns:
            bool: True if indexes created successfully
        """
        try:
            with self.engine.connect() as conn:
                for index_def in indexes:
                    index_name = index_def.get('name')
                    columns = index_def.get('columns', [])
                    unique = index_def.get('unique', False)
                    
                    if not index_name or not columns:
                        continue
                    
                    # Check if index already exists
                    check_query = f"""
                        SELECT COUNT(*) as count 
                        FROM INFORMATION_SCHEMA.STATISTICS 
                        WHERE TABLE_SCHEMA = DATABASE() 
                        AND TABLE_NAME = '{table_name}' 
                        AND INDEX_NAME = '{index_name}'
                    """
                    result = conn.execute(text(check_query))
                    exists = result.fetchone()[0] > 0
                    
                    if not exists:
                        unique_clause = 'UNIQUE ' if unique else ''
                        columns_str = ', '.join(columns)
                        
                        query = f"""
                            CREATE {unique_clause}INDEX {index_name} 
                            ON {table_name} ({columns_str})
                        """
                        
                        conn.execute(text(query))
                        logger.debug(f"Created index {index_name} on {table_name}")
                
                conn.commit()
            
            logger.info(f"Indexes created for table {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {str(e)}")
            return False
    
    def optimize_table(self, table_name: str) -> bool:
        """
        Run OPTIMIZE TABLE on a MySQL table
        
        Args:
            table_name: Name of the table to optimize
            
        Returns:
            bool: True if optimization completed successfully
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text(f"OPTIMIZE TABLE {table_name}"))
                conn.commit()
            
            logger.info(f"Optimized table {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to optimize table {table_name}: {str(e)}")
            return False
    
    def analyze_table(self, table_name: str) -> bool:
        """
        Run ANALYZE TABLE on a MySQL table to update statistics
        
        Args:
            table_name: Name of the table to analyze
            
        Returns:
            bool: True if analysis completed successfully
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text(f"ANALYZE TABLE {table_name}"))
                conn.commit()
            
            logger.info(f"Analyzed table {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to analyze table {table_name}: {str(e)}")
            return False
    
    def _get_engine_options(self) -> Dict[str, Any]:
        """Get MySQL-specific engine options"""
        return {
            'echo': self.config.get('echo', False),
            'pool_size': self.config.get('pool_size', 10),
            'max_overflow': self.config.get('max_overflow', 20),
            'pool_timeout': self.config.get('pool_timeout', 30),
            'pool_recycle': self.config.get('pool_recycle', 3600),
            'pool_pre_ping': True,
            'poolclass': QueuePool,
            'connect_args': {
                'connect_timeout': 10,
                'charset': 'utf8mb4',
                'use_unicode': True,
                'autocommit': False
            }
        }
    
    def _sanitize_connection_string(self) -> str:
        """Remove password from connection string for logging"""
        import re
        # Remove password from connection string
        sanitized = re.sub(r':([^:@]+)@', ':****@', self.connection_string)
        return sanitized
    
    def _split_sql_statements(self, script_content: str) -> List[str]:
        """
        Split SQL script into individual statements
        
        Args:
            script_content: SQL script content
            
        Returns:
            List of SQL statements
        """
        statements = []
        current_statement = []
        in_delimiter_block = False
        
        for line in script_content.split('\n'):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('--') or line.startswith('#'):
                continue
            
            # Handle MySQL DELIMITER statements
            if line.upper().startswith('DELIMITER'):
                in_delimiter_block = not in_delimiter_block
                continue
            
            current_statement.append(line)
            
            # Check for statement terminator
            if not in_delimiter_block and line.endswith(';'):
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
DatabaseFactory.register_adapter('mysql', MySQLAdapter)
DatabaseFactory.register_adapter('mariadb', MySQLAdapter)


__all__ = ['MySQLAdapter']
