"""
Medical term detection endpoints
"""
import logging
import traceback
from flask import request, jsonify

logger = logging.getLogger(__name__)

def register_term_routes(app):
    """Register medical term detection endpoints"""
    
    @app.route('/api/detect-medical-terms', methods=['POST'])
    def detect_medical_terms_endpoint():
        """API endpoint to detect medical terms in provided text."""
        try:
            data = request.json
            if 'text' not in data:
                return jsonify({'error': 'No text provided'}), 400
            
            text = data['text']
            
            # Import and use the advanced medical term detection function
            from utils.file_processor.medical_terms import detect_medical_terms
            
            # Process the text to find medical terms
            medical_terms = detect_medical_terms(text)
            
            return jsonify({
                'medical_terms': medical_terms
            })
            
        except Exception as e:
            logger.error(f"Error detecting medical terms: {str(e)}")
            traceback.print_exc()
            return jsonify({'error': 'Internal server error'}), 500
