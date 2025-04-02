"""
Model parallelism strategy implementation
"""
import logging
import torch
import math
from .base_strategy import DistributionStrategy

logger = logging.getLogger(__name__)

class ModelParallelismStrategy(DistributionStrategy):
    """
    Implements model parallelism by splitting model layers across devices.
    Each device processes different parts of the model.
    """
    
    def apply(self):
        """Apply model parallelism distribution strategy"""
        logger.info("Setting up model parallelism across devices")
        
        # Get all model modules that can be distributed
        all_layers = list(self.model.children())
        
        # Calculate split ratio based on device weights
        primary_ratio = self.device_config['main_weight']
        primary_layers_count = math.ceil(len(all_layers) * primary_ratio)
        
        # Distribute model components across devices
        for i, layer in enumerate(all_layers):
            # Place early layers on primary device, later layers on secondary
            target_device = self.primary_device if i < primary_layers_count else self.secondary_device
            
            # Some modules may not have a .to() method or parameters, so handle this safely
            try:
                layer.to(target_device)
                logger.debug(f"Layer {i} moved to {target_device}")
            except Exception as e:
                logger.warning(f"Failed to move layer {i} to {target_device}: {str(e)}")
        
        self.is_sharded = True
        logger.info(f"Model parallelism configured: {primary_layers_count} layers on {self.primary_device}, "
                   f"{len(all_layers) - primary_layers_count} layers on {self.secondary_device}")
                   
        return True
