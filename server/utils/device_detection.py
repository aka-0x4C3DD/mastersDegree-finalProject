"""
Hardware device detection and configuration
"""
import os
import logging
import torch

logger = logging.getLogger(__name__)

def detect_devices():
    """Detect and configure optimal devices for model inference"""
    device_config = {
        'main_device': None,
        'secondary_device': None,
        'main_weight': 0.85,
        'secondary_weight': 0.15
    }
    
    has_intel_npu = False
    has_amd_npu = False
    has_gpu = False
    has_mps = False
    
    # Check for CUDA GPU
    try:
        has_gpu = torch.cuda.is_available()
        if has_gpu:
            cuda_device_count = torch.cuda.device_count()
            cuda_device_name = torch.cuda.get_device_name(0)
            logger.info(f"CUDA is available. Device count: {cuda_device_count}")
            logger.info(f"CUDA Device: {cuda_device_name}")
        else:
            logger.info("CUDA is not available")
    except Exception as e:
        logger.error(f"Error checking CUDA availability: {str(e)}")
        has_gpu = False
    
    # Check for Apple Silicon
    try:
        has_mps = hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
        if has_mps:
            logger.info("Apple Silicon MPS is available")
    except Exception as e:
        logger.error(f"Error checking MPS availability: {str(e)}")
        has_mps = False
    
    # Check for Intel NPU
    try:
        # Only try to import if the environment var is explicitly set
        if os.environ.get("USE_INTEL_NPU", "0").lower() in ["1", "true", "yes"]:
            import intel_extension_for_pytorch as ipex
            has_intel_npu = True
            logger.info("Intel NPU detected and enabled")
        else:
            logger.info("Intel NPU detection skipped - set USE_INTEL_NPU=1 to enable")
    except ImportError:
        logger.info("Intel NPU extensions not available")
        has_intel_npu = False
    except Exception as e:
        logger.error(f"Error checking Intel NPU: {str(e)}")
        has_intel_npu = False
    
    # Check for AMD NPU (ROCm platform)
    try:
        if os.environ.get("USE_AMD_NPU", "0").lower() in ["1", "true", "yes"]:
            # Check if PyTorch was built with ROCm support
            has_hip = hasattr(torch, 'hip') and torch.hip.is_available()
            if has_hip:
                has_amd_npu = True
                logger.info("AMD NPU (ROCm) detected and enabled")
            else:
                logger.info("AMD NPU requested but PyTorch ROCm support not available")
        else:
            logger.info("AMD NPU detection skipped - set USE_AMD_NPU=1 to enable")
    except Exception as e:
        logger.error(f"Error checking AMD NPU: {str(e)}")
        has_amd_npu = False
    
    # Set device configurations based on availability
    # Priority: Intel NPU > AMD NPU > CUDA GPU > Apple Silicon > CPU
    if has_intel_npu:
        if has_gpu:
            # Use both Intel NPU (primary) and GPU (secondary)
            device_config['main_device'] = 'npu'
            device_config['secondary_device'] = 'cuda'
            logger.info(f"Using Intel NPU (85%) and GPU (15%) for inference")
        else:
            # Use Intel NPU only
            device_config['main_device'] = 'npu'
            device_config['secondary_device'] = 'cpu'
            logger.info(f"Using Intel NPU (85%) and CPU (15%) for inference")
    elif has_amd_npu:
        if has_gpu:
            # Use both AMD NPU (primary) and GPU (secondary)
            device_config['main_device'] = 'hip'
            device_config['secondary_device'] = 'cuda'
            logger.info(f"Using AMD NPU (85%) and GPU (15%) for inference")
        else:
            # Use AMD NPU only
            device_config['main_device'] = 'hip'
            device_config['secondary_device'] = 'cpu'
            logger.info(f"Using AMD NPU (85%) and CPU (15%) for inference")
    elif has_gpu:
        # Use GPU (primary) and CPU (secondary)
        device_config['main_device'] = 'cuda'
        device_config['secondary_device'] = 'cpu'
        logger.info(f"Using GPU (85%) and CPU (15%) for inference")
    elif has_mps:
        # Use Apple Silicon GPU
        device_config['main_device'] = 'mps'
        device_config['secondary_device'] = 'cpu'
        logger.info(f"Using Apple Silicon GPU (85%) and CPU (15%) for inference")
    else:
        # Use CPU only
        device_config['main_device'] = 'cpu'
        device_config['secondary_device'] = 'cpu'
        logger.info(f"Using CPU (100%) for inference - no accelerators available")
    
    return device_config

def get_device_details():
    """Get detailed information about available devices"""
    details = {}
    
    try:
        if torch.cuda.is_available():
            details['cuda_version'] = torch.version.cuda
            details['cuda_device_count'] = torch.cuda.device_count()
            details['cuda_device_name'] = torch.cuda.get_device_name(0)
            props = torch.cuda.get_device_properties(0)
            details['cuda_compute_capability'] = f"{props.major}.{props.minor}"
            details['cuda_total_memory'] = f"{props.total_memory / (1024**3):.2f} GB"
    except Exception as e:
        logger.error(f"Error getting CUDA details: {str(e)}")
    
    # Add similar sections for other device types if needed
    
    return details
