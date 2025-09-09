#!/usr/bin/env python3
"""
AFS Assessment Framework - Development Server Entry Point
Run the Flask application in development mode.
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
    print("Warning: python-dotenv not installed. Environment variables from .env file will not be loaded.")

# Import Flask application
try:
    from app import create_app
except ImportError as e:
    print(f"Error importing application: {e}")
    print("Make sure you have installed all dependencies with: pip install -r requirements.txt")
    sys.exit(1)

def main():
    """Main entry point for development server"""
    
    # Get configuration from environment
    debug = os.getenv('FLASK_DEBUG', 'True').lower() in ('true', '1', 'yes', 'on')
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5001))
    
    # Create Flask application
    try:
        app = create_app()
    except Exception as e:
        print(f"Error creating Flask application: {e}")
        sys.exit(1)
    
    # Development-specific configuration
    if debug:
        print("=" * 60)
        print("🚀 AFS Assessment Framework - Development Server")
        print("=" * 60)
        print(f"Environment: {app.config.get('ENV', 'development')}")
        print(f"Debug mode: {debug}")
        print(f"Database: {app.config.get('DATABASE_TYPE', 'unknown')}")
        print(f"Server: http://{host}:{port}")
        print("=" * 60)
        print("\nPress Ctrl+C to stop the server")
        print()
    
    # Run development server
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug,
            use_debugger=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 Development server stopped")
    except Exception as e:
        print(f"Error running development server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
