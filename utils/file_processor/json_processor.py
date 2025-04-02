"""
Module for processing and analyzing JSON files.
"""
import json
import logging

# Internal imports
from .text_processor import process_text_chunk

logger = logging.getLogger(__name__)

def process_json_file(file, model, tokenizer, device):
    """Process a JSON file with medical data"""
    content = file.read().decode('utf-8')
    
    try:
        json_data = json.loads(content)
        
        # Convert JSON to a readable format for analysis
        if isinstance(json_data, dict):
            text_to_analyze = json.dumps(json_data, indent=2)
        elif isinstance(json_data, list) and len(json_data) > 0:
            # If it's a list, take a sample for analysis
            sample = json_data[:5] if len(json_data) > 5 else json_data
            text_to_analyze = json.dumps(sample, indent=2)
        else:
            text_to_analyze = content
        
        # Process the extracted text
        result = process_text_chunk(text_to_analyze, model, tokenizer, device)
        
        return {
            "file_type": "json",
            "structure": "array" if isinstance(json_data, list) else "object",
            "size": len(json_data) if isinstance(json_data, list) else len(json_data.keys()),
            "response": result.get("response", "No analysis available.")
        }
    
    except json.JSONDecodeError:
        return {
            "file_type": "json",
            "error": "Invalid JSON format",
            "response": "The uploaded file is not valid JSON. Please check the format."
        }
