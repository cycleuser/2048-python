#!/usr/bin/env python3
"""
2048 Game - PySide6 Version
Complete standalone implementation with no external file dependencies
"""

import sys
import random
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout, 
                               QLabel, QVBoxLayout, QHBoxLayout, QFrame)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QKeyEvent, QPalette

# ==================== CONSTANTS ====================
SIZE = 400
GRID_LEN = 4
GRID_PADDING = 10

BACKGROUND_COLOR_GAME = "#92877d"
BACKGROUND_COLOR_CELL_EMPTY = "#9e948a"

BACKGROUND_COLOR_DICT = {
    2:      "#eee4da",
    4:      "#ede0c8",
    8:      "#f2b179",
    16:     "#f59563",
    32:     "#f67c5f",
    64:     "#f65e3b",
    128:    "#edcf72",
    256:    "#edcc61",
    512:    "#edc850",
    1024:   "#edc53f",
    2048:   "#edc22e",
    4096:   "#eee4da",
    8192:   "#edc22e",
    16384:  "#f2b179",
    32768:  "#f59563",
    65536:  "#f67c5f",
}

CELL_COLOR_DICT = {
    2:      "#776e65",
    4:      "#776e65",
    8:      "#f9f6f2",
    16:     "#f9f6f2",
    32:     "#f9f6f2",
    64:     "#f9f6f2",
    128:    "#f9f6f2",
    256:    "#f9f6f2",
    512:    "#f9f6f2",
    1024:   "#f9f6f2",
    2048:   "#f9f6f2",
    4096:   "#776e65",
    8192:   "#f9f6f2",
    16384:  "#776e65",
    32768:  "#776e65",
    65536:  "#f9f6f2",
}

# ==================== GAME LOGIC ====================

def new_game(n):
    """Create a new game matrix with two initial tiles"""
    matrix = []
    for i in range(n):
        matrix.append([0] * n)
    matrix = add_two(matrix)
    matrix = add_two(matrix)
    return matrix

def add_two(mat):
    """Add a new '2' tile to a random empty position"""
    a = random.randint(0, len(mat)-1)
    b = random.randint(0, len(mat)-1)
    while mat[a][b] != 0:
        a = random.randint(0, len(mat)-1)
        b = random.randint(0, len(mat)-1)
    mat[a][b] = 2
    return mat

def game_state(mat):
    """Check current game state: 'win', 'lose', or 'not over'"""
    # check for win cell
    for i in range(len(mat)):
        for j in range(len(mat[0])):
            if mat[i][j] == 2048:
                return 'win'
    # check for any zero entries
    for i in range(len(mat)):
        for j in range(len(mat[0])):
            if mat[i][j] == 0:
                return 'not over'
    # check for same cells that touch each other
    for i in range(len(mat)-1):
        for j in range(len(mat[0])-1):
            if mat[i][j] == mat[i+1][j] or mat[i][j+1] == mat[i][j]:
                return 'not over'
    for k in range(len(mat)-1):  # to check the left/right entries on the last row
        if mat[len(mat)-1][k] == mat[len(mat)-1][k+1]:
            return 'not over'
    for j in range(len(mat)-1):  # check up/down entries on last column
        if mat[j][len(mat)-1] == mat[j+1][len(mat)-1]:
            return 'not over'
    return 'lose'

def reverse(mat):
    """Reverse each row of the matrix"""
    new = []
    for i in range(len(mat)):
        new.append([])
        for j in range(len(mat[0])):
            new[i].append(mat[i][len(mat[0])-j-1])
    return new

def transpose(mat):
    """Transpose the matrix"""
    new = []
    for i in range(len(mat[0])):
        new.append([])
        for j in range(len(mat)):
            new[i].append(mat[j][i])
    return new

def cover_up(mat):
    """Move all tiles to the left (compress)"""
    new = []
    for j in range(GRID_LEN):
        partial_new = []
        for i in range(GRID_LEN):
            partial_new.append(0)
        new.append(partial_new)
    done = False
    for i in range(GRID_LEN):
        count = 0
        for j in range(GRID_LEN):
            if mat[i][j] != 0:
                new[i][count] = mat[i][j]
                if j != count:
                    done = True
                count += 1
    return new, done

