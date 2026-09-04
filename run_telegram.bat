@echo off
echo ===================================================
echo   CLIO TELEGRAM BOT LAUNCHER
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
echo Starting Telegram Bot (telegram_bot.py)...
".venv\Scripts\python" telegram_bot.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Telegram Bot crashed or closed unexpectedly.
    pause
) else (
    echo.
    echo Telegram Bot closed normally.
)
