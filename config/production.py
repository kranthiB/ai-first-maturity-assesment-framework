"""
Production configuration for AFS Assessment Framework
"""

import os
from .base import Config


class ProductionConfig(Config):
    """Production configuration with security and performance optimizations"""
    
    DEBUG = False
    TESTING = False
    
    # Security settings for production
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Database settings for production
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_RECORD_QUERIES = False
    
    # Enhanced engine options for production
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('SQLALCHEMY_ENGINE_OPTIONS_POOL_SIZE', 20)),
        'max_overflow': int(os.environ.get('SQLALCHEMY_ENGINE_OPTIONS_MAX_OVERFLOW', 30)),
        'pool_timeout': int(os.environ.get('SQLALCHEMY_ENGINE_OPTIONS_POOL_TIMEOUT', 30)),
        'pool_recycle': int(os.environ.get('SQLALCHEMY_ENGINE_OPTIONS_POOL_RECYCLE', 3600)),
        'pool_pre_ping': True,
    }
    
    # Cache settings for production
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # Logging settings for production
    LOG_LEVEL = 'INFO'
    
    # Performance settings
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year for static files
    
    @staticmethod
    def init_app(app):
        """Initialize production-specific settings"""
        Config.init_app(app)
        
        # Set up production logging
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Ensure logs directory exists
        import os
        if not os.path.exists('logs'):
            os.mkdir('logs')
            
        # Set up file handler
        file_handler = RotatingFileHandler(
            'logs/afs_assessment.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('AFS Assessment Framework startup')
        
        # Additional production validations
        if not app.config.get('SECRET_KEY') or app.config.get('SECRET_KEY') == 'dev-secret-key-change-in-production':
            app.logger.warning('SECRET_KEY not properly configured for production!')