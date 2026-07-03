@echo off
echo ========================================
echo NOVA Advanced Protection (PyArmor)
echo ========================================
echo.

echo Installing PyArmor...
pip install pyarmor

echo.
echo Obfuscating core modules...
pyarmor gen --output dist_protected core desktop.py

echo.
echo ========================================
echo Protection Complete!
echo Protected files are in: ./dist_protected/
echo ========================================
pause
