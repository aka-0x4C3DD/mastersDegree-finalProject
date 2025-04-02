"""
API endpoints package initialization
"""
from flask import Flask

def register_routes(app, model_manager, device_config):
    """Register all API routes with the Flask app"""
    # Import route registration functions
    from .health import register_health_routes
    from .query import register_query_routes
    from .file_processor import register_file_routes
    from .medical_terms import register_term_routes
    
    # Register routes
    register_health_routes(app, model_manager, device_config)
    register_query_routes(app, model_manager, device_config)
    register_file_routes(app, model_manager, device_config)
    register_term_routes(app)
