2048 Python (PySide6 Version)
==============================

[![Run on Repl.it](https://repl.it/badge/github/yangshun/2048-python)](https://repl.it/github/yangshun/2048-python)

---

**⚠️NOTE⚠️**: This is a PySide6 version of the original tkinter-based 2048 game, featuring enhanced UI and additional functionality.

---

Based on the popular game [2048](https://github.com/gabrielecirulli/2048) by Gabriele Cirulli. The game's objective is to slide numbered tiles on a grid to combine them to create a tile with the number 2048. This version uses PySide6 for a modern, responsive interface!

![screenshot](img/screenshot.png)

## Features

### GUI版本特性
- **Modern PySide6 Interface**: Enhanced visual experience with Qt framework
- **Fullscreen Support**: Press F11 to toggle fullscreen mode
- **Responsive Layout**: Game board maintains square aspect ratio and scales with window size
- **Undo Function**: Press 'B' to undo the last move
- **Multiple Control Schemes**: 
  - Arrow keys (↑↓←→)
  - WASD keys
  - Alternative IJKL keys

### 控制台版本特性
- **Cross-platform Terminal Support**: Works on Windows PowerShell, Linux bash, and macOS terminal
- **Colorful Interface**: ANSI color codes for enhanced visual experience
- **Real-time Score Display**: Shows current score and move count
- **Interactive Help System**: Press 'H' for in-game help
- **Restart Function**: Quick game restart with 'R' key
- **Unicode Characters**: Beautiful box-drawing characters for game board
- **Responsive Display**: Automatically clears screen for smooth gameplay

## Installation

First, install the required dependencies:

    $ pip install -r requirements.txt

## Running the Game

### GUI版本 (PySide6)

要启动图形界面版本，运行：
    
    $ python game.py

或使用原始的分离文件版本：

    $ python puzzle.py

### 控制台版本

要启动控制台版本，可以使用以下方式：

**直接运行：**
    
    $ python console_game.py

**Windows (PowerShell/CMD)：**
    
    $ start_console.bat

**Linux/macOS (Bash)：**
    
    $ ./start_console.sh

**或使用Python启动脚本：**
    
    $ python start_console.py

## Controls

### GUI版本控制
- **Movement**: Use arrow keys, WASD, or IJKL to move tiles
- **Undo**: Press 'B' to undo the last move  
- **Fullscreen**: Press 'F11' to toggle fullscreen mode
- **Quit**: Press 'Escape' to exit the game

### 控制台版本控制
- **Movement**: Use arrow keys or WASD to move tiles
- **Restart**: Press 'R' to restart the game
- **Help**: Press 'H' to show help information
- **Quit**: Press 'Q' or 'Escape' to exit the game

## Requirements

### GUI版本
- Python 3.6+
- PySide6 6.5.0+

### 控制台版本
- Python 3.6+
- 支持ANSI颜色代码的终端 (大多数现代终端都支持)
- Windows: PowerShell, Command Prompt, Windows Terminal
- Linux/macOS: Bash, Zsh, 或任何兼容终端

Contributors:
==

- [Yanghun Tay](http://github.com/yangshun) - Original tkinter version
- [Emmanuel Goh](http://github.com/emman27) - Original tkinter version
- PySide6 modernization and enhancements
