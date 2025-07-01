#!/usr/bin/env python3
"""
2048 Console Game - Cross-platform Terminal Version
Supports Windows PowerShell and Linux/macOS bash terminals
"""

import sys
import os
import random
import platform

# 跨平台键盘输入处理
if platform.system() == 'Windows':
    import msvcrt
else:
    import termios
    import tty

# ==================== CONSTANTS ====================
GRID_LEN = 4

# ANSI 颜色代码
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # 背景颜色
    BG_DEFAULT = '\033[48;5;237m'  # 深灰色背景
    BG_EMPTY = '\033[48;5;250m'    # 浅灰色
    
    # 数字颜色映射
    COLORS = {
        0: '\033[48;5;250m\033[30m',      # 空格 - 浅灰背景，黑字
        2: '\033[48;5;255m\033[30m',      # 白色背景，黑字
        4: '\033[48;5;254m\033[30m',      # 浅白背景，黑字
        8: '\033[48;5;214m\033[97m',      # 橙色背景，白字
        16: '\033[48;5;208m\033[97m',     # 深橙背景，白字
        32: '\033[48;5;196m\033[97m',     # 红色背景，白字
        64: '\033[48;5;160m\033[97m',     # 深红背景，白字
        128: '\033[48;5;227m\033[30m',    # 浅黄背景，黑字
        256: '\033[48;5;226m\033[30m',    # 黄色背景，黑字
        512: '\033[48;5;220m\033[30m',    # 金黄背景，黑字
        1024: '\033[48;5;214m\033[30m',   # 橙黄背景，黑字
        2048: '\033[48;5;196m\033[97m',   # 红色背景，白字（获胜）
    }

# ==================== CROSS-PLATFORM INPUT ====================

def get_key():
    """跨平台获取键盘输入"""
    if platform.system() == 'Windows':
        return get_key_windows()
    else:
        return get_key_unix()

def get_key_windows():
    """Windows下获取键盘输入"""
    key = msvcrt.getch()
    if key == b'\xe0':  # 特殊键前缀
        key = msvcrt.getch()
        if key == b'H':    # 上箭头
            return 'UP'
        elif key == b'P':  # 下箭头
            return 'DOWN'
        elif key == b'K':  # 左箭头
            return 'LEFT'
        elif key == b'M':  # 右箭头
            return 'RIGHT'
    else:
        char = key.decode('utf-8', errors='ignore').upper()
        if char == '\x1b':  # ESC
            return 'ESC'
        elif char == '\r':  # Enter
            return 'ENTER'
        elif char == '\x08':  # Backspace
            return 'BACKSPACE'
        else:
            return char

