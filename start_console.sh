#!/bin/bash

echo "Starting 2048 Console Game..."
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

# 尝试使用Python3，如果不存在则使用python
if command -v python3 &> /dev/null; then
    python3 console_game.py
elif command -v python &> /dev/null; then
    python console_game.py
else
    echo "Error: Python interpreter not found"
    exit 1
fi

# 如果游戏异常退出，显示错误信息
if [ $? -ne 0 ]; then
    echo
    echo "Error: Failed to start the game."
    echo "Please make sure console_game.py exists in the current directory."
    read -p "Press Enter to exit..."
fi 