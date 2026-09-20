@echo off
chcp 65001 >nul
title Antigravity 2.0 Desktop Studio
echo Launching Antigravity Bot Hub...
python main.py %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Make sure Python 3 is installed and in PATH.
    pause
)
