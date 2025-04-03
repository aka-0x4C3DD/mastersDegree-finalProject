"""
File processing endpoints
"""
import logging
import traceback
from flask import request, jsonify
# Remove torch import if not directly used here
# import torch

logger = logging.getLogger(__name__)

# Keep model_manager in the signature
def register_file_routes(app, model_manager, device_config):
    """Register file processing endpoints"""

    @app.route('/api/process-file', methods=['POST'])
    def handle_file_upload():
        """Process an uploaded file and return the analysis."""
        try:
            if 'file' not in request.files:
                logger.warning("No file uploaded in request")
                return jsonify({'error': 'No file uploaded'}), 400

            file = request.files['file']
            if file.filename == '':
                logger.warning("Empty filename in uploaded file")
                return jsonify({'error': 'No file selected'}), 400

            try:
                logger.info(f"Processing file: {file.filename}")
                # Process the file based on its type
                from utils.file_processor.processor import process_file

                # Pass model_manager directly to process_file
                result = process_file(file, model_manager)
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error processing file: {str(e)}")
                traceback.print_exc()
                return jsonify({'error': str(e)}), 500
        except Exception as e:
            logger.error(f"Unexpected error in handle_file_upload: {str(e)}")
            traceback.print_exc()
            return jsonify({'error': 'Internal server error'}), 500
