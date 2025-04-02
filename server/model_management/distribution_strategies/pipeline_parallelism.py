"""
Pipeline parallelism strategy implementation
"""
import logging
import torch
import math
from .base_strategy import DistributionStrategy

logger = logging.getLogger(__name__)

class PipelineParallelismStrategy(DistributionStrategy):
    """
    Implements pipeline parallelism by creating a 2-stage pipeline.
    Different batches of data are processed on different devices simultaneously.
    """
    
    def apply(self):
        """Apply pipeline parallelism distribution strategy"""
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
                    'embeddings': self.model.transformer.wte.to(self.primary_device),
                    'pos_embeddings': self.model.transformer.wpe.to(self.primary_device),
                    'early_layers': decoder_layers[:split_point].to(self.primary_device),
                    'late_layers': decoder_layers[split_point:].to(self.secondary_device),
                    'output_head': self.model.transformer.ln_f.to(self.secondary_device)
                }
                
                logger.info(f"Pipeline parallelism configured with split at layer {split_point} of {len(decoder_layers)}")
                return True
            
            else:
                # More generic approach for other models
                # Fall back to putting the whole model on the primary device
                self.model.to(self.primary_device)
                logger.warning("Pipeline parallelism not optimal for this model architecture; using primary device only")
                return False
        
        except Exception as e:
            logger.error(f"Failed to set up pipeline parallelism: {str(e)}")
            # Fall back to moving the whole model to the primary device
            self.model.to(self.primary_device)
            return False
