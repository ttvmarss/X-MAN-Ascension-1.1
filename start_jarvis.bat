@echo off
title JARVIS
color 0B

if not exist ".env" (
    echo [ERROR] .env file not found. Run setup_windows.bat first.
    pause
    exit /b 1
)

if not exist "node_modules" (
    echo [ERROR] Dependencies not installed. Run setup_windows.bat first.
    pause
    exit /b 1
)

findstr /C:"ANTHROPIC_API_KEY=sk-ant" ".env" >nul
if %errorlevel% neq 0 (
    findstr /C:"ANTHROPIC_API_KEY=your-" ".env" >nul
    if not errorlevel 1 (
        echo [ERROR] ANTHROPIC_API_KEY still set to placeholder.
        echo         Edit .env with your real key, then try again.
        pause
        exit /b 1
    )
)

:: Build frontend if dist missing
if not exist "frontend\dist\index.html" (
    echo [BUILD] Building frontend...
    cd frontend
    call npm run build
    cd ..
)

echo.
node server.js
echo.
echo JARVIS stopped.
pause
