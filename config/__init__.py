"""
Configuration module for AFS Assessment Framework

Provides different configurations for different environments:
- Development: Debug enabled, SQLite database
- Production: Security hardened, performance optimized
- Testing: In-memory database, minimal logging
- Docker: Container-optimized production settings
"""

import os
from .base import Config
from .development import DevelopmentConfig
from .production import ProductionConfig
from .testing import TestingConfig
from .docker import DockerConfig


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """
    Get configuration class based on environment
    
    Args:
        config_name (str): Configuration name or None to auto-detect
        
    Returns:
        Config: Configuration class
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return config.get(config_name, DevelopmentConfig)


__all__ = [
    'Config',
    'DevelopmentConfig', 
    'ProductionConfig',
    'TestingConfig',
    'DockerConfig',
    'config',
    'get_config'
]