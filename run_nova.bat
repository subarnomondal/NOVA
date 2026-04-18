@echo off
echo ===================================================
echo   NOVA AI LAUNCHER
echo ===================================================
echo.
echo Initializing Virtual Environment...

REM Check if venv exists
if not exist ".venv" (
    echo [ERROR] Virtual Environment not found!
    echo Please ask the assistant to repair environment.
    pause
    exit /b
)

REM Activate and run
echo Starting Desktop App (desktop.py)...
".venv\Scripts\python" desktop.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Nova crashed or closed unexpectedly.
    pause
) else (
    echo.
    echo Nova closed normally.
)
