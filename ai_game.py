#!/usr/bin/env python3
"""
2048 AI Game - PySide6 Version with Ollama Integration
Enhanced version with AI player capabilities and game statistics
"""

import sys
import random
import time
import json
import copy
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, 
    QLabel, QVBoxLayout, QHBoxLayout, QFrame, QPushButton,
    QComboBox, QSpinBox, QTextEdit, QDialog,
    QDialogButtonBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QKeyEvent

try:
    import ollama
except ImportError:
    ollama = None

# ==================== CONSTANTS ====================
GRID_LEN = 4
GRID_PADDING = 10
BACKGROUND_COLOR_GAME = "#92877d"
BACKGROUND_COLOR_CELL_EMPTY = "#9e948a"

BACKGROUND_COLOR_DICT = {
    2: "#eee4da", 4: "#ede0c8", 8: "#f2b179", 16: "#f59563",
    32: "#f67c5f", 64: "#f65e3b", 128: "#edcf72", 256: "#edcc61",
    512: "#edc850", 1024: "#edc53f", 2048: "#edc22e", 4096: "#eee4da",
    8192: "#edc22e", 16384: "#f2b179", 32768: "#f59563", 65536: "#f67c5f",
}

CELL_COLOR_DICT = {
    2: "#776e65", 4: "#776e65", 8: "#f9f6f2", 16: "#f9f6f2",
    32: "#f9f6f2", 64: "#f9f6f2", 128: "#f9f6f2", 256: "#f9f6f2",
    512: "#f9f6f2", 1024: "#f9f6f2", 2048: "#f9f6f2", 4096: "#776e65",
    8192: "#f9f6f2", 16384: "#776e65", 32768: "#776e65", 65536: "#f9f6f2",
}

# ==================== GAME LOGIC ====================
def new_game(n):
    matrix = [[0 for _ in range(n)] for _ in range(n)]
    matrix = add_two(matrix)
    matrix = add_two(matrix)
    return matrix

def add_two(mat):
    empty_cells = [(i, j) for i in range(len(mat)) for j in range(len(mat[0])) if mat[i][j] == 0]
    if empty_cells:
        a, b = random.choice(empty_cells)
        mat[a][b] = 2
    return mat

def game_state(mat):
    for i in range(len(mat)):
        for j in range(len(mat[0])):
            if mat[i][j] == 2048:
                return 'win'
    for i in range(len(mat)):
        for j in range(len(mat[0])):
            if mat[i][j] == 0:
                return 'not over'
    for i in range(len(mat)-1):
        for j in range(len(mat[0])-1):
            if mat[i][j] == mat[i+1][j] or mat[i][j+1] == mat[i][j]:
                return 'not over'
    for k in range(len(mat)-1):
        if mat[len(mat)-1][k] == mat[len(mat)-1][k+1]:
            return 'not over'
    for j in range(len(mat)-1):
        if mat[j][len(mat)-1] == mat[j+1][len(mat)-1]:
            return 'not over'
    return 'lose'

def reverse(mat):
    return [row[::-1] for row in mat]

def transpose(mat):
    return [[mat[j][i] for j in range(len(mat))] for i in range(len(mat[0]))]

def cover_up(mat):
    new = [[0 for _ in range(GRID_LEN)] for _ in range(GRID_LEN)]
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
    for i in range(GRID_LEN):
        for j in range(GRID_LEN-1):
            if mat[i][j] == mat[i][j+1] and mat[i][j] != 0:
                mat[i][j] *= 2
                mat[i][j+1] = 0
                done = True
    return mat, done

def up(game):
    game = transpose(game)
    game, done = cover_up(game)
    game, done = merge(game, done)
    game = cover_up(game)[0]
    game = transpose(game)
    return game, done

def down(game):
    game = reverse(transpose(game))
    game, done = cover_up(game)
    game, done = merge(game, done)
    game = cover_up(game)[0]
    game = transpose(reverse(game))
    return game, done

def left(game):
    game, done = cover_up(game)
    game, done = merge(game, done)
    game = cover_up(game)[0]
    return game, done

def right(game):
    game = reverse(game)
    game, done = cover_up(game)
    game, done = merge(game, done)
    game = cover_up(game)[0]
    game = reverse(game)
    return game, done

def calculate_score(matrix):
    return sum(sum(row) for row in matrix)

def matrix_to_string(matrix):
    return '\n'.join([' '.join([str(cell).rjust(4) for cell in row]) for row in matrix])

