"""
Base class for model distribution strategies
"""
import logging
import torch

logger = logging.getLogger(__name__)

class DistributionStrategy:
    """Base class for model distribution strategies"""
    
    def __init__(self, model, device_config):
        self.model = model
        self.device_config = device_config
        self.primary_device = torch.device(device_config['main_device'])
        self.secondary_device = torch.device(device_config['secondary_device'])
        self.pipeline_stages = None
        self.is_sharded = False
        
    def apply(self):
        """Apply the distribution strategy to the model"""
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_pipeline_stages(self):
        """Return pipeline stages if applicable, otherwise None"""
        return self.pipeline_stages
        
    def is_model_sharded(self):
        """Return whether the model is sharded across devices"""
        return self.is_sharded
