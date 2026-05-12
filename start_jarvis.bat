@echo off
setlocal
title JARVIS
color 0B

:: Pre-flight checks with friendly errors
if not exist ".env" (
    color 0C
    echo.
    echo  [X] .env file not found.
    echo.
    echo      You need to run INSTALL.bat first.
    echo.
    pause
    exit /b 1
)

if not exist "node_modules" (
    color 0C
    echo.
    echo  [X] Dependencies not installed.
    echo.
    echo      You need to run INSTALL.bat first.
    echo.
    pause
    exit /b 1
)

findstr /C:"your-anthropic-api-key-here" ".env" >nul
if not errorlevel 1 (
    color 0C
    echo.
    echo  [X] ANTHROPIC_API_KEY is still the placeholder.
    echo.
    echo      Edit .env in this folder and paste a real key,
    echo      or run INSTALL.bat again to set it interactively.
    echo.
    pause
    exit /b 1
)

:: Build frontend if missing
if not exist "frontend\dist\index.html" (
    echo  [BUILD] Building frontend (one-time)...
    cd frontend
    call npm run build
    cd ..
    if errorlevel 1 (
        color 0C
        echo  [X] Frontend build failed. Try running INSTALL.bat again.
        pause
        exit /b 1
    )
)

cls
echo.
echo  Starting JARVIS... your URL and QR code will appear below.
echo  (Press Ctrl+C in this window to stop.)
echo.

node server.js

echo.
echo  JARVIS stopped.
pause
