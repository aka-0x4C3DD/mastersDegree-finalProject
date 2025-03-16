"""
Model loading and management
"""
import os
import gc
import logging
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

logger = logging.getLogger(__name__)

class ModelManager:
    """Manages loading and inference with ClinicalGPT models"""
    
    def __init__(self, model_path, device_config):
        self.model_path = model_path
        self.device_config = device_config
        self.model = None
        self.tokenizer = None
        
        # Disable HF warning about symlinks
        os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
    
    def load_model(self):
        """Load model and tokenizer"""
        try:
            logger.info(f"Loading model from {self.model_path}")
            
            # Create device instances
            main_device = torch.device(self.device_config['main_device'])
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)
            logger.info("Tokenizer loaded successfully")
            
            # Load model with optimized settings
            model_dtype = torch.float16 if self.device_config['main_device'] == 'cuda' else torch.float32
            logger.info(f"Using model precision: {model_dtype}")
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path, 
                trust_remote_code=True,
                low_cpu_mem_usage=True,
                torch_dtype=model_dtype
            )
            logger.info("Model loaded successfully")
            
            # Move model to main device
            self.model.to(main_device)
            logger.info(f"Model moved to {self.device_config['main_device']} device successfully")
            
            # If main and secondary devices are different, set up hybrid execution
            if self.device_config['main_device'] != self.device_config['secondary_device']:
                # This is a placeholder for more advanced model splitting between devices
                # In a production environment, this would use more sophisticated methods like:
                # - Model parallelism across devices
                # - Pipeline parallelism
                # - Partial offloading of specific layers
                logger.info(f"Hybrid execution configured with {self.device_config['main_weight']*100:.0f}% on {self.device_config['main_device']}")
            
            # Run garbage collection to free memory
            gc.collect()
            if self.device_config['main_device'] == 'cuda':
                torch.cuda.empty_cache()
                
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False
    
    def generate_response(self, prompt):
        """Generate a response from the model"""
        try:
            if self.model is None or self.tokenizer is None:
                raise ValueError("Model or tokenizer not loaded")
            
            # Tokenize and prepare input
            inputs = self.tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=1024)
            
            # Move inputs to main device
            main_device = torch.device(self.device_config['main_device'])
            inputs = {key: val.to(main_device) for key, val in inputs.items()}
            
            logger.debug("Generating response...")
            # Generate response with the causal language model
            with torch.no_grad():
                output = self.model.generate(
                    inputs["input_ids"],
                    max_length=1024,
                    do_sample=True,
                    top_p=0.9,
                    temperature=0.6,
                    num_return_sequences=1
                )
            
            logger.debug("Decoding generated response...")
            # Decode the generated response
            generated_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
            
            # Extract just the response part (after "Assistant:")
            response_text = generated_text.split("Assistant:", 1)[-1].strip()
            logger.info(f"Generated response: {response_text[:50]}...")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
