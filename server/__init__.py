"""
ClinicalGPT Medical Assistant - Server Package
This package manages the Flask server, model loading, and API endpoints.
"""
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server_debug.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)