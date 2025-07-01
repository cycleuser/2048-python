@echo off
chcp 65001 >nul
title 2048 Console Game
echo Starting 2048 Console Game...
echo.
python console_game.py
if errorlevel 1 (
    echo.
    echo Error: Failed to start the game.
    echo Please make sure Python is installed and console_game.py exists.
    pause
) 