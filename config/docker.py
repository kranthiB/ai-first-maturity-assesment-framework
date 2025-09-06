"""
Docker configuration for AFS Assessment Framework
"""

import os
from .production import ProductionConfig


class DockerConfig(ProductionConfig):
    """Docker configuration based on production with container-specific settings"""
    
    # Override database URI for Docker environment
    @classmethod
    def get_database_uri(cls):
        """Get database URI for Docker environment"""
        # Use environment variables set in docker-compose
        return os.environ.get('DATABASE_URL') or cls.SQLALCHEMY_DATABASE_URI
    
    # Redis settings for Docker
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
    
    # Docker-specific logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    @staticmethod
    def init_app(app):
        """Initialize Docker-specific settings"""
        ProductionConfig.init_app(app)
        
        # Docker containers should log to stdout/stderr
        import logging
        import sys
        
        # Remove existing handlers
        for handler in app.logger.handlers[:]:
            app.logger.removeHandler(handler)
        
        # Add stdout handler for Docker
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
        ))
        handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.addHandler(handler)
        app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        
        app.logger.info('AFS Assessment Framework startup (Docker mode)')
        
        # Validate Docker environment
        required_env_vars = ['DATABASE_URL', 'SECRET_KEY']
        missing_vars = [var for var in required_env_vars 
                       if not os.environ.get(var)]
        
        if missing_vars:
            app.logger.error(f'Missing required environment variables: {missing_vars}')
        else:
            app.logger.info('All required environment variables are set')