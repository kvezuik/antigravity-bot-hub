@echo off
chcp 65001 >nul
title Antigravity Bot Hub - Grok Edition
echo Launching Antigravity Bot Hub...
python main.py %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Make sure Python 3 is installed and in PATH.
    pause
)
