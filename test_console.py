#!/usr/bin/env python3
"""
控制台版本2048游戏测试脚本
"""

import platform
import sys

def test_imports():
    """测试所有必要的模块导入"""
    print("测试模块导入...")
    
    try:
        import random
        print("✓ random 模块导入成功")
    except ImportError as e:
        print(f"✗ random 模块导入失败: {e}")
        return False
    
    try:
        import os
        print("✓ os 模块导入成功")
    except ImportError as e:
        print(f"✗ os 模块导入失败: {e}")
        return False
    
    # 测试平台特定的模块
    system = platform.system()
    print(f"检测到系统: {system}")
    
    if system == 'Windows':
        try:
            import msvcrt
            print("✓ msvcrt 模块导入成功 (Windows)")
        except ImportError as e:
            print(f"✗ msvcrt 模块导入失败: {e}")
            return False
    else:
        try:
            import termios
            import tty
            print("✓ termios 和 tty 模块导入成功 (Unix/Linux)")
        except ImportError as e:
            print(f"✗ termios/tty 模块导入失败: {e}")
            return False
    
    return True

def test_game_logic():
    """测试游戏逻辑"""
    print("\n测试游戏逻辑...")
    
    try:
        from console_game import new_game, add_two, game_state, left, right, up, down
        
        # 测试新游戏创建
        matrix = new_game(4)
        print(f"✓ 新游戏创建成功，矩阵大小: {len(matrix)}x{len(matrix[0])}")
        
        # 计算非零元素数量
        non_zero = sum(1 for row in matrix for cell in row if cell != 0)
        print(f"✓ 初始非零元素数量: {non_zero} (应该是2)")
        
        # 测试游戏状态检查
        state = game_state(matrix)
        print(f"✓ 游戏状态检查成功: {state}")
        
        # 测试移动函数
        original = [row[:] for row in matrix]  # 深拷贝
        new_matrix, moved = left(matrix)
        print(f"✓ 左移动测试完成，是否移动: {moved}")
        
        return True
        
    except Exception as e:
        print(f"✗ 游戏逻辑测试失败: {e}")
        return False

def test_display():
    """测试显示功能"""
    print("\n测试显示功能...")
    
    try:
        from console_game import print_matrix, clear_screen, Colors
        
        # 测试颜色代码
        print("测试ANSI颜色代码:")
        print(f"{Colors.BOLD}粗体文本{Colors.RESET}")
        print(f"{Colors.COLORS[2]} 2 {Colors.RESET} {Colors.COLORS[4]} 4 {Colors.RESET}")
        
        # 创建测试矩阵
        test_matrix = [
            [2, 4, 8, 16],
            [32, 64, 128, 256],
            [512, 1024, 2048, 0],
            [0, 0, 0, 0]
        ]
        
        print("\n显示测试矩阵:")
        print_matrix(test_matrix, score=1234, moves=10)
        
        return True
        
    except Exception as e:
        print(f"✗ 显示功能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("="*50)
    print("2048 控制台版本测试")
    print("="*50)
    
    all_passed = True
    
    # 运行所有测试
    tests = [
        test_imports,
        test_game_logic,
        test_display
    ]
    
    for test in tests:
        try:
            if not test():
                all_passed = False
        except Exception as e:
            print(f"✗ 测试异常: {e}")
            all_passed = False
        print("-" * 30)
    
    # 显示总结
    print("\n" + "="*50)
    if all_passed:
        print("🎉 所有测试通过! 控制台版本应该可以正常运行。")
        print(f"你可以运行: python console_game.py")
    else:
        print("❌ 部分测试失败。请检查错误信息。")
    print("="*50)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断。")
    except Exception as e:
        print(f"\n\n测试过程中发生意外错误: {e}")
    
    input("\n按Enter键退出...") 