@echo off
title JARVIS Setup — Windows 10
color 0B

echo.
echo  ==========================================
echo   J.A.R.V.I.S  —  Windows 10 + iPhone
echo   Setup
echo  ==========================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.11+ from https://python.org
    pause
    exit /b 1
)
echo [OK] Python found.

node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)
echo [OK] Node.js found.

if not exist ".env" (
    copy ".env.example" ".env"
    echo.
    echo [SETUP] Created .env file.
    echo         Open .env and add your API keys:
    echo           ANTHROPIC_API_KEY=your-key-here
    echo           FISH_API_KEY=your-key-here  (optional)
    echo           USER_NAME=YourName
    echo.
    echo Press any key AFTER editing .env to continue...
    pause >nul
)

echo.
echo [SETUP] Installing Python dependencies (this includes Whisper, will take a few min)...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)
echo [OK] Python dependencies installed.

echo.
echo [SETUP] Installing Playwright Chromium (for web research)...
python -m playwright install chromium
echo [OK] Playwright ready.

echo.
echo [SETUP] Installing frontend dependencies...
cd frontend
call npm install
if %errorlevel% neq 0 (
    echo [ERROR] npm install failed.
    cd ..
    pause
    exit /b 1
)
echo [SETUP] Building frontend...
call npm run build
cd ..
echo [OK] Frontend ready.

:: Windows Firewall hint
echo.
echo [INFO] To use JARVIS from your iPhone, Windows Firewall must allow Python.
echo        If prompted on first run, click "Allow access" for Private networks.
echo.

if not exist "%USERPROFILE%\Documents\JARVIS" mkdir "%USERPROFILE%\Documents\JARVIS"
if not exist "%USERPROFILE%\Documents\JARVIS Notes" mkdir "%USERPROFILE%\Documents\JARVIS Notes"
if not exist "%USERPROFILE%\Documents\JARVIS Projects" mkdir "%USERPROFILE%\Documents\JARVIS Projects"
echo [OK] Created JARVIS directories in Documents.

echo.
echo  ==========================================
echo   Setup complete!
echo.
echo   Start JARVIS:     start_jarvis.bat
echo.
echo   On this PC:       open the URL it prints
echo   On your iPhone:   scan the QR code in Safari
echo                     (accept the security warning - it's
echo                     your own self-signed cert)
echo  ==========================================
echo.
pause
