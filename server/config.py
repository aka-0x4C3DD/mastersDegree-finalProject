"""
Server configuration module
"""
import os
import configparser
import logging

logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from environment variables and config files"""
    config = {
        'model_path': os.environ.get('MODEL_PATH', 'medicalai/ClinicalGPT-base-zh'),
        'port': int(os.environ.get('PORT', 5000)),
        'debug': os.environ.get('FLASK_DEBUG', 'False').lower() == 'true',
        'device_config': {
            'main_device': None,
            'secondary_device': None,
            'main_weight': 0.85,  # 85% of workload on primary device
            'secondary_weight': 0.15  # 15% of workload on secondary device
        }
    }
    
    logger.info(f"Loaded configuration: MODEL_PATH={config['model_path']}, PORT={config['port']}")
    return config
