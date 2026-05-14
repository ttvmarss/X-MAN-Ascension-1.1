@echo off
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0tunnel.ps1"
pause