def merge(mat, done):
    """Merge adjacent tiles with the same value"""
    for i in range(GRID_LEN):
        for j in range(GRID_LEN-1):
            if mat[i][j] == mat[i][j+1] and mat[i][j] != 0:
                mat[i][j] *= 2
                mat[i][j+1] = 0
                done = True
    return mat, done

def up(game):
    """Move tiles up"""
    print("up")
    game = transpose(game)
    game, done = cover_up(game)
    game, done = merge(game, done)
    game = cover_up(game)[0]
    game = transpose(game)
    return game, done

def down(game):
    """Move tiles down"""
    print("down")
    game = reverse(transpose(game))
    game, done = cover_up(game)
    game, done = merge(game, done)
    game = cover_up(game)[0]
    game = transpose(reverse(game))
    return game, done

def left(game):
    """Move tiles left"""
    print("left")
    game, done = cover_up(game)
    game, done = merge(game, done)
    game = cover_up(game)[0]
    return game, done

def right(game):
    """Move tiles right"""
    print("right")
    game = reverse(game)
    game, done = cover_up(game)
    game, done = merge(game, done)
    game = cover_up(game)[0]
    game = reverse(game)
    return game, done

# ==================== GUI IMPLEMENTATION ====================

def gen():
    """Generate random grid position"""
    return random.randint(0, GRID_LEN - 1)

