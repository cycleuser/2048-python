import sys
import random
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout, 
                               QLabel, QVBoxLayout, QHBoxLayout, QFrame)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QKeyEvent, QPalette
import logic
import constants as c

def gen():
    return random.randint(0, c.GRID_LEN - 1)

class GameGrid(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle('2048')
        self.setMinimumSize(600, 600)
        
        # 初始化游戏状态
        self.matrix = logic.new_game(c.GRID_LEN)
        self.history_matrixs = []
        self.grid_cells = []
        
        # 设置键盘映射
        self.commands = {
            Qt.Key.Key_Up: logic.up,
            Qt.Key.Key_Down: logic.down,
            Qt.Key.Key_Left: logic.left,
            Qt.Key.Key_Right: logic.right,
            Qt.Key.Key_W: logic.up,
            Qt.Key.Key_S: logic.down,
            Qt.Key.Key_A: logic.left,
            Qt.Key.Key_D: logic.right,
                         Qt.Key.Key_I: logic.up,
             Qt.Key.Key_K: logic.down,
             Qt.Key.Key_J: logic.left,
             Qt.Key.Key_L: logic.right,
        }
        
        self.init_ui()
        self.update_grid_cells()
        
    def init_ui(self):
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 创建游戏网格容器
        self.game_container = QFrame()
        self.game_container.setFixedSize(500, 500)  # 固定正方形大小
        self.game_container.setStyleSheet(f"background-color: {c.BACKGROUND_COLOR_GAME}; border-radius: 6px;")
        
        # 创建网格布局
        grid_layout = QGridLayout(self.game_container)
        grid_layout.setSpacing(c.GRID_PADDING)
        grid_layout.setContentsMargins(c.GRID_PADDING, c.GRID_PADDING, c.GRID_PADDING, c.GRID_PADDING)
        
        # 创建网格单元格
        cell_size = (500 - c.GRID_PADDING * (c.GRID_LEN + 1)) // c.GRID_LEN
        
        for i in range(c.GRID_LEN):
            grid_row = []
            for j in range(c.GRID_LEN):
                cell = QLabel()
                cell.setFixedSize(cell_size, cell_size)
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setStyleSheet(f"""
                    background-color: {c.BACKGROUND_COLOR_CELL_EMPTY};
                    border-radius: 3px;
                    color: {c.CELL_COLOR_DICT.get(2, '#776e65')};
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
        cell_size = (size - c.GRID_PADDING * (c.GRID_LEN + 1)) // c.GRID_LEN
        font_size = max(12, cell_size // 4)  # 根据单元格大小调整字体
        
        for i in range(c.GRID_LEN):
            for j in range(c.GRID_LEN):
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
        for i in range(c.GRID_LEN):
            for j in range(c.GRID_LEN):
                new_number = self.matrix[i][j]
                cell = self.grid_cells[i][j]
                
                if new_number == 0:
                    cell.setText("")
                    bg_color = c.BACKGROUND_COLOR_CELL_EMPTY
                    text_color = c.CELL_COLOR_DICT.get(2, '#776e65')
                else:
                    cell.setText(str(new_number))
                    bg_color = c.BACKGROUND_COLOR_DICT.get(new_number, c.BACKGROUND_COLOR_CELL_EMPTY)
                    text_color = c.CELL_COLOR_DICT.get(new_number, '#776e65')
                
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
                self.matrix = logic.add_two(new_matrix)
                self.history_matrixs.append(self.matrix.copy())
                self.update_grid_cells()
                
                game_state = logic.game_state(self.matrix)
                if game_state == 'win':
                    self.show_game_result("You", "Win!")
                elif game_state == 'lose':
                    self.show_game_result("You", "Lose!")
    
    def show_game_result(self, text1, text2):
        """显示游戏结果"""
        if c.GRID_LEN >= 2:
            self.grid_cells[1][1].setText(text1)
            self.grid_cells[1][1].setStyleSheet(f"""
                background-color: {c.BACKGROUND_COLOR_CELL_EMPTY};
                border-radius: 3px;
                color: #776e65;
                font-family: Verdana;
                font-size: 20px;
                font-weight: bold;
            """)
            if c.GRID_LEN >= 3:
                self.grid_cells[1][2].setText(text2)
                self.grid_cells[1][2].setStyleSheet(f"""
                    background-color: {c.BACKGROUND_COLOR_CELL_EMPTY};
                    border-radius: 3px;
                    color: #776e65;
                    font-family: Verdana;
                    font-size: 20px;
                    font-weight: bold;
                """)

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("2048")
    
    game = GameGrid()
    game.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()