"""
Query processing endpoints
"""
import logging
import traceback
from flask import request, jsonify

logger = logging.getLogger(__name__)

def register_query_routes(app, model_manager, device_config):
    """Register query processing endpoints"""
    
    @app.route('/api/query', methods=['POST'])
    def process_query():
        """Process a text query using the ClinicalGPT model and return the response."""
        try:
            data = request.json
            
            if 'query' not in data:
                logger.warning("API request missing query field")
                return jsonify({'error': 'No query provided'}), 400
            
            query = data['query']
            logger.info(f"Processing query: {query[:50]}...")
            
            # Check if model is loaded
            if model_manager.model is None:
                logger.error("Model not loaded")
                return jsonify({'error': 'Model not loaded properly'}), 500
            
            # Process the query with ClinicalGPT
            try:
                # First check if we should search the web for information
                web_results = []
                if data.get('search_web', False):
                    logger.info("Searching web for medical information first...")
                    from utils.web_scraper.core import search_medical_sites
                    
                    search_term = data.get('search_term', query)
                    web_results = search_medical_sites(search_term, max_results=5)
                    logger.info(f"Found {len(web_results)} web results")
                    
                    # Create an enhanced prompt that includes web information
                    if web_results:
                        web_context = "\n\nInformation from trusted medical sources:\n"
                        for i, result in enumerate(web_results):
                            title = result.get('title', 'Medical Information')
                            content = result.get('content', '').strip()
                            source = result.get('source', 'trusted medical source')
                            
                            web_context += f"[Source {i+1}: {title} from {source}]\n{content}\n\n"
                        
                        # Create an enhanced prompt that instructs the model to use this information
                        prompt = f"User: {query}\n\nPlease use the following up-to-date information in your response:\n{web_context}\nAssistant:"
                    else:
                        # If no web results, use standard prompt
                        prompt = f"User: {query}\nAssistant:"
                else:
                    # Standard prompt without web search
                    prompt = f"User: {query}\nAssistant:"
                
                logger.debug(f"Using prompt with length: {len(prompt)}")
                
                response_text = model_manager.generate_response(prompt)
                
                # Build response with details
                response = {
                    'model_name': model_manager.model_path,
                    'response': response_text,
                    'web_results': web_results,
                    'device_used': device_config['main_device']
                }
                
                return jsonify(response)
            
            except Exception as e:
                logger.error(f"Error processing query: {str(e)}")
                traceback.print_exc()
                return jsonify({'error': str(e)}), 500
                
        except Exception as e:
            logger.error(f"Unexpected error in process_query: {str(e)}")
            traceback.print_exc()
            return jsonify({'error': 'Internal server error'}), 500
