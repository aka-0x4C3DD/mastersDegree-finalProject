"""
Medical term detection endpoints
"""
import logging
import traceback
from flask import request, jsonify

logger = logging.getLogger(__name__)

# Modify function signature to accept model_manager
def register_term_routes(app, model_manager):
    """Register medical term detection endpoints"""

    @app.route('/api/detect-medical-terms', methods=['POST'])
    def detect_medical_terms_endpoint():
        """API endpoint to detect medical terms in provided text using LLM."""
        try:
            data = request.json
            if 'text' not in data:
                return jsonify({'error': 'No text provided'}), 400

            text = data['text']

            # Import the LLM-based medical term detection function
            from utils.file_processor.medical_terms import detect_medical_terms

            # Process the text to find medical terms, passing model_manager
            medical_terms = detect_medical_terms(text, model_manager)

            return jsonify({
                # The result is now a list of strings
                'medical_terms': medical_terms
            })

        except Exception as e:
            logger.error(f"Error detecting medical terms: {str(e)}")
            traceback.print_exc()
            return jsonify({'error': 'Internal server error'}), 500