class GameGrid(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle('2048')
        self.setMinimumSize(600, 600)
        
        # 初始化游戏状态
        self.matrix = new_game(GRID_LEN)
        self.history_matrixs = []
        self.grid_cells = []
        
        # 设置键盘映射
        self.commands = {
            Qt.Key.Key_Up: up,
            Qt.Key.Key_Down: down,
            Qt.Key.Key_Left: left,
            Qt.Key.Key_Right: right,
            Qt.Key.Key_W: up,
            Qt.Key.Key_S: down,
            Qt.Key.Key_A: left,
            Qt.Key.Key_D: right,
            Qt.Key.Key_I: up,
            Qt.Key.Key_K: down,
            Qt.Key.Key_J: left,
            Qt.Key.Key_L: right,
        }
        
        self.init_ui()
        self.update_grid_cells()
        
    def init_ui(self):
        """Initialize the user interface"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 创建游戏网格容器
        self.game_container = QFrame()
        self.game_container.setFixedSize(500, 500)  # 固定正方形大小
        self.game_container.setStyleSheet(f"background-color: {BACKGROUND_COLOR_GAME}; border-radius: 6px;")
        
        # 创建网格布局
        grid_layout = QGridLayout(self.game_container)
        grid_layout.setSpacing(GRID_PADDING)
        grid_layout.setContentsMargins(GRID_PADDING, GRID_PADDING, GRID_PADDING, GRID_PADDING)
        
        # 创建网格单元格
        cell_size = (500 - GRID_PADDING * (GRID_LEN + 1)) // GRID_LEN
        
        for i in range(GRID_LEN):
            grid_row = []
            for j in range(GRID_LEN):
                cell = QLabel()
                cell.setFixedSize(cell_size, cell_size)
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setStyleSheet(f"""
                    background-color: {BACKGROUND_COLOR_CELL_EMPTY};
                    border-radius: 3px;
                    color: {CELL_COLOR_DICT.get(2, '#776e65')};
                    font-family: Verdana;
                    font-size: 24px;
                    font-weight: bold;
                """)
                grid_layout.addWidget(cell, i, j)
                grid_row.append(cell)
            self.grid_cells.append(grid_row)
        
        main_layout.addWidget(self.game_container)
        
        # 添加说明文字
        instructions = QLabel("使用方向键或WASD移动，ESC退出，B撤销，F11全屏")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setStyleSheet("color: #776e65; font-size: 14px; margin: 20px;")
        main_layout.addWidget(instructions)
        
        # 设置窗口背景
        self.setStyleSheet("background-color: #faf8ef;")
        
    def resizeEvent(self, event):
        """窗口大小改变时保持游戏区域为正方形"""
        super().resizeEvent(event)
        
        # 计算可用空间
        available_width = event.size().width() - 100  # 留一些边距
        available_height = event.size().height() - 200  # 为说明文字留空间
        
        # 选择较小的尺寸以保持正方形
        size = min(available_width, available_height, 600)  # 最大600px
        size = max(size, 300)  # 最小300px
        
        self.game_container.setFixedSize(size, size)
        
        # 重新计算单元格大小
        cell_size = (size - GRID_PADDING * (GRID_LEN + 1)) // GRID_LEN
        font_size = max(12, cell_size // 4)  # 根据单元格大小调整字体
        
        for i in range(GRID_LEN):
            for j in range(GRID_LEN):
                self.grid_cells[i][j].setFixedSize(cell_size, cell_size)
                current_style = self.grid_cells[i][j].styleSheet()
                # 更新字体大小
                new_style = current_style.replace(
                    f"font-size: {current_style.split('font-size: ')[1].split('px')[0]}px",
                    f"font-size: {font_size}px"
                ) if "font-size:" in current_style else current_style + f"font-size: {font_size}px;"
                self.grid_cells[i][j].setStyleSheet(new_style)
        
    def update_grid_cells(self):
        """更新网格单元格显示"""
        for i in range(GRID_LEN):
            for j in range(GRID_LEN):
                new_number = self.matrix[i][j]
                cell = self.grid_cells[i][j]
                
                if new_number == 0:
                    cell.setText("")
                    bg_color = BACKGROUND_COLOR_CELL_EMPTY
                    text_color = CELL_COLOR_DICT.get(2, '#776e65')
                else:
                    cell.setText(str(new_number))
                    bg_color = BACKGROUND_COLOR_DICT.get(new_number, BACKGROUND_COLOR_CELL_EMPTY)
                    text_color = CELL_COLOR_DICT.get(new_number, '#776e65')
                
                # 获取当前字体大小
                current_style = cell.styleSheet()
                font_size = 24
                if "font-size:" in current_style:
                    try:
                        font_size = int(current_style.split('font-size: ')[1].split('px')[0])
                    except:
                        font_size = 24
                
                cell.setStyleSheet(f"""
                    background-color: {bg_color};
                    border-radius: 3px;
                    color: {text_color};
                    font-family: Verdana;
                    font-size: {font_size}px;
                    font-weight: bold;
                """)
    
    def keyPressEvent(self, event: QKeyEvent):
        """处理键盘事件"""
        key = event.key()
        
        if key == Qt.Key.Key_Escape:
            self.close()
        elif key == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        elif key == Qt.Key.Key_B and len(self.history_matrixs) > 1:
            self.matrix = self.history_matrixs.pop()
            self.update_grid_cells()
            print('back on step total step:', len(self.history_matrixs))
        elif key in self.commands:
            new_matrix, done = self.commands[key](self.matrix)
            if done:
                self.matrix = add_two(new_matrix)
                self.history_matrixs.append(self.matrix.copy())
                self.update_grid_cells()
                
                game_state_result = game_state(self.matrix)
                if game_state_result == 'win':
                    # self.show_game_result("You", "Win!")
                    pass
                elif game_state_result == 'lose':
                    self.show_game_result("You", "Lose!")
    
    def show_game_result(self, text1, text2):
        """显示游戏结果"""
        if GRID_LEN >= 2:
            self.grid_cells[1][1].setText(text1)
            self.grid_cells[1][1].setStyleSheet(f"""
                background-color: {BACKGROUND_COLOR_CELL_EMPTY};
                border-radius: 3px;
                color: #776e65;
                font-family: Verdana;
                font-size: 20px;
                font-weight: bold;
            """)
            if GRID_LEN >= 3:
                self.grid_cells[1][2].setText(text2)
                self.grid_cells[1][2].setStyleSheet(f"""
                    background-color: {BACKGROUND_COLOR_CELL_EMPTY};
                    border-radius: 3px;
                    color: #776e65;
                    font-family: Verdana;
                    font-size: 20px;
                    font-weight: bold;
                """)

# ==================== MAIN APPLICATION ====================

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("2048")
    
    game = GameGrid()
    game.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 