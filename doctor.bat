@echo off
setlocal enabledelayedexpansion
title JARVIS - Doctor
color 0E

cls
echo.
echo  ============================================================
echo                 JARVIS DOCTOR - Diagnostics
echo  ============================================================
echo.
echo  Checking your setup for common issues...
echo.

set FAIL=0

:: Node
echo  [1] Node.js
where node >nul 2>&1
if errorlevel 1 (
    echo      [X] Not installed. Install from https://nodejs.org/
    set /a FAIL+=1
) else (
    for /f "delims=v" %%v in ('node --version') do set NODE_VER=%%v
    for /f "tokens=1 delims=." %%a in ("!NODE_VER!") do set NODE_MAJOR=%%a
    if !NODE_MAJOR! LSS 18 (
        echo      [X] v!NODE_VER! is too old. Need 18+. Update at https://nodejs.org/
        set /a FAIL+=1
    ) else (
        echo      [OK] v!NODE_VER!
    )
)

:: npm
echo  [2] npm
where npm >nul 2>&1
if errorlevel 1 (
    echo      [X] Not found - reinstall Node.js
    set /a FAIL+=1
) else (
    for /f %%v in ('npm --version') do echo      [OK] v%%v
)

:: .env file
echo  [3] .env config
if not exist ".env" (
    echo      [X] Missing - run INSTALL.bat
    set /a FAIL+=1
) else (
    findstr /C:"your-anthropic-api-key-here" ".env" >nul
    if not errorlevel 1 (
        echo      [X] ANTHROPIC_API_KEY is still the placeholder
        set /a FAIL+=1
    ) else (
        findstr /C:"ANTHROPIC_API_KEY=sk-ant" ".env" >nul
        if errorlevel 1 (
            echo      [!] ANTHROPIC_API_KEY does not start with sk-ant-
        ) else (
            echo      [OK] API key looks valid
        )
    )
)

:: node_modules
echo  [4] Backend dependencies
if not exist "node_modules" (
    echo      [X] Missing - run INSTALL.bat
    set /a FAIL+=1
) else (
    echo      [OK] Installed
)

:: frontend deps
echo  [5] Frontend dependencies
if not exist "frontend\node_modules" (
    echo      [X] Missing - run INSTALL.bat
    set /a FAIL+=1
) else (
    echo      [OK] Installed
)

:: frontend build
echo  [6] Frontend build
if not exist "frontend\dist\index.html" (
    echo      [!] Not built yet. start_jarvis.bat will build it automatically.
) else (
    echo      [OK] Built
)

:: Port 8000
echo  [7] Port 8000 availability
netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul
if not errorlevel 1 (
    echo      [!] Port 8000 is already in use by another process.
    echo          If JARVIS won't start, stop the other program or
    echo          change PORT in .env to e.g. 8001.
) else (
    echo      [OK] Port 8000 is free
)

:: Firewall hint
echo  [8] Firewall
echo      [i] If your phone can't connect, Windows Firewall may be
echo          blocking Node.js. Allow it for Private networks.

echo.
echo  ============================================================
if !FAIL! EQU 0 (
    color 0A
    echo   All checks passed. Run start_jarvis.bat to launch JARVIS.
) else (
    color 0C
    echo   Found !FAIL! issue^(s^). Fix the [X] items above.
)
echo  ============================================================
echo.
pause
