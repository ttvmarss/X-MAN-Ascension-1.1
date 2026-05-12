@echo off
title JARVIS — Starting...
color 0B

echo.
echo  ==========================================
echo   J.A.R.V.I.S  —  Windows 10 Edition
echo   Starting up...
echo  ==========================================
echo.

:: Check .env exists
if not exist ".env" (
    echo [ERROR] .env file not found. Run setup_windows.bat first.
    pause
    exit /b 1
)

:: Check API key is set
findstr /C:"ANTHROPIC_API_KEY=your-" ".env" >nul
if %errorlevel% equ 0 (
    echo [WARNING] ANTHROPIC_API_KEY still set to placeholder in .env
    echo           Edit .env with your real API key before continuing.
    pause
    exit /b 1
)

:: Build frontend if dist doesn't exist
if not exist "frontend\dist\index.html" (
    echo [SETUP] Building frontend...
    cd frontend
    call npm run build
    cd ..
    echo [OK] Frontend built.
)

:: Start backend server in a new window (port 8000)
echo [START] Launching JARVIS backend on port 8000...
start "JARVIS Backend" cmd /k "python server.py"

:: Start frontend dev server in a new window (port 8340, proxies /ws to 8000)
echo [START] Launching JARVIS frontend on port 8340...
start "JARVIS Frontend" cmd /k "cd frontend && npm run dev"

:: Wait 3 seconds for both to start
timeout /t 3 /nobreak >nul

:: Open Chrome (try different paths)
echo [START] Opening Chrome...
set CHROME_PATH=""
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
) else if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
)

if %CHROME_PATH%=="" (
    echo [INFO] Chrome not found at default paths. Opening in default browser.
    start http://localhost:8340
) else (
    start "" %CHROME_PATH% "http://localhost:8340"
)

echo.
echo  ==========================================
echo   JARVIS is running!
echo.
echo   Backend:  http://localhost:8340
echo   UI:       http://localhost:8340
echo.
echo   Click anywhere on the page to activate.
echo   Then speak naturally.
echo.
echo   Close this window to stop the launcher.
echo  ==========================================
echo.
pause