# ==================== AI WORKER THREAD ====================
class AIWorker(QThread):
    move_signal = Signal(str)
    error_signal = Signal(str)
    thinking_signal = Signal(str)
    
    def __init__(self, matrix, model_name, move_delay=2000):
        super().__init__()
        self.matrix = matrix
        self.model_name = model_name
        self.move_delay = move_delay
        self.running = True
        
    def run(self):
        if not ollama:
            self.error_signal.emit("Ollama not installed. Please install: pip install ollama")
            return
            
        try:
            self.thinking_signal.emit("AI thinking...")
            
            board_str = matrix_to_string(self.matrix)
            current_score = calculate_score(self.matrix)
            
            prompt = f"""
You are playing the 2048 game. Your goal is to reach the tile 2048 by combining tiles.

Current board state:
{board_str}

Current score: {current_score}

Game rules:
- Use arrow keys to move tiles: UP, DOWN, LEFT, RIGHT
- When two tiles with the same number touch, they merge into one
- Each move adds a new tile (usually 2) to the board
- The game ends when no more moves are possible

Please analyze the current board and choose the BEST move from: UP, DOWN, LEFT, RIGHT

Consider:
1. Creating larger numbers by merging tiles
2. Keeping the largest numbers in corners
3. Maintaining open spaces
4. Setting up future merges

Respond with ONLY one word: UP, DOWN, LEFT, or RIGHT
"""

            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            ai_move = response['message']['content'].strip().upper()
            
            valid_moves = ['UP', 'DOWN', 'LEFT', 'RIGHT']
            if ai_move not in valid_moves:
                for move in valid_moves:
                    if move in ai_move:
                        ai_move = move
                        break
                else:
                    ai_move = random.choice(valid_moves)
            
            self.msleep(self.move_delay)
            
            if self.running:
                self.move_signal.emit(ai_move)
                
        except Exception as e:
            self.error_signal.emit(f"AI Error: {str(e)}")
    
    def stop(self):
        self.running = False

# ==================== STATISTICS DIALOG ====================
class StatisticsDialog(QDialog):
    def __init__(self, stats, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Game Statistics")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        tabs = QTabWidget()
        
        # Game Stats Tab
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        
        stats_text = QTextEdit()
        stats_text.setReadOnly(True)
        stats_content = self.format_stats(stats)
        stats_text.setPlainText(stats_content)
        stats_layout.addWidget(stats_text)
        
        tabs.addTab(stats_tab, "Statistics")
        
        # Game History Tab
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        
        history_table = QTableWidget()
        history_table.setColumnCount(6)
        history_table.setHorizontalHeaderLabels([
            "Date", "Mode", "Score", "Time (s)", "Moves", "Max Tile"
        ])
        
        games = stats.get('games', [])
        history_table.setRowCount(len(games))
        
        for i, game in enumerate(games):
            history_table.setItem(i, 0, QTableWidgetItem(game.get('date', 'N/A')))
            history_table.setItem(i, 1, QTableWidgetItem(game.get('mode', 'N/A')))
            history_table.setItem(i, 2, QTableWidgetItem(str(game.get('score', 0))))
            history_table.setItem(i, 3, QTableWidgetItem(f"{game.get('time', 0):.1f}"))
            history_table.setItem(i, 4, QTableWidgetItem(str(game.get('moves', 0))))
            history_table.setItem(i, 5, QTableWidgetItem(str(game.get('max_tile', 0))))
        
        history_layout.addWidget(history_table)
        tabs.addTab(history_tab, "Game History")
        
        layout.addWidget(tabs)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)
    
    def format_stats(self, stats):
        total_games = len(stats.get('games', []))
        if total_games == 0:
            return "No games played yet."
        
        games = stats['games']
        
        total_score = sum(game.get('score', 0) for game in games)
        avg_score = total_score / total_games
        best_score = max(game.get('score', 0) for game in games)
        
        total_time = sum(game.get('time', 0) for game in games)
        avg_time = total_time / total_games
        
        total_moves = sum(game.get('moves', 0) for game in games)
        avg_moves = total_moves / total_games
        
        max_tiles = [game.get('max_tile', 0) for game in games]
        best_tile = max(max_tiles)
        
        wins = sum(1 for tile in max_tiles if tile >= 2048)
        win_rate = (wins / total_games) * 100
        
        human_games = [g for g in games if g.get('mode') == 'Human']
        ai_games = [g for g in games if g.get('mode', '').startswith('AI')]
        
        content = f"""OVERALL STATISTICS
==================
Total Games: {total_games}
Total Score: {total_score:,}
Average Score: {avg_score:.1f}
Best Score: {best_score:,}

Total Time Played: {total_time:.1f} seconds
Average Game Time: {avg_time:.1f} seconds

Total Moves: {total_moves}
Average Moves per Game: {avg_moves:.1f}

Best Tile Achieved: {best_tile}
Games Won (2048+): {wins}
Win Rate: {win_rate:.1f}%

GAME MODE BREAKDOWN
==================
Human Games: {len(human_games)}
AI Games: {len(ai_games)}
"""

        if ai_games:
            ai_scores = [g.get('score', 0) for g in ai_games]
            ai_avg_score = sum(ai_scores) / len(ai_scores)
            ai_best_score = max(ai_scores)
            
            content += f"""
AI PERFORMANCE
==============
AI Average Score: {ai_avg_score:.1f}
AI Best Score: {ai_best_score:,}
"""

        if human_games:
            human_scores = [g.get('score', 0) for g in human_games]
            human_avg_score = sum(human_scores) / len(human_scores)
            human_best_score = max(human_scores)
            
            content += f"""
HUMAN PERFORMANCE
================
Human Average Score: {human_avg_score:.1f}
Human Best Score: {human_best_score:,}
"""

        return content

