@echo off
echo ===================================================
echo Cleaning up ClinicalGPT Medical Assistant
echo ===================================================
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

REM Additional cleanup steps can be added here if needed

echo.
echo ===================================================
echo Cleanup complete
echo ===================================================
echo.

pause
