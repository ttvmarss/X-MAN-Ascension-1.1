@echo off
title JARVIS Setup — Windows 10
color 0B

echo.
echo  ==========================================
echo   J.A.R.V.I.S  -  Windows 10 + iPhone
echo   Setup (Node.js edition)
echo  ==========================================
echo.

:: Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found.
    echo         Install Node.js 18 or newer from https://nodejs.org
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('node --version') do echo [OK] Node.js %%v
echo.

:: Create .env from example if missing
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo [SETUP] Created .env file.
    echo.
    echo  ============================================================
    echo   IMPORTANT: Open .env and add your Anthropic API key.
    echo.
    echo   Get a key at:  https://console.anthropic.com
    echo.
    echo   Edit this line in .env:
    echo     ANTHROPIC_API_KEY=sk-ant-...
    echo  ============================================================
    echo.
    echo Press any key AFTER you have edited .env...
    pause >nul
)

:: Install backend (Node) dependencies
echo [SETUP] Installing backend dependencies...
call npm install
if %errorlevel% neq 0 (
    echo [ERROR] npm install failed.
    pause
    exit /b 1
)
echo [OK] Backend ready.
echo.

:: Install + build frontend
echo [SETUP] Installing frontend dependencies...
cd frontend
call npm install
if %errorlevel% neq 0 (
    echo [ERROR] Frontend npm install failed.
    cd ..
    pause
    exit /b 1
)
echo [SETUP] Building frontend for production...
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Frontend build failed.
    cd ..
    pause
    exit /b 1
)
cd ..
echo [OK] Frontend built.
echo.

:: Create data directories
if not exist "%USERPROFILE%\Documents\JARVIS" mkdir "%USERPROFILE%\Documents\JARVIS"
if not exist "%USERPROFILE%\Documents\JARVIS Notes" mkdir "%USERPROFILE%\Documents\JARVIS Notes"
if not exist "%USERPROFILE%\Documents\JARVIS Projects" mkdir "%USERPROFILE%\Documents\JARVIS Projects"

echo.
echo  ============================================================
echo   Setup complete.
echo.
echo   Start JARVIS:  start_jarvis.bat
echo.
echo   On this PC:     open the URL it prints in your browser
echo   On your phone:  scan the QR code in Safari/Chrome
echo                   (same WiFi network as this PC)
echo.
echo   Windows Firewall: if prompted on first run, click
echo   "Allow access" for Private networks (so phone can connect)
echo  ============================================================
echo.
pause
