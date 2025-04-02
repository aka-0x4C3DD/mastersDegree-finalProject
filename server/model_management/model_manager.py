"""
Main model manager that coordinates model loading and inference
"""
import gc
import logging
import torch

from .model_loader import ModelLoader
from .inference import InferenceEngine
from .distribution_strategies import get_strategy

logger = logging.getLogger(__name__)

class ModelManager:
    """Manages loading and inference with ClinicalGPT models"""
    
    def __init__(self, model_path, device_config):
        self.model_path = model_path
        self.device_config = device_config
        self.model = None
        self.tokenizer = None
        self.pipeline_stages = None
        self.is_sharded = False
        self.loader = ModelLoader(device_config)
        self.inference_engine = None
    
    def load_model(self):
        """Load model and tokenizer"""
        try:
            # Load model and tokenizer
            self.model, self.tokenizer = self.loader.load_model_and_tokenizer(self.model_path)
            
            # If main and secondary devices are different, set up hybrid execution
            if self.device_config['main_device'] != self.device_config['secondary_device']:
                strategy_applied = self._apply_distribution_strategy()
            else:
                # Standard single-device execution
                main_device = torch.device(self.device_config['main_device'])
                self.model.to(main_device)
                logger.info(f"Model moved to {self.device_config['main_device']} device successfully")
            
            # Initialize the inference engine
            self.inference_engine = InferenceEngine(self.model, self.tokenizer, self.device_config)
            
            # Run garbage collection to free memory
            self._cleanup_memory()
                
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False
    
    def _apply_distribution_strategy(self):
        """Choose and apply an appropriate distribution strategy based on model and hardware"""
        # Estimate model size to help determine strategy
        model_size_gb = self.loader.estimate_model_size_gb(self.model)
        logger.info(f"Estimated model size: {model_size_gb:.2f} GB")
        
        # Select distribution strategy based on model size and available hardware
        if self.device_config['main_device'] == 'cuda' and model_size_gb > 8:
            # For very large models, use model parallelism
            strategy = get_strategy('model_parallelism', self.model, self.device_config)
        elif self.device_config['main_device'] == 'cuda' and self.device_config['secondary_device'] == 'cpu':
            # For mixed GPU/CPU scenarios, use partial layer offloading
            strategy = get_strategy('layer_offloading', self.model, self.device_config)
        else:
            # For other scenarios, use pipeline parallelism
            strategy = get_strategy('pipeline_parallelism', self.model, self.device_config)

        # Apply the selected strategy
        success = strategy.apply()
        
        # Store strategy results
        self.is_sharded = strategy.is_model_sharded()
        self.pipeline_stages = strategy.get_pipeline_stages()
        
        return success
    
    def _cleanup_memory(self):
        """Clean up memory after model loading"""
        gc.collect()
        if self.device_config['main_device'] == 'cuda':
            torch.cuda.empty_cache()
    
    def generate_response(self, prompt):
        """Generate a response using the loaded model"""
        if not self.inference_engine:
            raise ValueError("Model not loaded or inference engine not initialized")
        
        return self.inference_engine.generate_response(prompt, self.pipeline_stages)
