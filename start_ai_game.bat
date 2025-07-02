@echo off
chcp 65001 >nul
title 2048 AI Enhanced Game
echo ========================================
echo 🎮 2048 AI Enhanced Game Launcher
echo ========================================
echo.
echo Starting the enhanced 2048 game with AI features...
echo.
python start_ai_game.py
if errorlevel 1 (
    echo.
    echo Error: Failed to start the game.
    echo Please make sure Python is installed and all files are present.
    echo.
    echo Required files:
    echo - start_ai_game.py
    echo - ai_game.py
    echo.
    pause
) 