@echo off
echo ===================================================
echo   CLIO AI LAUNCHER
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

echo Checking for ghost processes and duplicate instances...
wmic process where "name='python.exe' and commandline like '%desktop.py%'" call terminate >nul 2>&1

REM Activate and run
REM Telegram bot is now natively integrated inside desktop.py!

echo Starting Desktop App (desktop.py)...
".venv\Scripts\python" desktop.py 2>> userdata\crash_dump.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Clio crashed or closed unexpectedly.
    echo [INFO] The crash details have been saved to userdata\crash_dump.txt
    pause
) else (
    echo.
    echo Clio closed normally.
)
