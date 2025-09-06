"""
Base configuration for AFS Assessment Framework
"""

import os
from pathlib import Path


class Config:
    """Base configuration class with common settings"""
    
    # Application settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    APP_NAME = os.environ.get('APP_NAME', 'AFS Maturity Assessment Framework')
    APP_VERSION = os.environ.get('APP_VERSION', '1.0.0')
    
    # Database settings
    DATABASE_TYPE = os.environ.get('DATABASE_TYPE', 'sqlite')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # Engine options for better performance
    # Database connection pool settings (for MySQL/PostgreSQL)
    @classmethod 
    def get_db_config(cls):
        """Get database-specific configuration"""
        db_type = cls.DATABASE_TYPE.lower()
        
        base_config = {
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SQLALCHEMY_RECORD_QUERIES': True
        }
        
        if db_type == 'sqlite':
            # SQLite doesn't support pool settings
            return base_config
        else:
            # PostgreSQL/MySQL pool settings
            base_config.update({
                'SQLALCHEMY_ENGINE_OPTIONS': {
                    'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),
                    'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 20)),
                    'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30)),
                    'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 3600))
                }
            })
            return base_config
    
    # Flask-WTF settings
    WTF_CSRF_ENABLED = os.environ.get('WTF_CSRF_ENABLED', 'True').lower() == 'true'
    WTF_CSRF_TIME_LIMIT = int(os.environ.get('WTF_CSRF_TIME_LIMIT', 3600))
    
    # Session settings
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    
    # File upload settings
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'static/uploads')
    ALLOWED_EXTENSIONS = set(os.environ.get('ALLOWED_EXTENSIONS', 'csv,xlsx,pdf').split(','))
    
    # Export settings
    EXPORT_FOLDER = os.environ.get('EXPORT_FOLDER', 'data/exports')
    EXPORT_CLEANUP_HOURS = int(os.environ.get('EXPORT_CLEANUP_HOURS', 24))
    
    # Redis/Caching settings
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.environ.get('LOG_FORMAT', 
                               '%(asctime)s %(levelname)s %(name)s %(message)s')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))
    
    # Email settings (for future use)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Feature flags
    ENABLE_REGISTRATION = os.environ.get('ENABLE_REGISTRATION', 'True').lower() == 'true'
    ENABLE_API = os.environ.get('ENABLE_API', 'True').lower() == 'true'
    ENABLE_EXPORTS = os.environ.get('ENABLE_EXPORTS', 'True').lower() == 'true'
    ENABLE_ANALYTICS = os.environ.get('ENABLE_ANALYTICS', 'True').lower() == 'true'
    
    # Analytics settings
    ANALYTICS_ENABLED = os.environ.get('ANALYTICS_ENABLED', 'True').lower() == 'true'
    METRICS_ENABLED = os.environ.get('METRICS_ENABLED', 'False').lower() == 'true'
    
    @staticmethod
    def init_app(app):
        """Initialize application with this configuration"""
        # Create necessary directories
        directories = [
            app.config.get('UPLOAD_FOLDER', 'static/uploads'),
            app.config.get('EXPORT_FOLDER', 'data/exports'),
            'logs',
            'backups'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            
    @classmethod
    def get_database_uri(cls):
        """Get the appropriate database URI based on DATABASE_TYPE"""
        db_type = cls.DATABASE_TYPE.lower()
        
        if db_type == 'postgresql':
            return (f"postgresql://{os.environ.get('POSTGRES_USER')}:"
                   f"{os.environ.get('POSTGRES_PASSWORD')}@"
                   f"{os.environ.get('POSTGRES_HOST', 'localhost')}:"
                   f"{os.environ.get('POSTGRES_PORT', 5432)}/"
                   f"{os.environ.get('POSTGRES_DB')}")
        
        elif db_type == 'mysql':
            return (f"mysql+pymysql://{os.environ.get('MYSQL_USER')}:"
                   f"{os.environ.get('MYSQL_PASSWORD')}@"
                   f"{os.environ.get('MYSQL_HOST', 'localhost')}:"
                   f"{os.environ.get('MYSQL_PORT', 3306)}/"
                   f"{os.environ.get('MYSQL_DATABASE')}")
        
        elif db_type == 'h2':
            h2_path = os.environ.get('H2_DATABASE_PATH', './data/afs_assessment')
            return f"h2://{h2_path}"
        
        else:  # Default to SQLite
            return cls.SQLALCHEMY_DATABASE_URI