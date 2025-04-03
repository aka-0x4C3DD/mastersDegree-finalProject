"""
Query processing endpoints
"""
import logging
from flask import Blueprint, request, jsonify
from server.model_management import ModelManager
from utils.web_scraper import search_medical_sites # Use the refactored web scraper entry point
# Import the LLM-based keyword extraction function
from utils.file_processor.medical_terms import extract_search_keywords

logger = logging.getLogger(__name__)
query_bp = Blueprint('query', __name__)

# Keep model_manager in the signature
def register_query_routes(app, model_manager: ModelManager, device_config):
    """Registers query-related API routes."""

    @query_bp.route('/query', methods=['POST'])
    def handle_query():
        """Handles user queries, optionally searches web, and generates response."""
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Missing query in request"}), 400

        user_query = data['query']
        search_web = data.get('search_web', False) # Default to False if not provided
        
        logger.info(f"Received query: '{user_query[:100]}...', Search web: {search_web}")

        web_results = []
        search_context = ""
        
        if search_web:
            try:
                # --- Keyword Extraction Step using LLM ---
                # Pass model_manager to the keyword extraction function
                search_keywords = extract_search_keywords(user_query, model_manager)
                if not search_keywords:
                    logger.warning("No keywords extracted via LLM, falling back to original query for web search.")
                    search_term = user_query
                else:
                    search_term = search_keywords
                # --- End Keyword Extraction ---

                logger.info(f"Performing web search with term: '{search_term}'")
                # Use the extracted keywords (or original query as fallback) for the search
                web_results = search_medical_sites(search_term, max_results=3) 
                
                if web_results:
                    # Prepare context for the LLM prompt
                    search_context = "\n\nRelevant information from trusted sources:\n"
                    for i, result in enumerate(web_results):
                        search_context += f"\nSource {i+1}: {result.get('source', 'N/A')}\n"
                        search_context += f"Title: {result.get('title', 'N/A')}\n"
                        search_context += f"Content: {result.get('content', 'N/A')}\n"
                    search_context += "\n---\n"
                    logger.info(f"Added context from {len(web_results)} web results.")
                else:
                    logger.info("Web search returned no results.")
                    
            except Exception as e:
                logger.error(f"Error during web search: {str(e)}", exc_info=True)
                # Optionally inform the user or just proceed without web context
                search_context = "\n\n[Web search encountered an error and could not retrieve information.]\n"


        # Construct the prompt for the LLM
        # Use the ORIGINAL user query + context from KEYWORD search
        prompt = f"User Query: {user_query}{search_context}\nBased on the above query and potentially relevant information, please provide a comprehensive and helpful medical assistant response. If web information was provided, synthesize it with your knowledge but prioritize accuracy and safety. State if information comes from external sources."
        
        logger.debug(f"Constructed prompt for LLM (first 200 chars): {prompt[:200]}...")

        try:
            # Generate response using the model manager
            model_response = model_manager.generate_response(prompt)
            
            # Prepare final response structure
            response_data = {
                "query": user_query,
                "response": model_response,
                "web_results": web_results # Include web results for display
            }
            
            logger.info("Successfully generated response.")
            return jsonify(response_data), 200

        except Exception as e:
            logger.error(f"Error generating model response: {str(e)}", exc_info=True)
            return jsonify({"error": "Failed to generate response from model"}), 500

    app.register_blueprint(query_bp, url_prefix='/api')