# ==================== MODEL SELECTION DIALOG ====================
class ModelSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select AI Model")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # 标题和说明
        title = QLabel("🤖 AI Model Selection")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px; color: #2c3e50;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        instructions = QLabel(
            "Choose an Ollama model to control the 2048 game.\n"
            "Different models may have different playing strategies.\n\n"
            "📋 Requirements:\n"
            "• Ollama server must be running (ollama serve)\n"
            "• At least one model must be installed (ollama pull <model>)"
        )
        instructions.setStyleSheet("color: #555; margin: 10px; padding: 10px; background-color: #f8f9fa; border-radius: 5px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # 模型选择组
        model_group = QGroupBox("Available Models")
        model_group.setStyleSheet("QGroupBox { font-weight: bold; margin: 5px; }")
        model_layout = QVBoxLayout(model_group)
        
        # 模型下拉框
        self.model_combo = QComboBox()
        self.model_combo.setMinimumHeight(30)
        self.model_combo.setToolTip("Select an AI model to play 2048.\nDifferent models may have different strategies.")
        self.model_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QComboBox:focus {
                border-color: #4CAF50;
            }
        """)
        model_layout.addWidget(self.model_combo)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 Refresh Models")
        refresh_btn.setStyleSheet("""
            QPushButton {
                padding: 8px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_models)
        model_layout.addWidget(refresh_btn)
        
        layout.addWidget(model_group)
        
        # AI设置组
        settings_group = QGroupBox("AI Settings")
        settings_group.setStyleSheet("QGroupBox { font-weight: bold; margin: 5px; }")
        settings_layout = QVBoxLayout(settings_group)
        
        delay_layout = QHBoxLayout()
        delay_label = QLabel("⏱️ Move Delay:")
        delay_label.setMinimumWidth(100)
        delay_layout.addWidget(delay_label)
        
        self.delay_spin = QSpinBox()
        self.delay_spin.setMinimum(500)
        self.delay_spin.setMaximum(10000)
        self.delay_spin.setValue(2000)
        self.delay_spin.setSuffix(" ms")
        self.delay_spin.setToolTip("Time between AI moves.\n500ms = very fast\n2000ms = comfortable to watch\n5000ms+ = slow, easy to analyze")
        self.delay_spin.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
        """)
        delay_layout.addWidget(self.delay_spin)
        
        delay_help = QLabel("(Longer delay = easier to observe AI thinking)")
        delay_help.setStyleSheet("color: #666; font-style: italic; font-size: 11px;")
        
        settings_layout.addLayout(delay_layout)
        settings_layout.addWidget(delay_help)
        
        layout.addWidget(settings_group)
        
        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-style: italic; margin: 5px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("▶️ Start AI")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("❌ Cancel")
        buttons.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton[text*="Start"] {
                background-color: #27ae60;
                color: white;
                border: none;
            }
            QPushButton[text*="Start"]:hover {
                background-color: #229954;
            }
            QPushButton[text*="Cancel"] {
                background-color: #e74c3c;
                color: white;
                border: none;
            }
            QPushButton[text*="Cancel"]:hover {
                background-color: #c0392b;
            }
        """)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.selected_model = None
        self.move_delay = 2000
        
        # 现在所有UI组件都已创建完成，可以安全地刷新模型列表
        self.refresh_models()
    
    def refresh_models(self):
        self.model_combo.clear()
        
        # 安全地设置状态标签（如果存在的话）
        if hasattr(self, 'status_label'):
            self.status_label.setText("🔄 Loading models...")
        
        if not ollama:
            self.model_combo.addItem("❌ Ollama not installed")
            if hasattr(self, 'status_label'):
                self.status_label.setText("❌ Ollama Python package not found")
            return
        
        try:
            models = ollama.list()
            
            if models and 'models' in models and len(models['models']) > 0:
                for model in models['models']:
                    # 获取完整的模型名称，包括标签
                    model_name = model.get('name', 'Unknown Model')
                    # 也获取模型大小信息
                    size_gb = model.get('size', 0) / (1024**3)
                    display_name = f"🤖 {model_name} ({size_gb:.1f}GB)"
                    self.model_combo.addItem(display_name, model_name)
                    
                if hasattr(self, 'status_label'):
                    self.status_label.setText(f"✅ Found {len(models['models'])} available models")
                print(f"Found {len(models['models'])} models")
            else:
                self.model_combo.addItem("📦 No models found")
                if hasattr(self, 'status_label'):
                    self.status_label.setText("⚠️ No models installed. Run: ollama pull llama2")
                
        except Exception as e:
            self.model_combo.addItem(f"❌ Connection error: {str(e)}")
            if hasattr(self, 'status_label'):
                self.status_label.setText("❌ Cannot connect to Ollama server. Is it running?")
            print(f"Error loading models: {e}")
    
    def accept(self):
        current_text = self.model_combo.currentText()
        current_data = self.model_combo.currentData()
        
        if (current_text and 
            not current_text.startswith(("❌", "📦", "🔄")) and
            current_data):
            # 使用存储在数据中的实际模型名称
            self.selected_model = current_data
            self.move_delay = self.delay_spin.value()
            if hasattr(self, 'status_label'):
                self.status_label.setText(f"✅ Starting AI with {self.selected_model}")
            super().accept()
        else:
            # 显示详细的错误信息
            error_msg = "⚠️ Cannot start AI\n\n"
            
            if current_text.startswith("❌"):
                if "not installed" in current_text:
                    error_msg += "Ollama Python package is not installed.\n\n"
                    error_msg += "📥 To install: pip install ollama"
                elif "Connection error" in current_text:
                    error_msg += "Cannot connect to Ollama server.\n\n"
                    error_msg += "🚀 To start Ollama: ollama serve"
                else:
                    error_msg += "Ollama connection error.\n\n"
                    error_msg += "Check if Ollama is running properly."
            elif current_text.startswith("📦"):
                error_msg += "No AI models are installed.\n\n"
                error_msg += "📦 To install models:\n"
                error_msg += "• ollama pull llama2 (General purpose)\n"
                error_msg += "• ollama pull mistral (Faster)\n"
                error_msg += "• ollama pull codellama (Logic-focused)"
            else:
                error_msg += "Please select a valid AI model.\n\n"
                error_msg += "💡 Troubleshooting:\n"
                error_msg += "1. Start Ollama: ollama serve\n"
                error_msg += "2. Install a model: ollama pull llama2\n"
                error_msg += "3. Click 'Refresh Models'"
            
            QMessageBox.warning(self, "AI Startup Error", error_msg)

