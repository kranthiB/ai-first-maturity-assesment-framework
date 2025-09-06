#!/usr/bin/env python3
"""
AFS Assessment Framework - WSGI Entry Point
Production WSGI server entry point for deployment with Gunicorn, uWSGI, etc.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # In production, environment variables should be set by the system
    pass

# Set production environment if not specified
if not os.getenv('FLASK_ENV'):
    os.environ['FLASK_ENV'] = 'production'

# Import Flask application
try:
    from app import create_app
    
    # Create application instance
    application = create_app()
    app = application  # Alias for compatibility
    
    # Production-specific configuration
    if application.config.get('ENV') == 'production':
        # Disable debug mode in production
        application.debug = False
        
        # Log application startup
        application.logger.info("AFS Assessment Framework started in production mode")
        application.logger.info(f"Database: {application.config.get('DATABASE_TYPE', 'unknown')}")
        application.logger.info(f"Debug mode: {application.debug}")

except ImportError as e:
    print(f"Error importing application: {e}")
    print("Make sure all dependencies are installed and the app module is available.")
    sys.exit(1)
except Exception as e:
    print(f"Error creating Flask application: {e}")
    sys.exit(1)

# Health check endpoint for load balancers
@application.route('/health')
def health_check():
    """Simple health check endpoint for load balancers and monitoring"""
    try:
        # Basic application health check
        from app.extensions import db
        
        # Test database connectivity
        db.session.execute('SELECT 1')
        
        return {
            'status': 'healthy',
            'service': 'afs-assessment-framework',
            'timestamp': application.extensions.get('start_time', 'unknown')
        }, 200
        
    except Exception as e:
        application.logger.error(f"Health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'service': 'afs-assessment-framework'
        }, 503

# Application factory function for testing
def create_wsgi_app(config_name='production'):
    """
    Create WSGI application instance with specific configuration
    
    Args:
        config_name (str): Configuration name ('production', 'development', etc.)
    
    Returns:
        Flask application instance
    """
    os.environ['FLASK_ENV'] = config_name
    return create_app()

if __name__ == '__main__':
    # This should not be used in production
    # Use a proper WSGI server like Gunicorn instead
    print("Warning: Running WSGI application directly is not recommended for production.")
    print("Use a proper WSGI server like Gunicorn:")
    print("  gunicorn --bind 0.0.0.0:5000 wsgi:application")
    
    # Run with development server for testing
    application.run(host='127.0.0.1', port=5000, debug=False)
