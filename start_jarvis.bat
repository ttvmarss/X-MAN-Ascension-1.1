@echo off
title JARVIS — Starting...
color 0B

echo.
echo  ==========================================
echo   J.A.R.V.I.S  —  Windows 10 + iPhone
echo   Starting up...
echo  ==========================================
echo.

if not exist ".env" (
    echo [ERROR] .env file not found. Run setup_windows.bat first.
    pause
    exit /b 1
)

findstr /C:"ANTHROPIC_API_KEY=your-" ".env" >nul
if %errorlevel% equ 0 (
    echo [WARNING] ANTHROPIC_API_KEY still set to placeholder in .env
    echo           Edit .env with your real API key before continuing.
    pause
    exit /b 1
)

:: Build frontend if not already built (or if main.ts changed)
if not exist "frontend\dist\index.html" (
    echo [BUILD] Building frontend for production...
    cd frontend
    call npm run build
    if %errorlevel% neq 0 (
        echo [ERROR] Frontend build failed.
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo [OK] Frontend built.
)

:: Start backend server (serves both API and UI on the same port over HTTPS)
echo [START] Launching JARVIS server...
echo         (it will print your LAN URL + a QR code for your phone)
echo.

:: Run in foreground so user sees the QR code
python server.py

pause