# ==================== MAIN GAME WINDOW ====================
class GameGrid(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle('2048 AI Enhanced')
        self.setMinimumSize(800, 900)
        
        # Game state
        self.matrix = new_game(GRID_LEN)
        self.history_matrixs = []
        self.grid_cells = []
        
        # AI state
        self.ai_mode = False
        self.ai_worker = None
        self.selected_model = None
        self.move_delay = 2000
        
        # Game statistics
        self.start_time = None
        self.moves_count = 0
        self.game_mode = "Human"
        self.stats = self.load_stats()
        
        # Keyboard commands
        self.commands = {
            Qt.Key.Key_Up: up,
            Qt.Key.Key_Down: down,
            Qt.Key.Key_Left: left,
            Qt.Key.Key_Right: right,
            Qt.Key.Key_W: up,
            Qt.Key.Key_S: down,
            Qt.Key.Key_A: left,
            Qt.Key.Key_D: right,
        }
        
        self.init_ui()
        self.update_grid_cells()
        self.start_new_game()
    
    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Control panel
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        
        # Game info
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("color: black; font-size: 18px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(self.info_label)
        
        # Game grid container
        self.game_container = QFrame()
        self.game_container.setFixedSize(500, 500)
        self.game_container.setStyleSheet(f"background-color: {BACKGROUND_COLOR_GAME}; border-radius: 6px;")
        
        # Grid layout
        grid_layout = QGridLayout(self.game_container)
        grid_layout.setSpacing(GRID_PADDING)
        grid_layout.setContentsMargins(GRID_PADDING, GRID_PADDING, GRID_PADDING, GRID_PADDING)
        
        # Create grid cells
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
                    color: black;
                    font-family: Verdana;
                    font-size: 24px;
                    font-weight: bold;
                """)
                grid_layout.addWidget(cell, i, j)
                grid_row.append(cell)
            self.grid_cells.append(grid_row)
        
        # 创建游戏容器的居中布局
        game_layout_wrapper = QHBoxLayout()
        game_layout_wrapper.addStretch()
        game_layout_wrapper.addWidget(self.game_container)
        game_layout_wrapper.addStretch()
        main_layout.addLayout(game_layout_wrapper)
        
        # Instructions
        instructions = QLabel(
            "🎮 人类游戏: 方向键/WASD移动 | 🤖 AI游戏: 选择模型后点击'开始AI' | ESC/空格: 停止AI | F11: 全屏"
        )
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setStyleSheet("color: black; font-size: 14px; margin: 10px; font-weight: bold;")
        main_layout.addWidget(instructions)
        
        # Status bar
        self.status_label = QLabel("准备就绪 - 选择AI模型或开始手动游戏")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: black; font-size: 16px; margin: 10px; font-weight: bold;")
        main_layout.addWidget(self.status_label)
        
        self.setStyleSheet("background-color: #faf8ef;")
    
    def create_control_panel(self):
        """Create the control panel with AI model selection and controls"""
        panel = QFrame()
        panel.setFixedHeight(200)
        panel.setStyleSheet("""
            QFrame { 
                background-color: #f5f5f5; 
                border: 1px solid #ccc;
                border-radius: 5px; 
            }
            QLabel { 
                color: black; 
                font-weight: bold; 
                font-size: 14px;
            }
            QPushButton { 
                background-color: #4a90e2; 
                color: white; 
                border: none; 
                border-radius: 4px; 
                padding: 8px 16px; 
                font-weight: bold; 
                font-size: 14px;
            }
            QPushButton:hover { background-color: #357abd; }
            QPushButton:disabled { background-color: #ccc; color: #666; }
            QComboBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                color: black;
                font-size: 14px;
                font-weight: bold;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #ccc;
                selection-background-color: #4a90e2;
                selection-color: white;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #f0f0f0;
                width: 20px;
            }
            QComboBox::down-arrow {
                border: 2px solid black;
                width: 3px;
                height: 3px;
                background-color: black;
            }
            QSpinBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                color: black;
                font-size: 14px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 第一行：AI模型选择
        first_row = QHBoxLayout()
        first_row.setSpacing(10)
        
        # 模型选择
        model_label = QLabel("AI模型:")
        model_label.setFixedWidth(80)
        first_row.addWidget(model_label)
        
        self.model_combo = QComboBox()
        self.model_combo.setFixedHeight(35)
        self.model_combo.setMinimumWidth(300)
        first_row.addWidget(self.model_combo)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(35, 35)
        refresh_btn.clicked.connect(self.refresh_models)
        first_row.addWidget(refresh_btn)
        
        # 速度设置
        speed_label = QLabel("速度:")
        speed_label.setFixedWidth(50)
        first_row.addWidget(speed_label)
        
        self.speed_spin = QSpinBox()
        self.speed_spin.setFixedSize(100, 35)
        self.speed_spin.setMinimum(500)
        self.speed_spin.setMaximum(5000)
        self.speed_spin.setValue(2000)
        self.speed_spin.setSuffix("ms")
        first_row.addWidget(self.speed_spin)
        
        first_row.addStretch()
        layout.addLayout(first_row)
        
        # 第二行：控制按钮
        second_row = QHBoxLayout()
        second_row.setSpacing(15)
        
        # AI控制按钮
        self.start_ai_btn = QPushButton("🤖 开始AI")
        self.start_ai_btn.setFixedSize(120, 40)
        self.start_ai_btn.setStyleSheet("""
            QPushButton { 
                background-color: #27ae60; 
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #229954; }
            QPushButton:disabled { background-color: #ccc; color: #666; }
        """)
        self.start_ai_btn.clicked.connect(self.start_ai_mode)
        second_row.addWidget(self.start_ai_btn)
        
        self.stop_ai_btn = QPushButton("⏹️ 停止AI")
        self.stop_ai_btn.setFixedSize(120, 40)
        self.stop_ai_btn.setStyleSheet("""
            QPushButton { 
                background-color: #dc3545; 
                color: white;
                border: 2px solid #dc3545;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { 
                background-color: #c82333; 
                border-color: #c82333;
                transform: scale(1.05);
            }
            QPushButton:disabled { 
                background-color: #ccc; 
                color: #666; 
                border-color: #ccc;
            }
        """)
        self.stop_ai_btn.clicked.connect(self.stop_ai_mode)
        self.stop_ai_btn.setEnabled(False)
        second_row.addWidget(self.stop_ai_btn)
        
        # 间隔
        second_row.addSpacing(30)
        
        # 游戏控制按钮
        new_game_btn = QPushButton("🔄 新游戏")
        new_game_btn.setFixedSize(120, 40)
        new_game_btn.clicked.connect(self.start_new_game)
        second_row.addWidget(new_game_btn)
        
        stats_btn = QPushButton("📊 统计")
        stats_btn.setFixedSize(120, 40)
        stats_btn.clicked.connect(self.show_statistics)
        second_row.addWidget(stats_btn)
        
        second_row.addStretch()
        layout.addLayout(second_row)
        
        # 初始化模型列表
        self.refresh_models()
        
        return panel

    def start_ai_mode(self):
        """Start AI playing mode"""
        # 获取选择的模型
        current_text = self.model_combo.currentText()
        current_data = self.model_combo.currentData()
        
        # 检查是否有有效的模型选择
        if (not current_text or 
            current_text.startswith(("❌", "📦", "🔄")) or
            not current_data):
            # 显示错误信息
            self.show_model_error(current_text)
            return
        
        # 开始AI模式
        self.selected_model = current_data
        self.move_delay = self.speed_spin.value()
        
        self.ai_mode = True
        self.game_mode = f"AI ({self.selected_model})"
        self.start_ai_btn.setEnabled(False)
        self.stop_ai_btn.setEnabled(True)
        self.model_combo.setEnabled(False)
        self.speed_spin.setEnabled(False)
        
        self.status_label.setText(f"🤖 AI ({self.selected_model}) 正在思考...")
        self.make_ai_move()
    
    def stop_ai_mode(self):
        """Stop AI playing mode"""
        self.ai_mode = False
        if self.ai_worker:
            self.ai_worker.stop()
            self.ai_worker.wait()
            self.ai_worker = None
        
        self.game_mode = "Human"
        self.start_ai_btn.setEnabled(True)
        self.stop_ai_btn.setEnabled(False)
        self.model_combo.setEnabled(True)
        self.speed_spin.setEnabled(True)
        self.status_label.setText("AI已停止 - 人类控制")
    
    def refresh_models(self):
        """刷新可用的AI模型列表"""
        self.model_combo.clear()
        
        if not ollama:
            self.model_combo.addItem("❌ Ollama未安装", None)
            return
        
        try:
            models = ollama.list()
            print(f"Debug: Raw models data: {models}")  # 调试信息
            
            if models and 'models' in models and len(models['models']) > 0:
                model_list = []
                
                for model in models['models']:
                    print(f"Debug: Model data: {model}")  # 调试每个模型的数据
                    
                    # 尝试多种可能的字段名
                    model_name = (model.get('name') or 
                                model.get('model') or 
                                model.get('id') or
                                str(model.get('digest', 'Unknown'))[:12])
                    
                    # 移除可能的':latest'后缀，使名称更简洁
                    if model_name.endswith(':latest'):
                        model_name = model_name[:-7]
                    
                    size_gb = model.get('size', 0) / (1024**3) if model.get('size') else 0
                    display_name = f"🤖 {model_name} ({size_gb:.1f}GB)"
                    
                    model_list.append((display_name, model_name))
                
                # 对模型列表按名称排序
                model_list.sort(key=lambda x: x[1].lower())
                
                # 添加排序后的模型到下拉框
                default_index = -1
                for i, (display_name, model_name) in enumerate(model_list):
                    self.model_combo.addItem(display_name, model_name)
                    
                    # 查找默认模型qwen3:0.6b
                    if 'qwen3:0.6b' in model_name.lower() or 'qwen3-0.6b' in model_name.lower():
                        default_index = i
                
                # 设置默认选择
                if default_index >= 0:
                    self.model_combo.setCurrentIndex(default_index)
                    print(f"Default model set to: {model_list[default_index][1]}")
                
                print(f"Found {len(models['models'])} AI models (sorted)")
            else:
                self.model_combo.addItem("📦 未找到模型", None)
                
        except Exception as e:
            self.model_combo.addItem(f"❌ 连接错误: {str(e)}", None)
            print(f"Error loading models: {e}")
    
    def show_model_error(self, current_text):
        """显示模型选择错误信息"""
        if current_text.startswith("❌"):
            if "未安装" in current_text:
                error_msg = "⚠️ Ollama未安装\n\n请安装Ollama:\npip install ollama"
            elif "连接错误" in current_text:
                error_msg = "⚠️ 无法连接到Ollama服务器\n\n请启动Ollama服务:\nollama serve"
            else:
                error_msg = "⚠️ Ollama连接问题\n\n请检查Ollama是否正常运行"
        elif current_text.startswith("📦"):
            error_msg = "⚠️ 没有可用的AI模型\n\n请安装模型:\n• ollama pull llama2\n• ollama pull mistral\n• ollama pull codellama"
        else:
            error_msg = "⚠️ 请选择一个有效的AI模型\n\n如果列表为空:\n1. 启动Ollama: ollama serve\n2. 安装模型: ollama pull llama2\n3. 点击🔄刷新"
        
        QMessageBox.warning(self, "AI模型错误", error_msg)
    
    def make_ai_move(self):
        """Make an AI move"""
        if not self.ai_mode:
            return
        
        # Check if game is over
        state = game_state(self.matrix)
        if state in ['win', 'lose']:
            self.stop_ai_mode()
            return
        
        # Create AI worker
        self.ai_worker = AIWorker(copy.deepcopy(self.matrix), self.selected_model, self.move_delay)
        self.ai_worker.move_signal.connect(self.handle_ai_move)
        self.ai_worker.error_signal.connect(self.handle_ai_error)
        self.ai_worker.thinking_signal.connect(self.handle_ai_thinking)
        self.ai_worker.start()
    
    def handle_ai_move(self, move):
        """Handle AI move result"""
        move_map = {
            'UP': up,
            'DOWN': down,
            'LEFT': left,
            'RIGHT': right
        }
        
        if move in move_map:
            self.execute_move(move_map[move])
            self.status_label.setText(f"🤖 AI移动: {move} | 模型: {self.selected_model}")
            
            # Continue AI play if still in AI mode and game not over
            if self.ai_mode:
                state = game_state(self.matrix)
                if state == 'not over':
                    # Schedule next move
                    QTimer.singleShot(100, self.make_ai_move)
                else:
                    self.stop_ai_mode()
    
    def handle_ai_error(self, error_msg):
        """Handle AI error"""
        self.status_label.setText(error_msg)
        self.stop_ai_mode()
        QMessageBox.warning(self, "AI Error", error_msg)
    
    def handle_ai_thinking(self, message):
        """Handle AI thinking status"""
        self.status_label.setText(f"🤖 AI正在思考... | 模型: {self.selected_model}")
    
    def execute_move(self, move_func):
        """Execute a move and update the game state"""
        new_matrix, done = move_func(copy.deepcopy(self.matrix))
        if done:
            self.matrix = add_two(new_matrix)
            self.history_matrixs.append(copy.deepcopy(self.matrix))
            self.moves_count += 1
            self.update_grid_cells()
            self.update_info()
            
            game_state_result = game_state(self.matrix)
            if game_state_result == 'win':
                self.show_game_result("You", "Win!")
                self.end_game()
            elif game_state_result == 'lose':
                self.show_game_result("Game", "Over!")
                self.end_game()
    
    def start_new_game(self):
        """Start a new game"""
        if self.ai_mode:
            self.stop_ai_mode()
        
        # Save previous game if it had moves
        if hasattr(self, 'start_time') and self.start_time and self.moves_count > 0:
            self.save_game_result()
        
        self.matrix = new_game(GRID_LEN)
        self.history_matrixs = []
        self.moves_count = 0
        self.start_time = time.time()
        self.game_mode = "Human"
        
        # 恢复控件状态
        self.start_ai_btn.setEnabled(True)
        self.stop_ai_btn.setEnabled(False)
        self.model_combo.setEnabled(True)
        self.speed_spin.setEnabled(True)
        
        self.update_grid_cells()
        self.update_info()
        self.status_label.setText("新游戏开始 - 选择模型开启AI或手动游戏")
    
    def end_game(self):
        """Handle game end"""
        if self.ai_mode:
            self.stop_ai_mode()
        
        self.save_game_result()
    
    def save_game_result(self):
        """Save the current game result to statistics"""
        if not self.start_time:
            return
        
        game_time = time.time() - self.start_time
        score = calculate_score(self.matrix)
        max_tile = max(max(row) for row in self.matrix)
        
        game_data = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'mode': self.game_mode,
            'score': score,
            'time': game_time,
            'moves': self.moves_count,
            'max_tile': max_tile
        }
        
        if 'games' not in self.stats:
            self.stats['games'] = []
        
        self.stats['games'].append(game_data)
        self.save_stats()
    
    def load_stats(self):
        """Load game statistics from file"""
        try:
            with open('game_stats.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {'games': []}
        except json.JSONDecodeError:
            return {'games': []}
    
    def save_stats(self):
        """Save game statistics to file"""
        try:
            with open('game_stats.json', 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            print(f"Error saving stats: {e}")
    
    def show_statistics(self):
        """Show statistics dialog"""
        dialog = StatisticsDialog(self.stats, self)
        dialog.exec()
    
    def update_info(self):
        """Update game info display"""
        score = calculate_score(self.matrix)
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        self.info_label.setText(
            f"Score: {score:,} | Moves: {self.moves_count} | "
            f"Time: {elapsed:.1f}s | Mode: {self.game_mode}"
        )
    
    def update_grid_cells(self):
        """Update grid cell display"""
        for i in range(GRID_LEN):
            for j in range(GRID_LEN):
                new_number = self.matrix[i][j]
                cell = self.grid_cells[i][j]
                
                if new_number == 0:
                    cell.setText("")
                    bg_color = BACKGROUND_COLOR_CELL_EMPTY
                    text_color = "black"
                else:
                    cell.setText(str(new_number))
                    bg_color = BACKGROUND_COLOR_DICT.get(new_number, BACKGROUND_COLOR_CELL_EMPTY)
                    text_color = "black"
                
                cell.setStyleSheet(f"""
                    background-color: {bg_color};
                    border-radius: 3px;
                    color: {text_color};
                    font-family: Verdana;
                    font-size: 24px;
                    font-weight: bold;
                """)
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard events"""
        key = event.key()
        
        if key == Qt.Key.Key_Escape:
            if self.ai_mode:
                # ESC键快速停止AI
                self.stop_ai_mode()
                self.status_label.setText("AI已停止 - 按ESC键停止")
            else:
                if self.moves_count > 0:
                    self.save_game_result()
                self.close()
        elif key == Qt.Key.Key_Space and self.ai_mode:
            # 空格键也可以停止AI
            self.stop_ai_mode()
            self.status_label.setText("AI已停止 - 按空格键停止")
        elif key == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        elif key == Qt.Key.Key_B and len(self.history_matrixs) > 1 and not self.ai_mode:
            self.matrix = self.history_matrixs.pop()
            self.moves_count = max(0, self.moves_count - 1)
            self.update_grid_cells()
            self.update_info()
        elif key in self.commands and not self.ai_mode:
            self.execute_move(self.commands[key])
    
    def show_game_result(self, text1, text2):
        """Display game result"""
        if GRID_LEN >= 2:
            if self.ai_mode:
                display_text1 = f"AI"
                display_text2 = text2
                result_text = f"🤖 AI游戏结束: {text2} | 模型: {self.selected_model}"
            else:
                display_text1 = text1
                display_text2 = text2
                result_text = f"🎮 游戏结束: {text2}"
            
            self.grid_cells[1][1].setText(display_text1)
            self.grid_cells[1][1].setStyleSheet(f"""
                background-color: {BACKGROUND_COLOR_CELL_EMPTY};
                border-radius: 3px;
                color: black;
                font-family: Verdana;
                font-size: 20px;
                font-weight: bold;
            """)
            if GRID_LEN >= 3:
                self.grid_cells[1][2].setText(display_text2)
                self.grid_cells[1][2].setStyleSheet(f"""
                    background-color: {BACKGROUND_COLOR_CELL_EMPTY};
                    border-radius: 3px;
                    color: black;
                    font-family: Verdana;
                    font-size: 20px;
                    font-weight: bold;
                """)
            
            self.status_label.setText(result_text)
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.ai_mode:
            self.stop_ai_mode()
        
        if self.moves_count > 0:
            self.save_game_result()
        
        event.accept()

# ==================== MAIN APPLICATION ====================
def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("2048 AI Enhanced")
    
    # Check if Ollama is available
    if not ollama:
        QMessageBox.warning(
            None, 
            "Ollama Not Found",
            "Ollama is not installed. AI features will be disabled.\n"
            "To enable AI features, install Ollama:\n"
            "pip install ollama"
        )
    
    game = GameGrid()
    game.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 