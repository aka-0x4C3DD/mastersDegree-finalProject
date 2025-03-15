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
from utils.web_scraper import WebScraper

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

web_scraper = WebScraper()

try:
    logger.info("Starting ClinicalGPT Medical Assistant server...")

    # Add the project root to the Python path to make imports work properly
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        logger.info(f"Added {project_root} to Python path")

    # Import utility modules
    try:
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

except ImportError as e:
    logger.error(f"ERROR importing utility modules: {str(e)}")
    traceback.print_exc()

# Load environment variables
MODEL_PATH = os.environ.get('MODEL_PATH', 'HPAI-BSC/Llama3.1-Aloe-Beta-8B')
logger.info(f"Using model: {MODEL_PATH}")

try:
    # Initialize model and tokenizer
    logger.info(f"Loading model from {MODEL_PATH}")
    
    # Determine optimal device strategy
    has_npu = False
    
    # Check for CUDA GPU
    has_gpu = torch.cuda.is_available()
    if has_gpu:
        cuda_device_count = torch.cuda.device_count()
        cuda_device_name = torch.cuda.get_device_name(0)
        logger.info(f"CUDA is available. Device count: {cuda_device_count}")
        logger.info(f"CUDA Device: {cuda_device_name}")
    else:
        logger.info("CUDA is not available")

    # Check for Apple Silicon
    has_mps = hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
    if has_mps:
        logger.info("Apple Silicon MPS is available")

    # Check for Intel NPU
    use_npu = os.environ.get("USE_INTEL_NPU", "1").lower() in ["1", "true", "yes"]
    if use_npu:
            try:
                import intel_extension_for_pytorch as ipex  # type: ignore
                has_npu = True
                logger.info("Intel NPU detected and enabled")
            except ImportError:
                logger.warning("Intel NPU extensions not found. Install with 'pip install intel-extension-for-pytorch' to use.")
                has_npu = False

    # Set device configurations
    if has_npu:
        device_config['main_device'] = 'npu'
        device_config['secondary_device'] = 'cuda' if has_gpu else 'cpu'
        logger.info(f"Using NPU (85%) and {device_config['secondary_device']} (15%)")
    elif has_gpu:
        device_config['main_device'] = 'cuda'
        device_config['secondary_device'] = 'cpu'
        logger.info(f"Using GPU (85%) and CPU (15%)")
    elif has_mps:
        device_config['main_device'] = 'mps'
        device_config['secondary_device'] = 'cpu'
        logger.info(f"Using Apple Silicon GPU (85%) and CPU (15%)")
    else:
        device_config['main_device'] = 'cpu'
        device_config['secondary_device'] = 'cpu'
        logger.info("Using CPU only")

    # Create device instances
    main_device = torch.device(device_config['main_device'])
    secondary_device = torch.device(device_config['secondary_device'])

    # Log hardware details
    if has_gpu:
        props = torch.cuda.get_device_properties(0)
        logger.info(f"CUDA Memory: {props.total_memory / 1e9:.2f} GB")
        logger.info(f"CUDA Compute Capability: {props.major}.{props.minor}")

    # Disable HF symlink warnings
    os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    logger.info("Tokenizer loaded successfully")

    # Determine precision
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
    logger.info(f"Model moved to {device_config['main_device']} successfully")

    # Garbage collection
    gc.collect()
    if has_gpu:
        torch.cuda.empty_cache()

except Exception as e:
    logger.error(f"Model initialization failed: {str(e)}", exc_info=True)

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

        # Fetch medical info from trusted domains
        web_results = []
        if data.get('search_web', False):
            search_term = data.get('search_term', query)
            # Use web scraper to search all trusted domains
            search_results = web_scraper.search_medical_sites(query)
            for result in search_results[:3]:
                web_results.append({
                    "source": result['source'],
                    "content": result['content']
                })

        # Generate response using the model
        inputs = tokenizer(query, return_tensors="pt").to(main_device)
        with torch.no_grad():
            outputs = model.generate(
                inputs["input_ids"],
                max_length=512,
                do_sample=True,
                top_p=0.9,
                temperature=0.6
            )
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract response part after user prompt
        response_text = generated_text.split("Assistant:", 1)[-1].strip()

        response = {
            'model_name': MODEL_PATH,
            'response': response_text,
            'web_results': web_results,
            'device_used': device_config['main_device']
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# ... [remaining routes and code remain unchanged] ...

if __name__ == '__main__':
    # Existing server startup code
    logger.info(f"Starting server on http://localhost:{int(os.environ.get('PORT', 5000))}")
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
