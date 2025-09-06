"""
Testing configuration for AFS Assessment Framework
"""

import tempfile
import os
from .base import Config


class TestingConfig(Config):
    """Testing configuration with isolated test environment"""
    
    DEBUG = False
    TESTING = True
    
    # Use in-memory SQLite database for fast tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ECHO = False
    
    # Override database type for testing
    DATABASE_TYPE = 'sqlite'
    
    # Disable CSRF for easier testing
    WTF_CSRF_ENABLED = False
    
    # Cache settings for testing
    CACHE_TYPE = 'simple'
    
    # Security settings for testing
    SESSION_COOKIE_SECURE = False
    
    # Create temporary directories for testing
    _temp_dir = None
    
    @classmethod
    def get_temp_dir(cls):
        """Get or create temporary directory for testing"""
        if cls._temp_dir is None:
            cls._temp_dir = tempfile.mkdtemp()
        return cls._temp_dir
    
    @classmethod
    def cleanup_temp_dir(cls):
        """Clean up temporary directory"""
        if cls._temp_dir and os.path.exists(cls._temp_dir):
            import shutil
            shutil.rmtree(cls._temp_dir)
            cls._temp_dir = None
    
    # Use class variables instead of properties for testing
    UPLOAD_FOLDER = '/tmp/afs_test_uploads'
    EXPORT_FOLDER = '/tmp/afs_test_exports'
    
    # Logging settings for testing
    LOG_LEVEL = 'ERROR'  # Only log errors during testing
    
    # Feature flags for testing
    ENABLE_REGISTRATION = True
    ENABLE_API = True
    ENABLE_EXPORTS = True
    ENABLE_ANALYTICS = False  # Disable analytics during testing
    
    @staticmethod
    def init_app(app):
        """Initialize testing-specific settings"""
        Config.init_app(app)
        
        # Set up minimal logging for tests
        import logging
        logging.disable(logging.CRITICAL)
        
        # Create test directories
        test_dirs = [
            app.config.get('UPLOAD_FOLDER'),
            app.config.get('EXPORT_FOLDER')
        ]
        
        for directory in test_dirs:
            if directory:
                os.makedirs(directory, exist_ok=True)