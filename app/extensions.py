"""
Flask extensions initialization for AFS Assessment Framework

Extensions are initialized here to avoid circular imports.
They are configured in the application factory.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_caching import Cache


# Initialize core extensions
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
cache = Cache()


def init_extensions(app):
    """
    Initialize Flask extensions with application instance
    
    Args:
        app: Flask application instance
    """
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Initialize Flask-Migrate
    migrate.init_app(app, db)
    
    # Initialize CSRF protection
    csrf.init_app(app)
    
    # Initialize caching
    cache.init_app(app)
    
    # Set up additional extension configurations
    _configure_sqlalchemy(app)
    _configure_cache(app)


def _configure_sqlalchemy(app):
    """Configure SQLAlchemy-specific settings"""
    
    @app.before_first_request
    def create_tables():
        """Create database tables if they don't exist"""
        try:
            # Try to create tables if they don't exist
            db.create_all()
            app.logger.info("Database tables ensured")
        except Exception as e:
            app.logger.error(f"Error creating database tables: {str(e)}")
    
    @app.teardown_appcontext
    def close_db(error):
        """Close database connection on app context teardown"""
        if error:
            db.session.rollback()
        db.session.remove()


def _configure_cache(app):
    """Configure caching-specific settings"""
    
    if app.config.get('CACHE_TYPE') == 'redis':
        # Additional Redis cache configuration if needed
        try:
            # Test Redis connection
            cache.clear()
            app.logger.info("Redis cache connection successful")
        except Exception as e:
            app.logger.warning(f"Redis cache connection failed: {str(e)}")
            # Fallback to simple cache
            app.config['CACHE_TYPE'] = 'simple'
            cache.init_app(app)
            app.logger.info("Fallback to simple cache")


__all__ = [
    'db', 'migrate', 'csrf', 'cache', 'init_extensions'
]