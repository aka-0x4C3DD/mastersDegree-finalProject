"""
Model distribution strategies for different hardware configurations
"""
from .base_strategy import DistributionStrategy
from .model_parallelism import ModelParallelismStrategy
from .pipeline_parallelism import PipelineParallelismStrategy
from .layer_offloading import LayerOffloadingStrategy

def get_strategy(strategy_type, model, device_config):
    """Factory function to get the appropriate distribution strategy"""
    strategies = {
        'model_parallelism': ModelParallelismStrategy,
        'pipeline_parallelism': PipelineParallelismStrategy,
        'layer_offloading': LayerOffloadingStrategy
    }
    
    if strategy_type not in strategies:
        raise ValueError(f"Unknown strategy type: {strategy_type}")
        
    return strategies[strategy_type](model, device_config)

__all__ = [
    'DistributionStrategy',
    'ModelParallelismStrategy',
    'PipelineParallelismStrategy', 
    'LayerOffloadingStrategy',
    'get_strategy'
]
