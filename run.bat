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
pip install pillow accelerate

REM NVIDIA GPU Support - Installing proper CUDA version for PyTorch
echo Checking for NVIDIA GPU...
python -c "import torch; print('CUDA Available: ' + str(torch.cuda.is_available()))"
if %ERRORLEVEL% == 0 (
    echo Checking PyTorch CUDA compatibility...
    pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/cu118
)

REM Set environment variables for running the application
set FLASK_DEBUG=true
set PORT=5000
set MODEL_PATH=medicalai/ClinicalGPT-base-zh

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
python server\server.py

echo.
echo ===================================================
echo Server stopped
echo ===================================================
echo.

pause