def get_key_unix():
    """Unix/Linux下获取键盘输入"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        key = sys.stdin.read(1)
        
        if key == '\x1b':  # ESC 或方向键
            key += sys.stdin.read(2)
            if key == '\x1b[A':
                return 'UP'
            elif key == '\x1b[B':
                return 'DOWN'
            elif key == '\x1b[D':
                return 'LEFT'
            elif key == '\x1b[C':
                return 'RIGHT'
            else:
                return 'ESC'
        elif key == '\r' or key == '\n':
            return 'ENTER'
        elif key == '\x7f' or key == '\x08':  # DEL 或 Backspace
            return 'BACKSPACE'
        elif key == '\x03':  # Ctrl+C
            return 'ESC'
        else:
            return key.upper()
            
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

# ==================== GAME LOGIC ====================

def new_game(n):
    """创建新游戏矩阵"""
    matrix = [[0 for _ in range(n)] for _ in range(n)]
    matrix = add_two(matrix)
    matrix = add_two(matrix)
    return matrix

def add_two(mat):
    """随机添加一个2到空位置"""
    empty_cells = [(i, j) for i in range(len(mat)) for j in range(len(mat[0])) if mat[i][j] == 0]
    if empty_cells:
        row, col = random.choice(empty_cells)
        mat[row][col] = 2
    return mat

def game_state(mat):
    """检查游戏状态"""
    # 检查是否获胜
    for row in mat:
        if 2048 in row:
            return 'win'
    
    # 检查是否还有空位
    for row in mat:
        if 0 in row:
            return 'continue'
    
    # 检查是否可以合并
    for i in range(len(mat)):
        for j in range(len(mat[0])):
            if j < len(mat[0]) - 1 and mat[i][j] == mat[i][j + 1]:
                return 'continue'
            if i < len(mat) - 1 and mat[i][j] == mat[i + 1][j]:
                return 'continue'
    
    return 'lose'

def reverse(mat):
    """反转矩阵的每一行"""
    return [row[::-1] for row in mat]

def transpose(mat):
    """转置矩阵"""
    return [[mat[j][i] for j in range(len(mat))] for i in range(len(mat[0]))]

def cover_up(mat):
    """将非零元素向左移动"""
    new_mat = [[0 for _ in range(GRID_LEN)] for _ in range(GRID_LEN)]
    done = False
    
    for i in range(GRID_LEN):
        count = 0
        for j in range(GRID_LEN):
            if mat[i][j] != 0:
                new_mat[i][count] = mat[i][j]
                if j != count:
                    done = True
                count += 1
    
    return new_mat, done

def merge(mat, done):
    """合并相同的相邻元素"""
    for i in range(GRID_LEN):
        for j in range(GRID_LEN - 1):
            if mat[i][j] == mat[i][j + 1] and mat[i][j] != 0:
                mat[i][j] *= 2
                mat[i][j + 1] = 0
                done = True
    return mat, done

def up(game):
    """向上移动"""
    game = transpose(game)
    game, done = cover_up(game)
    game, done = merge(game, done)
    game = cover_up(game)[0]
    game = transpose(game)
    return game, done

def down(game):
    """向下移动"""
    game = reverse(transpose(game))
    game, done = cover_up(game)
    game, done = merge(game, done)
    game = cover_up(game)[0]
    game = transpose(reverse(game))
    return game, done

def left(game):
    """向左移动"""
    game, done = cover_up(game)
    game, done = merge(game, done)
    game = cover_up(game)[0]
    return game, done

def right(game):
    """向右移动"""
    game = reverse(game)
    game, done = cover_up(game)
    game, done = merge(game, done)
    game = cover_up(game)[0]
    game = reverse(game)
    return game, done

# ==================== DISPLAY FUNCTIONS ====================

def clear_screen():
    """清屏"""
    os.system('cls' if platform.system() == 'Windows' else 'clear')

def print_matrix(mat, score=0, moves=0):
    """打印游戏矩阵"""
    clear_screen()
    
    # 打印标题和信息
    print(f"{Colors.BOLD}🎮 2048 Console Game 🎮{Colors.RESET}")
    print(f"Score: {score}  |  Moves: {moves}")
    print(f"目标: 合并数字方块达到 {Colors.BOLD}2048{Colors.RESET}!")
    print()
    
    # 打印游戏矩阵
    print("┌" + "─" * 25 + "┐")
    
    for i, row in enumerate(mat):
        print("│", end="")
        for j, num in enumerate(row):
            if num == 0:
                cell_text = "   "
                color = Colors.COLORS[0]
            else:
                cell_text = f"{num:^3}"
                color = Colors.COLORS.get(num, Colors.COLORS[2048])
            
            print(f"{color} {cell_text} {Colors.RESET}", end="")
            if j < len(row) - 1:
                print("│", end="")
        print(" │")
        
        if i < len(mat) - 1:
            print("├" + "─" * 25 + "┤")
    
    print("└" + "─" * 25 + "┘")
    print()

def print_controls():
    """打印控制说明"""
    print(f"{Colors.BOLD}控制说明:{Colors.RESET}")
    print("↑↓←→ 或 WASD - 移动方块")
    print("Q/ESC - 退出游戏")
    print("R - 重新开始")
    print("H - 显示帮助")
    print()

def calculate_score(matrix):
    """计算当前分数（所有非零数字的和）"""
    return sum(sum(row) for row in matrix)

# ==================== MAIN GAME CLASS ====================

class Console2048:
    def __init__(self):
        self.matrix = new_game(GRID_LEN)
        self.score = 0
        self.moves = 0
        self.game_over = False
        self.won = False
        
        self.commands = {
            'UP': up,
            'DOWN': down,
            'LEFT': left,
            'RIGHT': right,
            'W': up,
            'S': down,
            'A': left,
            'D': right,
        }
    
    def play(self):
        """主游戏循环"""
        print(f"{Colors.BOLD}欢迎来到 2048 控制台版本!{Colors.RESET}")
        print("按任意键开始游戏...")
        get_key()
        
        while not self.game_over:
            self.score = calculate_score(self.matrix)
            print_matrix(self.matrix, self.score, self.moves)
            
            state = game_state(self.matrix)
            
            if state == 'win' and not self.won:
                print(f"{Colors.BOLD}🎉 恭喜! 你达到了 2048! 🎉{Colors.RESET}")
                print("你可以继续游戏争取更高分数，或按 Q 退出")
                self.won = True
            elif state == 'lose':
                print(f"{Colors.BOLD}😢 游戏结束! 没有更多可行的移动了 😢{Colors.RESET}")
                print(f"最终分数: {self.score}")
                print("按 R 重新开始，或按 Q 退出")
                self.handle_game_over()
                continue
            
            print_controls()
            print("请输入移动方向: ", end="", flush=True)
            
            try:
                key = get_key()
                self.handle_input(key)
            except KeyboardInterrupt:
                break
        
        print(f"\n{Colors.BOLD}感谢游戏! 再见! 👋{Colors.RESET}")
    
    def handle_input(self, key):
        """处理用户输入"""
        key = key.upper()
        
        if key == 'Q' or key == 'ESC':
            self.game_over = True
        elif key == 'R':
            self.restart_game()
        elif key == 'H':
            self.show_help()
        elif key in self.commands:
            new_matrix, moved = self.commands[key](self.matrix)
            if moved:
                self.matrix = add_two(new_matrix)
                self.moves += 1
        else:
            print(f"\n无效的输入: {key}")
            print("按任意键继续...")
            get_key()
    
    def handle_game_over(self):
        """处理游戏结束状态"""
        while True:
            key = get_key().upper()
            if key == 'R':
                self.restart_game()
                break
            elif key == 'Q' or key == 'ESC':
                self.game_over = True
                break
    
    def restart_game(self):
        """重新开始游戏"""
        self.matrix = new_game(GRID_LEN)
        self.score = 0
        self.moves = 0
        self.won = False
        print("游戏已重新开始!")
    
    def show_help(self):
        """显示帮助信息"""
        clear_screen()
        print(f"{Colors.BOLD}=== 2048 游戏帮助 ==={Colors.RESET}")
        print()
        print(f"{Colors.BOLD}游戏目标:{Colors.RESET}")
        print("合并相同数字的方块，目标是创造出数字为 2048 的方块！")
        print()
        print(f"{Colors.BOLD}游戏规则:{Colors.RESET}")
        print("• 使用方向键或 WASD 移动所有方块")
        print("• 当两个相同数字的方块碰撞时，它们会合并成一个")
        print("• 每次移动后，会随机在空位置生成一个新的 2")
        print("• 当无法移动时游戏结束")
        print()
        print(f"{Colors.BOLD}评分系统:{Colors.RESET}")
        print("分数是所有方块数字的总和")
        print()
        print(f"{Colors.BOLD}控制键:{Colors.RESET}")
        print("↑↓←→ 或 WASD - 移动方块")
        print("Q/ESC - 退出游戏")
        print("R - 重新开始")
        print("H - 显示此帮助")
        print()
        print("按任意键返回游戏...")
        get_key()

# ==================== MAIN FUNCTION ====================

def main():
    """主函数"""
    try:
        # 检查终端是否支持ANSI颜色
        if platform.system() == 'Windows':
            # 在Windows上启用ANSI转义序列支持
            os.system('color')
        
        game = Console2048()
        game.play()
        
    except Exception as e:
        print(f"游戏出现错误: {e}")
        print("请确保你的终端支持ANSI颜色代码")
        input("按Enter键退出...")

if __name__ == '__main__':
    main() 