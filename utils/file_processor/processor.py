"""
Core file processing module that dispatches to format-specific handlers.
"""
import os
import logging

logger = logging.getLogger(__name__)

def process_file(file, model, tokenizer, device):
    """Process different types of medical files
    
    Args:
        file: File object from Flask's request.files
        model: The loaded ClinicalGPT model
        tokenizer: The loaded tokenizer
        device: The device (CPU/GPU) to run inference on
    
    Returns:
        Dictionary with processed results
    """
    filename = file.filename
    file_ext = os.path.splitext(filename)[1].lower()
    
    try:
        # Import handlers here to avoid circular imports
        from .text_processor import process_text_file
        from .csv_processor import process_csv_file
        from .json_processor import process_json_file
        from .image_processor import process_image_file
        from .pdf_processor import process_pdf_file
        
        # Process file based on extension
        if file_ext == '.txt':
            return process_text_file(file, model, tokenizer, device)
        elif file_ext == '.csv':
            return process_csv_file(file, model, tokenizer, device)
        elif file_ext == '.json':
            return process_json_file(file, model, tokenizer, device)
        elif file_ext in ['.jpg', '.jpeg', '.png']:
            return process_image_file(file, model, tokenizer, device)
        elif file_ext == '.pdf':
            return process_pdf_file(file, model, tokenizer, device)
        else:
            return {"error": f"Unsupported file type: {file_ext}"}
    
    except Exception as e:
        logger.error(f"Error processing file {filename}: {str(e)}")
        return {"error": f"Error processing file: {str(e)}"}
