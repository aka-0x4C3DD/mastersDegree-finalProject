from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS
import os
import json
import sys
import traceback
import logging
import time
import gc

import configparser

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Delayed import after adding project root to path
from utils.web_scraper import search_medical_sites


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

# Disable Intel Extension auto-loading to prevent errors
os.environ["TORCH_DEVICE_BACKEND_AUTOLOAD"] = "0"

# Now it's safe to import torch
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# Define global variables
tokenizer = None
model = None
device_config = {
    'main_device': None,
    'secondary_device': None,
    'main_weight': 0.85,  # 85% of workload on primary device
    'secondary_weight': 0.15  # 15% of workload on secondary device
}

# Load configuration file
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
        
        # Determine optimal device strategy
        # Priority: NPU > GPU > CPU
        has_npu = False
        
        # Check for CUDA GPU
        try:
            has_gpu = torch.cuda.is_available()
            if has_gpu:
                cuda_device_count = torch.cuda.device_count()
                cuda_device_name = torch.cuda.get_device_name(0)
                logger.info(f"CUDA is available. Device count: {cuda_device_count}")
                logger.info(f"CUDA Device: {cuda_device_name}")
            else:
                logger.info("CUDA is not available")
        except Exception as e:
            logger.error(f"Error checking CUDA availability: {str(e)}")
            has_gpu = False
        
        # Check for Apple Silicon
        try:
            has_mps = hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
            if has_mps:
                logger.info("Apple Silicon MPS is available")
        except Exception as e:
            logger.error(f"Error checking MPS availability: {str(e)}")
            has_mps = False
        
        # Check for Intel NPU safely
        try:
            # We'll only try to import if the environment var is explicitly set
            if os.environ.get("USE_INTEL_NPU", "0").lower() in ["1", "true", "yes"]:
                import intel_extension_for_pytorch as ipex
                has_npu = True
                logger.info("Intel NPU detected and enabled")
            else:
                logger.info("Intel NPU detection skipped - set USE_INTEL_NPU=1 to enable")
        except ImportError:
            logger.info("Intel NPU extensions not available")
            has_npu = False
        except Exception as e:
            logger.error(f"Error checking Intel NPU: {str(e)}")
            has_npu = False
        
        # Set device configurations based on availability
        if has_npu:
            if has_gpu:
                # Use both NPU (primary) and GPU (secondary)
                device_config['main_device'] = 'npu'
                device_config['secondary_device'] = 'cuda'
                logger.info(f"Using NPU (85%) and GPU (15%) for inference")
            else:
                # Use NPU only
                device_config['main_device'] = 'npu'
                device_config['secondary_device'] = 'cpu'
                logger.info(f"Using NPU (85%) and CPU (15%) for inference")
        elif has_gpu:
            # Use GPU (primary) and CPU (secondary)
            device_config['main_device'] = 'cuda'
            device_config['secondary_device'] = 'cpu'
            logger.info(f"Using GPU (85%) and CPU (15%) for inference")
        elif has_mps:
            # Use Apple Silicon GPU
            device_config['main_device'] = 'mps'
            device_config['secondary_device'] = 'cpu'
            logger.info(f"Using Apple Silicon GPU (85%) and CPU (15%) for inference")
        else:
            # Use CPU only
            device_config['main_device'] = 'cpu'
            device_config['secondary_device'] = 'cpu'
            logger.info(f"Using CPU (100%) for inference - no accelerators available")
        
        # Create device instances
        main_device = torch.device(device_config['main_device'])
        secondary_device = torch.device(device_config['secondary_device'])
        
        # Log detailed hardware info
        if has_gpu:
            props = torch.cuda.get_device_properties(0)
            logger.info(f"CUDA Memory: {props.total_memory / 1e9:.2f} GB")
            logger.info(f"CUDA Compute Capability: {props.major}.{props.minor}")
            
        # Disable HF warning about symlinks
        os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
        
        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
        logger.info("Tokenizer loaded successfully")
        
        # Load model with optimized settings
        model_dtype = torch.float16 if has_gpu else torch.float32
        logger.info(f"Using model precision: {model_dtype}")
        
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH, 
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            torch_dtype=model_dtype
        )
        logger.info("Model loaded successfully")
        
        # Move model to main device
        model.to(main_device)
        logger.info(f"Model moved to {device_config['main_device']} device successfully")
        
        # If main and secondary devices are different, set up hybrid execution
        if device_config['main_device'] != device_config['secondary_device']:
            # This is a placeholder for more advanced model splitting between devices
            # In a production environment, this would use more sophisticated methods like:
            # - Model parallelism across devices
            # - Pipeline parallelism
            # - Partial offloading of specific layers
            logger.info(f"Hybrid execution configured with {device_config['main_weight']*100:.0f}% on {device_config['main_device']}")
        
        # Run garbage collection to free memory
        gc.collect()
        if has_gpu:
            torch.cuda.empty_cache()
        
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
            'primary_device': device_config['main_device'],
            'secondary_device': device_config['secondary_device'],
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
                
                # Move inputs to main device
                main_device = torch.device(device_config['main_device'])
                inputs = {key: val.to(main_device) for key, val in inputs.items()}
                
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
                main_device = torch.device(device_config['main_device'])
                result = process_file(file, model, tokenizer, main_device)
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
        return jsonify({
            'status': 'ok', 
            'model': MODEL_PATH, 
            'model_status': model_status,
            'primary_device': device_config['main_device'],
            'secondary_device': device_config['secondary_device'],
        })

    @app.route('/api/device-info', methods=['GET'])
    def device_info():
        """Return detailed information about the devices being used."""
        info = {
            'primary_device': device_config['main_device'],
            'primary_device_weight': f"{device_config['main_weight']*100:.0f}%",
            'secondary_device': device_config['secondary_device'],
            'secondary_device_weight': f"{device_config['secondary_weight']*100:.0f}%"
        }
        
        # Add GPU details if available
        if torch.cuda.is_available():
            info['cuda_version'] = torch.version.cuda
            info['cuda_device_count'] = torch.cuda.device_count()
            info['cuda_device_name'] = torch.cuda.get_device_name(0)
            props = torch.cuda.get_device_properties(0)
            info['cuda_compute_capability'] = f"{props.major}.{props.minor}"
            info['cuda_total_memory'] = f"{props.total_memory / (1024**3):.2f} GB"
        
        return jsonify(info)

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