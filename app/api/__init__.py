"""
AI-First Software Engineering Maturity Assessment Framework
API Module - RESTful API Endpoints

Task 4.1: Create RESTful API Endpoints
Provides REST API endpoints for assessment operations.
"""

from .basic_api import create_basic_api_blueprint


def create_api_blueprint():
    """
    Create and configure the main API blueprint.
    
    Returns:
        Blueprint: Configured API blueprint with all endpoints
    """
    return create_basic_api_blueprint()
