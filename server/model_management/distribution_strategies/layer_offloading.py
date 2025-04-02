"""
Layer offloading strategy implementation
"""
import logging
import torch
from .base_strategy import DistributionStrategy

logger = logging.getLogger(__name__)

class LayerOffloadingStrategy(DistributionStrategy):
    """
    Implements partial layer offloading where attention layers stay on primary device
    but feed-forward networks (FFNs) are offloaded to secondary device.
    This can be effective since attention layers are more performance-critical.
    """
    
    def apply(self):
        """Apply layer offloading distribution strategy"""
        logger.info("Setting up partial layer offloading")
        
        try:
            # Move the entire model to the secondary device first
            self.model.to(self.secondary_device)
            
            # Then selectively move critical components back to the primary device
            offload_count = 0
            
            # For transformer models, keep attention layers on primary device
            for name, module in self.model.named_modules():
                # Keep attention mechanisms on the primary device for better performance
                if any(attention_part in name.lower() for attention_part in ['attn', 'attention', 'self']):
                    try:
                        module.to(self.primary_device)
                        offload_count += 1
                    except Exception as e:
                        logger.debug(f"Could not move module {name} to primary device: {str(e)}")
            
            # Also keep token embeddings on primary device for faster inference starts
            if hasattr(self.model, 'get_input_embeddings'):
                self.model.get_input_embeddings().to(self.primary_device)
                offload_count += 1
                
            # Keep LM head on primary device for faster final predictions
            if hasattr(self.model, 'get_output_embeddings') and self.model.get_output_embeddings() is not None:
                self.model.get_output_embeddings().to(self.primary_device)
                offload_count += 1
            
            logger.info(f"Partial layer offloading configured: {offload_count} critical modules on {self.primary_device}, "
                       f"rest of model on {self.secondary_device}")
            
            return offload_count > 0
        
        except Exception as e:
            logger.error(f"Failed to set up partial layer offloading: {str(e)}")
            # Fall back to moving the whole model to the primary device
            self.model.to(self.primary_device)
            return False
