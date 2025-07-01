#!/usr/bin/env python3
"""
简单的启动脚本 - 2048控制台版本
"""

import sys
import os

def main():
    try:
        # 导入并运行控制台游戏
        from console_game import Console2048
        
        game = Console2048()
        game.play()
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保 console_game.py 文件在同一目录下")
    except Exception as e:
        print(f"启动游戏时出错: {e}")
    
    input("按Enter键退出...")

if __name__ == '__main__':
    main() 