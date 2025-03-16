@echo off
echo ===================================================
echo Cleaning up ClinicalGPT Medical Assistant
echo ===================================================
echo.

REM Ask for confirmation before proceeding with cleanup
echo This will remove all local data including:
echo  - Python virtual environment (venv)
echo  - Downloaded models and weights
echo  - Log files
echo  - Cache directories
echo  - Temporary files
echo.
set /p CONFIRM="Are you sure you want to proceed? (y/n): "
if /i "%CONFIRM%" neq "y" (
    echo Cleanup cancelled.
    pause
    exit /B 0
)

echo.
echo Starting cleanup process...
echo.

REM Delete virtual environment if it exists
if exist venv\ (
    echo Deleting virtual environment...
    rmdir /s /q venv
    if %ERRORLEVEL% neq 0 (
        echo Failed to delete virtual environment.
        pause
        exit /B 1
    )
)

REM Delete logs directory if it exists
if exist logs\ (
    echo Deleting logs directory...
    rmdir /s /q logs
    if %ERRORLEVEL% neq 0 (
        echo Failed to delete logs directory.
        pause
        exit /B 1
    )
)

REM Delete downloaded models if they exist
if exist models\ (
    echo Deleting downloaded models...
    rmdir /s /q models
    if %ERRORLEVEL% neq 0 (
        echo Failed to delete models directory.
        pause
        exit /B 1
    )
)

REM Delete model_data if it exists
if exist model_data\ (
    echo Deleting model data...
    rmdir /s /q model_data
    if %ERRORLEVEL% neq 0 (
        echo Failed to delete model_data directory.
        pause
        exit /B 1
    )
)

REM Delete saved_models if it exists
if exist saved_models\ (
    echo Deleting saved models...
    rmdir /s /q saved_models
    if %ERRORLEVEL% neq 0 (
        echo Failed to delete saved_models directory.
        pause
        exit /B 1
    )
)

REM Delete any Python cache directories
for /d /r . %%d in (__pycache__) do @if exist "%%d" (
    echo Deleting %%d...
    rmdir /s /q "%%d"
)

REM Delete any .pyc files
echo Deleting Python compiled files...
del /s /q *.pyc 2>nul

REM Delete HuggingFace cache if requested
set /p HF_CACHE="Would you like to clear the HuggingFace cache as well? (y/n): "
if /i "%HF_CACHE%" equ "y" (
    echo Clearing HuggingFace cache...
    
    REM Using Python to clear the cache
    python -c "from huggingface_hub.constants import HF_CACHE; print(f'Cache location: {HF_CACHE}'); import shutil; shutil.rmtree(HF_CACHE, ignore_errors=True); print('Cache cleared.')" 2>nul
    
    if %ERRORLEVEL% neq 0 (
        echo Failed to clear HuggingFace cache. You may need to delete it manually.
    )
)

REM Delete temp files in the current directory
echo Deleting temporary files...
if exist temp\ rmdir /s /q temp
if exist tmp\ rmdir /s /q tmp

REM Delete any log files in the root directory
del /q *.log 2>nul
del /q *log.txt 2>nul

REM Delete server debug log if it exists
if exist server_debug.log (
    echo Deleting server debug log...
    del /q server_debug.log
)

echo.
echo ===================================================
echo Cleanup complete!
echo ===================================================
echo All temporary data, models and environments have been removed.
echo You will need to run the setup script again to reinstall dependencies.
echo.

pause
