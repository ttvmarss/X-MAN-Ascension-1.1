@echo off
title JARVIS Setup — Windows 10
color 0B

echo.
echo  ==========================================
echo   J.A.R.V.I.S  —  Windows 10 Edition
echo   Just A Rather Very Intelligent System
echo  ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.11+ from https://python.org
    pause
    exit /b 1
)
echo [OK] Python found.

:: Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)
echo [OK] Node.js found.

:: Create .env if it doesn't exist
if not exist ".env" (
    copy ".env.example" ".env"
    echo.
    echo [SETUP] Created .env file.
    echo         Open .env and add your API keys:
    echo           ANTHROPIC_API_KEY=your-key-here
    echo           FISH_API_KEY=your-key-here
    echo           USER_NAME=YourName
    echo.
    echo Press any key AFTER editing .env to continue...
    pause >nul
)

:: Install Python dependencies
echo.
echo [SETUP] Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] pip install failed. Check your Python installation.
    pause
    exit /b 1
)
echo [OK] Python dependencies installed.

:: Install Playwright browsers
echo.
echo [SETUP] Installing Playwright browsers (this may take a few minutes)...
python -m playwright install chromium
echo [OK] Playwright ready.

:: Install frontend dependencies
echo.
echo [SETUP] Installing frontend dependencies...
cd frontend
call npm install
if %errorlevel% neq 0 (
    echo [ERROR] npm install failed. Check your Node.js installation.
    cd ..
    pause
    exit /b 1
)
cd ..
echo [OK] Frontend dependencies installed.

:: Create data directories
if not exist "%USERPROFILE%\Documents\JARVIS" mkdir "%USERPROFILE%\Documents\JARVIS"
if not exist "%USERPROFILE%\Documents\JARVIS Notes" mkdir "%USERPROFILE%\Documents\JARVIS Notes"
if not exist "%USERPROFILE%\Documents\JARVIS Projects" mkdir "%USERPROFILE%\Documents\JARVIS Projects"
echo [OK] Created JARVIS directories in Documents.

echo.
echo  ==========================================
echo   Setup complete!
echo.
echo   To start JARVIS, run:  start_jarvis.bat
echo   Then open Chrome at:   http://localhost:8340
echo  ==========================================
echo.
pause
