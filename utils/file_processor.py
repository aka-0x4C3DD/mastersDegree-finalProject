"""
Legacy file processor module that now imports from the modular package structure.
This module is kept for backward compatibility.
"""
import logging
from utils.file_processor.processor import process_file
from utils.file_processor.medical_terms import detect_medical_terms

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Log a deprecation warning when this module is imported
logger.warning(
    "The monolithic file_processor.py is deprecated and will be removed in a future version. "
    "Please update your imports to use the new modular structure: "
    "from utils.file_processor import process_file, detect_medical_terms"
)

# Re-export the main functions for backward compatibility
__all__ = ['process_file', 'detect_medical_terms']