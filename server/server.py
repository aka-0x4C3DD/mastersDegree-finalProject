"""
ClinicalGPT Medical Assistant - Main server module
This is the entry point for the Flask server application.
"""
import os
import sys
import time
import traceback
import logging
from flask import Flask, send_from_directory
from flask_cors import CORS

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
logger = logging.getLogger(__name__)

# Disable Intel Extension auto-loading to prevent errors
os.environ["TORCH_DEVICE_BACKEND_AUTOLOAD"] = "0"

try:
    logger.info("Starting ClinicalGPT Medical Assistant server...")
    
    # Import server modules
    from server.config import load_config
    from server.utils.device_detection import detect_devices
    from server.model_management import ModelManager  # Updated import path
    from server.api import register_routes
    
    # Load configuration
    config = load_config()
    
    # Detect available devices
    device_config = detect_devices()
    
    # Set up static folder path
    static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    logger.info(f"Static folder path: {static_folder}")
    
    # Initialize Flask app
    app = Flask(__name__, static_folder=static_folder)
    CORS(app)  # Enable CORS for all routes
    
    # Initialize model manager
    model_manager = ModelManager(config['model_path'], device_config)
    model_manager.load_model()
    
    # Register static file routes
    @app.route('/')
    def index():
        """Serve the main web interface"""
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/js/<path:filename>')
    def serve_js(filename):
        """Serve JavaScript files"""
        return send_from_directory(os.path.join(app.static_folder, 'js'), filename)

    @app.route('/css/<path:filename>')
    def serve_css(filename):
        """Serve CSS files"""
        return send_from_directory(os.path.join(app.static_folder, 'css'), filename)
    
    # Register API routes
    register_routes(app, model_manager, device_config)
    
    # Run the app if executed directly
    if __name__ == '__main__':
        try:
            logger.info(f"Starting server on http://localhost:{config['port']}")
            app.run(host='0.0.0.0', port=config['port'], debug=config['debug'], use_reloader=False)
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Error starting server: {str(e)}")
            traceback.print_exc()
            
except Exception as global_exception:
    print(f"CRITICAL ERROR: {str(global_exception)}")
    traceback.print_exc()
    time.sleep(30)  # Keep the window open to see the error