"""
Handles loading models and tokenizers from various sources
"""
import os
import logging
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

logger = logging.getLogger(__name__)

class ModelLoader:
    """Responsible for loading models and tokenizers from various sources"""
    
    def __init__(self, device_config):
        self.device_config = device_config
        # Disable HF warning about symlinks
        os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
        
    def load_model_and_tokenizer(self, model_path):
        """Load model and tokenizer from specified path"""
        try:
            logger.info(f"Loading model from {model_path}")
            
            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
            logger.info("Tokenizer loaded successfully")
            
            # Configure precision based on hardware
            model_dtype = torch.float16 if self.device_config['main_device'] == 'cuda' else torch.float32
            logger.info(f"Using model precision: {model_dtype}")
            
            # Load model with optimized settings
            model = AutoModelForCausalLM.from_pretrained(
                model_path, 
                trust_remote_code=True,
                low_cpu_mem_usage=True,
                torch_dtype=model_dtype
            )
            logger.info("Model loaded successfully")
            
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
            
    def estimate_model_size_gb(self, model):
        """Estimate model size in GB based on parameter count"""
        param_count = sum(p.numel() for p in model.parameters())
        # Each parameter is typically stored as float32 (4 bytes) or float16 (2 bytes)
        bytes_per_param = 2 if self.device_config['main_device'] == 'cuda' else 4
        model_size_gb = (param_count * bytes_per_param) / (1024**3)
        return model_size_gb
