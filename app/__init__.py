"""
AFS Assessment Framework - Flask Application Factory

This module implements the Flask application factory pattern for the
AI-First Software Engineering Maturity Assessment Framework.
"""

import os
from typing import Optional

from flask import Flask, request, jsonify, current_app, render_template
from werkzeug.exceptions import HTTPException
import click

# Import extensions
from .extensions import (
    db, migrate, csrf, cache
)

# Import configuration
from .config import ConfigValidator, setup_logging, load_environment_config


def create_app(config_name: Optional[str] = None) -> Flask:
    """
    Flask application factory
    
    Args:
        config_name: Configuration name (development, production, testing, docker)
                    If None, will be determined from FLASK_ENV environment variable
        
    Returns:
        Flask: Configured Flask application instance
    """
    # Get the project root directory (parent of app directory)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    app = Flask(__name__,
                template_folder=os.path.join(project_root, 'templates'),
                static_folder=os.path.join(project_root, 'static'))
    
    # Load configuration
    config_name = config_name or _determine_config_name()
    _load_configuration(app, config_name)
    
    # Set up logging
    setup_logging(app)
    app.logger.info(f"Starting AFS Assessment Framework in {config_name} mode")
    
    # Initialize extensions
    _initialize_extensions(app)
    
    # Register blueprints
    _register_blueprints(app)
    
    # Register error handlers
    _register_error_handlers(app)
    
    # Register context processors
    _register_context_processors(app)
    
    # Register CLI commands
    _register_cli_commands(app)
    
    # Validate configuration
    if not ConfigValidator.validate_all(app):
        app.logger.error("Application configuration validation failed")
        if not app.testing:
            raise RuntimeError("Invalid application configuration")
    
    app.logger.info("Application initialization completed successfully")
    return app


def _determine_config_name() -> str:
    """
    Determine configuration name from environment
    
    Returns:
        str: Configuration name
    """
    flask_env = os.environ.get('FLASK_ENV', 'development').lower()
    
    # Map Flask environment to our config names
    config_map = {
        'development': 'development',
        'production': 'production',
        'testing': 'testing',
        'docker': 'docker'
    }
    
    return config_map.get(flask_env, 'development')


def _load_configuration(app: Flask, config_name: str) -> None:
    """
    Load configuration for the given environment
    
    Args:
        app: Flask application instance
        config_name: Configuration name
    """
    # Import configuration classes
    from config.base import Config
    from config.development import DevelopmentConfig
    from config.production import ProductionConfig
    from config.testing import TestingConfig
    from config.docker import DockerConfig
    
    config_classes = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig,
        'docker': DockerConfig
    }
    
    config_class = config_classes.get(config_name, DevelopmentConfig)
    app.config.from_object(config_class)
    
    # Apply database-specific configuration
    db_config = config_class.get_db_config() if hasattr(config_class, 'get_db_config') else Config.get_db_config()
    app.config.update(db_config)
    
    # Override with environment variables
    env_config = load_environment_config()
    app.config.update(env_config)
    
    # Set config name for reference
    app.config['CONFIG_NAME'] = config_name
    
    app.logger.info(f"Configuration loaded: {config_name}")


def _initialize_extensions(app: Flask) -> None:
    """
    Initialize Flask extensions
    
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
    
    app.logger.info("Extensions initialized")


def _register_blueprints(app: Flask) -> None:
    """
    Register application blueprints
    
    Args:
        app: Flask application instance
    """
    # Main blueprint
    from .blueprints.main import main_bp
    app.register_blueprint(main_bp)
    
    # Assessment blueprint
    from .blueprints.assessment import assessment_bp
    app.register_blueprint(assessment_bp, url_prefix='/assessment')
    
    # API blueprint
    from .api import create_api_blueprint
    api_bp = create_api_blueprint()
    app.register_blueprint(api_bp)
    
    app.logger.info("Blueprints registered")


def _register_error_handlers(app: Flask) -> None:
    """
    Register error handlers
    
    Args:
        app: Flask application instance
    """
    @app.errorhandler(400)
    def bad_request(error):
        if request.is_json:
            return jsonify({
                'error': 'Bad Request',
                'message': 'The request could not be understood',
                'status_code': 400
            }), 400
        return app.send_static_file('templates/errors/400.html'), 400
    
    @app.errorhandler(403)
    def forbidden(error):
        if request.is_json:
            return jsonify({
                'error': 'Forbidden',
                'message': 'Access denied',
                'status_code': 403
            }), 403
        return app.send_static_file('templates/errors/403.html'), 403
    
    @app.errorhandler(404)
    def not_found(error):
        if request.is_json:
            return jsonify({
                'error': 'Not Found',
                'message': 'The requested resource was not found',
                'status_code': 404
            }), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {str(error)}")
        if request.is_json:
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred',
                'status_code': 500
            }), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        if request.is_json:
            return jsonify({
                'error': error.name,
                'message': error.description,
                'status_code': error.code
            }), error.code
        return error
    
    app.logger.info("Error handlers registered")


def _register_context_processors(app: Flask) -> None:
    """
    Register template context processors
    
    Args:
        app: Flask application instance
    """
    @app.context_processor
    def inject_config():
        """Inject configuration variables into templates"""
        return {
            'config_name': app.config.get('CONFIG_NAME', 'unknown'),
            'debug': app.debug,
            'app_name': app.config.get('APP_NAME', 'AFS Assessment'),
            'version': app.config.get('VERSION', '1.0.0')
        }
    
    @app.context_processor
    def utility_processor():
        """Inject utility functions into templates"""
        def format_industry(industry_value):
            """Format industry value for display"""
            if not industry_value:
                return ''
            
            # Mapping for special cases
            industry_mapping = {
                'bfsi': 'BFSI',
                'energy_utilities': 'Energy & Utilities',
                'government': 'Government Public Sector',
                'travel_transport_tourism': 'Travel, Transport & Tourism',
                'media_communications': 'Media & Communications',
                'retail_commerce': 'Retail & Commerce',
                'automotive': 'Automotive',
                'healthcare': 'Healthcare',
                'technology': 'Technology',
                'other': 'Other'
            }
            
            return industry_mapping.get(
                industry_value.lower(),
                industry_value.replace('_', ' ').title()
            )
        
        return {
            'enumerate': enumerate,
            'len': len,
            'str': str,
            'int': int,
            'format_industry': format_industry
        }
    
    app.logger.info("Context processors registered")


def _register_cli_commands(app: Flask) -> None:
    """
    Register CLI commands
    
    Args:
        app: Flask application instance
    """
    @app.cli.command()
    def init_db():
        """Initialize the database"""
        from scripts.setup import setup_database
        setup_database()
        click.echo("Database initialized")
    
    @app.cli.command()
    def seed_db():
        """Seed the database with initial data"""
        from scripts.seed_database import seed_database
        seed_database()
        click.echo("Database seeded")
    
    @app.cli.command()
    def validate_config():
        """Validate application configuration"""
        if ConfigValidator.validate_all(current_app):
            click.echo("Configuration is valid")
        else:
            click.echo("Configuration validation failed")
    
    app.logger.info("CLI commands registered")


# Create application instance for WSGI
application = create_app()


__all__ = ['create_app', 'application']