@echo off
echo ========================================================
echo       CLIO (NOVA) - Local AGI Desktop Setup
echo ========================================================
echo.
echo Installing Python dependencies...
pip install -r ..\requirements.txt
echo.
echo Installing Playwright browsers (for web search skills)...
playwright install
echo.
echo Installing YT-DLP (for music/media skills)...
pip install yt-dlp
echo.
echo ========================================================
echo Setup Complete!
echo.
echo IMPORTANT NEXT STEPS:
echo 1. Open the 'userdata/config' folder (it will be created on first run)
echo    or rename 'keys.example.json' to 'keys.json' if it exists.
echo 2. Add your OpenRouter, Groq, or OpenAI API key.
echo 3. Run 'run_clio.bat' to start the AI Desktop Assistant.
echo ========================================================
pause
