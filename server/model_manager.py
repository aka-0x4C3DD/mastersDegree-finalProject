"""
Model loading and management
"""
import os
import gc
import logging
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import Dict, List, Optional, Tuple
import math

logger = logging.getLogger(__name__)

class ModelManager:
    """Manages loading and inference with ClinicalGPT models"""
    
    def __init__(self, model_path, device_config):
        self.model_path = model_path
        self.device_config = device_config
        self.model = None
        self.tokenizer = None
        self.pipeline_stages = None  # For pipeline parallelism
        self.is_sharded = False  # For model parallelism
        
        # Disable HF warning about symlinks
        os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
    
    def load_model(self):
        """Load model and tokenizer"""
        try:
            logger.info(f"Loading model from {self.model_path}")
            
            # Create device instances
            main_device = torch.device(self.device_config['main_device'])
            secondary_device = torch.device(self.device_config['secondary_device'])
            
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
            
            # If main and secondary devices are different, set up hybrid execution
            if self.device_config['main_device'] != self.device_config['secondary_device']:
                # Choose an advanced distribution approach based on model size and available memory
                model_size_gb = self._estimate_model_size_gb()
                logger.info(f"Estimated model size: {model_size_gb:.2f} GB")
                
                # Select distribution strategy based on model size and available hardware
                if self.device_config['main_device'] == 'cuda' and model_size_gb > 8:
                    # For very large models, use model parallelism
                    self.setup_model_parallelism(main_device, secondary_device)
                elif self.device_config['main_device'] == 'cuda' and self.device_config['secondary_device'] == 'cpu':
                    # For mixed GPU/CPU scenarios, use partial layer offloading
                    self.setup_partial_layer_offloading(main_device, secondary_device)
                else:
                    # For other scenarios, use pipeline parallelism
                    self.setup_pipeline_parallelism(main_device, secondary_device)
            else:
                # Standard single-device execution
                self.model.to(main_device)
                logger.info(f"Model moved to {self.device_config['main_device']} device successfully")
            
            # Run garbage collection to free memory
            gc.collect()
            if self.device_config['main_device'] == 'cuda':
                torch.cuda.empty_cache()
                
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False
            
    def _estimate_model_size_gb(self) -> float:
        """Estimate model size in GB based on parameter count"""
        param_count = sum(p.numel() for p in self.model.parameters())
        # Each parameter is typically stored as float32 (4 bytes)
        # For float16, it would be 2 bytes per parameter
        bytes_per_param = 2 if self.device_config['main_device'] == 'cuda' else 4
        model_size_gb = (param_count * bytes_per_param) / (1024**3)
        return model_size_gb
    
    def setup_model_parallelism(self, primary_device: torch.device, secondary_device: torch.device):
        """
        Implement model parallelism by splitting model layers across devices.
        Each device processes different parts of the model.
        """
        logger.info("Setting up model parallelism across devices")
        
        # Get all model modules that can be distributed
        all_layers = list(self.model.children())
        
        # Calculate split ratio based on device weights
        primary_ratio = self.device_config['main_weight']
        primary_layers_count = math.ceil(len(all_layers) * primary_ratio)
        
        # Distribute model components across devices
        for i, layer in enumerate(all_layers):
            # Place early layers on primary device, later layers on secondary
            target_device = primary_device if i < primary_layers_count else secondary_device
            
            # Some modules may not have a .to() method or parameters, so handle this safely
            try:
                layer.to(target_device)
                logger.debug(f"Layer {i} moved to {target_device}")
            except Exception as e:
                logger.warning(f"Failed to move layer {i} to {target_device}: {str(e)}")
        
        self.is_sharded = True
        logger.info(f"Model parallelism configured: {primary_layers_count} layers on {primary_device}, "
                   f"{len(all_layers) - primary_layers_count} layers on {secondary_device}")
    
    def setup_pipeline_parallelism(self, primary_device: torch.device, secondary_device: torch.device):
        """
        Implement pipeline parallelism by creating a 2-stage pipeline.
        Different batches of data are processed on different devices simultaneously.
        """
        logger.info("Setting up pipeline parallelism across devices")
        
        # For transformers model, we split the model at encoder/decoder level
        # or for decoder-only models, we split the decoder stack
        try:
            # Find a natural split point in the model
            # For decoder-only models like GPT, we can split the decoder stack
            if hasattr(self.model, 'transformer'):
                # GPT-style model
                decoder_layers = self.model.transformer.h  # This is the list of decoder blocks
                split_point = math.ceil(len(decoder_layers) * self.device_config['main_weight'])
                
                # Create two stages
                self.pipeline_stages = {
                    'embeddings': self.model.transformer.wte.to(primary_device),
                    'pos_embeddings': self.model.transformer.wpe.to(primary_device),
                    'early_layers': decoder_layers[:split_point].to(primary_device),
                    'late_layers': decoder_layers[split_point:].to(secondary_device),
                    'output_head': self.model.transformer.ln_f.to(secondary_device)
                }
                
                logger.info(f"Pipeline parallelism configured with split at layer {split_point} of {len(decoder_layers)}")
            
            else:
                # More generic approach for other models
                # Fall back to putting the whole model on the primary device
                self.model.to(primary_device)
                logger.warning("Pipeline parallelism not optimal for this model architecture; using primary device only")
                self.pipeline_stages = None
        
        except Exception as e:
            logger.error(f"Failed to set up pipeline parallelism: {str(e)}")
            # Fall back to moving the whole model to the primary device
            self.model.to(primary_device)
            self.pipeline_stages = None
    
    def setup_partial_layer_offloading(self, primary_device: torch.device, secondary_device: torch.device):
        """
        Implement partial layer offloading where attention layers stay on primary device
        but feed-forward networks (FFNs) are offloaded to secondary device.
        This can be effective since attention layers are more performance-critical.
        """
        logger.info("Setting up partial layer offloading")
        
        try:
            # Move the entire model to the secondary device first
            self.model.to(secondary_device)
            
            # Then selectively move critical components back to the primary device
            offload_count = 0
            
            # For transformer models, keep attention layers on primary device
            for name, module in self.model.named_modules():
                # Keep attention mechanisms on the primary device for better performance
                if any(attention_part in name.lower() for attention_part in ['attn', 'attention', 'self']):
                    try:
                        module.to(primary_device)
                        offload_count += 1
                    except Exception as e:
                        logger.debug(f"Could not move module {name} to primary device: {str(e)}")
            
            # Also keep token embeddings on primary device for faster inference starts
            if hasattr(self.model, 'get_input_embeddings'):
                self.model.get_input_embeddings().to(primary_device)
                offload_count += 1
                
            # Keep LM head on primary device for faster final predictions
            if hasattr(self.model, 'get_output_embeddings') and self.model.get_output_embeddings() is not None:
                self.model.get_output_embeddings().to(primary_device)
                offload_count += 1
            
            logger.info(f"Partial layer offloading configured: {offload_count} critical modules on {primary_device}, "
                       f"rest of model on {secondary_device}")
        
        except Exception as e:
            logger.error(f"Failed to set up partial layer offloading: {str(e)}")
            # Fall back to moving the whole model to the primary device
            self.model.to(primary_device)
    
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
                # If we're using pipeline parallelism, handle it differently
                if self.pipeline_stages is not None:
                    # Custom forward pass through pipeline stages
                    output = self._pipeline_generate(inputs["input_ids"])
                else:
                    # Standard generation
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
    
    def _pipeline_generate(self, input_ids):
        """Custom generation logic for pipeline parallelism"""
        # This is a simplified implementation; a production version would need more sophisticated logic
        try:
            # We'll implement a simple auto-regressive generation
            current_ids = input_ids.clone()
            max_length = 1024
            
            while current_ids.size(1) < max_length:
                # Process through pipeline stages
                embeddings = self.pipeline_stages['embeddings'](current_ids)
                if 'pos_embeddings' in self.pipeline_stages:
                    position_ids = torch.arange(0, current_ids.size(1), dtype=torch.long,
                                             device=current_ids.device)
                    position_embeddings = self.pipeline_stages['pos_embeddings'](position_ids)
                    hidden_states = embeddings + position_embeddings
                else:
                    hidden_states = embeddings
                
                # Process through early layers on primary device
                hidden_states = self.pipeline_stages['early_layers'](hidden_states)
                
                # Transfer to secondary device for late layers
                hidden_states = hidden_states.to(self.pipeline_stages['late_layers'].device)
                hidden_states = self.pipeline_stages['late_layers'](hidden_states)
                
                # Final output processing
                hidden_states = self.pipeline_stages['output_head'](hidden_states)
                
                # Get the next token prediction
                next_token_logits = self.model.lm_head(hidden_states[:, -1, :])
                next_token = next_token_logits.argmax(dim=-1).unsqueeze(-1)
                
                # Append to the sequence
                current_ids = torch.cat([current_ids, next_token], dim=-1)
                
                # Stop if end of sequence token is generated
                if next_token.item() == self.tokenizer.eos_token_id:
                    break
                    
            return current_ids
            
        except Exception as e:
            logger.error(f"Pipeline generation failed: {str(e)}")
            # Fall back to standard generation on the main device
            logger.warning("Falling back to standard generation")
            self.model.to(self.device_config['main_device'])
            return self.model.generate(
                input_ids,
                max_length=1024,
                do_sample=True,
                top_p=0.9,
                temperature=0.6,
                num_return_sequences=1
            )
