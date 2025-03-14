from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import os
import json
import sys
import traceback
import logging
import time

# Configure logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define global variables
tokenizer = None
model = None
device = None

try:
    logger.info("Starting ClinicalGPT Medical Assistant server...")
    
    # Add the project root to the Python path to make imports work properly
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        logger.info(f"Added {project_root} to Python path")

    # Now import from utils
    try:
        from utils.web_scraper import search_medical_sites
        from utils.file_processor import process_file
        logger.info("Successfully imported utility modules")
    except ImportError as e:
        logger.error(f"ERROR importing utility modules: {str(e)}")
        traceback.print_exc()

    # Set up static folder path
    static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    logger.info(f"Static folder path: {static_folder}")

    app = Flask(__name__, static_folder=static_folder)
    CORS(app)  # Enable CORS for all routes

    # Load environment variables - Changed model to ClinicalGPT-base-zh
    MODEL_PATH = os.environ.get('MODEL_PATH', 'medicalai/ClinicalGPT-base-zh')
    logger.info(f"Using model: {MODEL_PATH}")

    # Initialize model and tokenizer
    try:
        logger.info(f"Loading model from {MODEL_PATH}")
        
        # Determine device
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {device}")
        
        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
        logger.info("Tokenizer loaded successfully")
        
        # Load model with more conservative memory settings and trust remote code
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH, 
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
        logger.info("Model loaded successfully")
        
        model.to(device)
        logger.info("Model moved to device successfully")
        
    except Exception as e:
        logger.error(f"ERROR loading model: {str(e)}")
        traceback.print_exc()
        # Continue with app definition but model might not work

    @app.route('/')
    def index():
        """Serve the main web interface"""
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/js/<path:filename>')
    def serve_js(filename):
        """Serve JavaScript files"""
        return send_from_directory(os.path.join(app.static_folder, 'js'), filename)

    @app.route('/css/<path:filename>')
    def serve_css(filename):
        """Serve CSS files"""
        return send_from_directory(os.path.join(app.static_folder, 'css'), filename)

    @app.route('/api/info', methods=['GET'])
    def api_info():
        """Home page with basic status info."""
        return jsonify({
            'status': 'running',
            'model': MODEL_PATH,
            'endpoints': {
                '/api/health': 'Health check',
                '/api/query': 'Process a medical query',
                '/api/process-file': 'Process a medical file'
            }
        })

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
            if model is None:
                logger.error("Model not loaded")
                return jsonify({'error': 'Model not loaded properly'}), 500
            
            # Process the query with ClinicalGPT
            try:
                # Format the prompt properly for the model
                prompt = f"User: {query}\nAssistant:"
                logger.debug(f"Using prompt: {prompt}")
                
                # Tokenize and prepare input
                inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=512)
                inputs = {key: val.to(device) for key, val in inputs.items()}
                
                logger.debug("Generating response...")
                # Generate response with the causal language model
                with torch.no_grad():
                    output = model.generate(
                        inputs["input_ids"],
                        max_length=1024,
                        do_sample=True,
                        top_p=0.9,
                        temperature=0.6,
                        num_return_sequences=1
                    )
                
                logger.debug("Decoding generated response...")
                # Decode the generated response
                generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
                
                # Extract just the response part (after "Assistant:")
                response_text = generated_text.split("Assistant:", 1)[-1].strip()
                logger.info(f"Generated response: {response_text[:50]}...")
                
                # If requested, search for additional context from trusted medical sites
                web_results = None
                if data.get('search_web', False):
                    logger.info("Searching web for additional context...")
                    search_term = data.get('search_term', query)
                    web_results = search_medical_sites(search_term)
                
                # Build response with updated model name
                response = {
                    'model_name': MODEL_PATH,
                    'response': response_text,
                    'web_results': web_results
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
                result = process_file(file, model, tokenizer, device)
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error processing file: {str(e)}")
                traceback.print_exc()
                return jsonify({'error': str(e)}), 500
        except Exception as e:
            logger.error(f"Unexpected error in handle_file_upload: {str(e)}")
            traceback.print_exc()
            return jsonify({'error': 'Internal server error'}), 500

    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Simple health check endpoint."""
        # Check if model is loaded
        model_status = "loaded" if model is not None else "not_loaded"
        return jsonify({'status': 'ok', 'model': MODEL_PATH, 'model_status': model_status})

    # Make sure app is defined at the module level for proper imports
    if __name__ == '__main__':
        try:
            logger.info(f"Starting server on http://localhost:{int(os.environ.get('PORT', 5000))}")
            port = int(os.environ.get('PORT', 5000))
            debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
            app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Error starting server: {str(e)}")
            traceback.print_exc()
            
except Exception as global_exception:
    print(f"CRITICAL ERROR: {str(global_exception)}")
    traceback.print_exc()
    time.sleep(30)  # Keep the window open to see the error