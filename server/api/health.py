"""
Health and status check endpoints
"""
import logging
from flask import jsonify

logger = logging.getLogger(__name__)

def register_health_routes(app, model_manager, device_config):
    """Register health and status check endpoints"""
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Simple health check endpoint."""
        # Check if model is loaded
        model_status = "loaded" if model_manager.model is not None else "not_loaded"
        return jsonify({
            'status': 'ok', 
            'model': model_manager.model_path, 
            'model_status': model_status,
            'primary_device': device_config['main_device'],
            'secondary_device': device_config['secondary_device'],
        })
    
    @app.route('/api/info', methods=['GET'])
    def api_info():
        """Home page with basic status info."""
        return jsonify({
            'status': 'running',
            'model': model_manager.model_path,
            'primary_device': device_config['main_device'],
            'secondary_device': device_config['secondary_device'],
            'endpoints': {
                '/api/health': 'Health check',
                '/api/query': 'Process a medical query',
                '/api/process-file': 'Process a medical file',
                '/api/detect-medical-terms': 'Detect medical terms in text',
                '/api/device-info': 'Hardware acceleration details'
            }
        })
    
    @app.route('/api/device-info', methods=['GET'])
    def device_info():
        """Return detailed information about the devices being used."""
        from ..utils.device_detection import get_device_details
        
        info = {
            'primary_device': device_config['main_device'],
            'primary_device_weight': f"{device_config['main_weight']*100:.0f}%",
            'secondary_device': device_config['secondary_device'],
            'secondary_device_weight': f"{device_config['secondary_weight']*100:.0f}%",
            **get_device_details()
        }
        
        return jsonify(info)
