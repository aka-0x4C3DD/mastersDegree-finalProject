@echo off
echo ===================================================
echo ClinicalGPT Medical Assistant - Web Interface
echo ===================================================
echo.

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in the PATH.
    echo Please install Python 3.8 or later and try again.
    pause
    exit /B 1
)

REM Get the current directory
set PROJECT_DIR=%~dp0
cd %PROJECT_DIR%

REM Create virtual environment if it doesn't exist
if not exist venv\ (
    echo Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo Failed to create virtual environment.
        pause
        exit /B 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Create a logs directory if it doesn't exist
if not exist logs\ mkdir logs

REM Set environment variables to prevent errors
set HF_HUB_DISABLE_SYMLINKS_WARNING=1
set TORCH_DEVICE_BACKEND_AUTOLOAD=0

REM Install dependencies
echo Installing required packages...
pip install -r requirements.txt
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.3/en_core_sci_sm-0.5.3.tar.gz

REM Check for system dependencies
echo Checking system dependencies for advanced file processing and web scraping...
python -c "from utils.dependency_checker import check_dependencies; check_dependencies()"

REM Detect CPU vendor and install appropriate extensions
echo Detecting CPU vendor for optimized PyTorch extensions...
python -c "import platform; cpu_info = platform.processor(); print(f'CPU: {cpu_info}')"
python -c "import platform; is_intel = 'Intel' in platform.processor(); is_amd = 'AMD' in platform.processor(); print(f'Intel CPU: {is_intel}'); print(f'AMD CPU: {is_amd}'); exit(0 if is_intel else 1 if is_amd else 2)" >nul
if %ERRORLEVEL% == 0 (
    echo Intel CPU detected - Installing Intel extension for PyTorch...
    pip install intel-extension-for-pytorch --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/
    set USE_INTEL_NPU=1
) else if %ERRORLEVEL% == 1 (
    echo AMD CPU detected - Installing AMD optimizers...
    pip install --upgrade torch
    REM Check if AMD ROCm is available for this system
    python -c "import os; os.environ['PYTORCH_ROCM_ARCH'] = 'gfx900;gfx906;gfx908;gfx90a'; import torch; print(f'PyTorch compiled with ROCm: {torch.backends.cuda.is_built()}')"
    if %ERRORLEVEL% == 0 (
        echo AMD ROCm platform appears to be available
        set USE_AMD_NPU=1
    )
)

REM NVIDIA GPU Support - Installing proper CUDA version for PyTorch
echo Checking for NVIDIA GPU...
python -c "import torch; print('CUDA Available: ' + str(torch.cuda.is_available()))"
if %ERRORLEVEL% == 0 (
    echo Checking PyTorch CUDA compatibility...
    pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/cu118
)

REM Check for AMD ROCm support
echo Checking for AMD GPU...
python -c "import torch; hasattr_hip = hasattr(torch, 'hip'); hip_available = hasattr(torch, 'hip') and torch.hip.is_available() if hasattr_hip else False; print(f'AMD ROCm Available: {hip_available}')"

REM Set environment variables for running the application
set FLASK_DEBUG=true
set PORT=5000
set MODEL_PATH=HPAI-BSC/Llama3.1-Aloe-Beta-8B
set PYTHONPATH=%PROJECT_DIR%  # Added to include project root in Python path

echo.
echo ===================================================
echo Starting ClinicalGPT Medical Assistant
echo ===================================================
echo.

echo Starting server...
echo.
echo Server will be accessible at http://localhost:5000
echo Your web browser should open automatically...
echo DO NOT CLOSE THIS WINDOW while using the application
echo.

REM Try to open the web browser automatically
start "" http://localhost:5000

REM Launch server and keep it running
python -m server.server

echo.
echo ===================================================
echo Server stopped
echo ===================================================
echo.

pause
