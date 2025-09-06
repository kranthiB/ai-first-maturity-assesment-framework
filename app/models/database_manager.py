"""
Database integration for Flask application

This module provides integration between the database adapter pattern
and the Flask application factory.
"""

import logging
from typing import Optional
from flask import Flask, current_app, g

from .database import get_database_adapter, DatabaseAdapter


logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Database manager for Flask applications
    
    This class manages the database adapter lifecycle within Flask applications
    and provides convenient access to database operations.
    """
    
    def __init__(self, app: Optional[Flask] = None):
        """
        Initialize database manager
        
        Args:
            app: Flask application instance
        """
        self.adapter: Optional[DatabaseAdapter] = None
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask) -> None:
        """
        Initialize database manager with Flask application
        
        Args:
            app: Flask application instance
        """
        # Create database adapter from app configuration
        try:
            self.adapter = get_database_adapter(app.config)
            app.logger.info(f"Database adapter configured: {type(self.adapter).__name__}")
            
            # Connect to database
            if self.adapter.connect():
                app.logger.info("Database connection established")
            else:
                app.logger.error("Failed to establish database connection")
            
            # Store adapter in app extensions
            if not hasattr(app, 'extensions'):
                app.extensions = {}
            app.extensions['database_adapter'] = self.adapter
            
            # Register teardown handler
            app.teardown_appcontext(self._close_db)
            
        except Exception as e:
            app.logger.error(f"Failed to initialize database manager: {str(e)}")
            raise
    
    def get_adapter(self) -> DatabaseAdapter:
        """
        Get the database adapter
        
        Returns:
            DatabaseAdapter instance
            
        Raises:
            RuntimeError: If adapter is not initialized
        """
        if not self.adapter:
            raise RuntimeError("Database adapter not initialized")
        return self.adapter
    
    def _close_db(self, error):
        """Close database connection on app context teardown"""
        # This is handled by the adapter's session management
        pass


def get_db_adapter() -> DatabaseAdapter:
    """
    Get database adapter for current Flask application context
    
    Returns:
        DatabaseAdapter instance
        
    Raises:
        RuntimeError: If called outside application context or adapter not configured
    """
    if not current_app:
        raise RuntimeError("Must be called within Flask application context")
    
    adapter = current_app.extensions.get('database_adapter')
    if not adapter:
        raise RuntimeError("Database adapter not configured")
    
    return adapter


def init_database_with_app(app: Flask) -> DatabaseManager:
    """
    Initialize database manager with Flask application
    
    Args:
        app: Flask application instance
        
    Returns:
        DatabaseManager instance
    """
    db_manager = DatabaseManager(app)
    return db_manager


__all__ = ['DatabaseManager', 'get_db_adapter', 'init_database_with_app']
