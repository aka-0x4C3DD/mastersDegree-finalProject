"""
ClinicalGPT Medical Assistant - File Processing Package
This package handles processing and analysis of various medical file formats.
"""
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import main functions for easy access
from .processor import process_file
from .medical_terms import detect_medical_terms

# Other modules are imported as needed by the processor
