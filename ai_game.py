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
import csv
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, 
    QLabel, QVBoxLayout, QHBoxLayout, QFrame, QPushButton,
    QComboBox, QSpinBox, QTextEdit, QDialog,
    QDialogButtonBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QMessageBox, QGroupBox, QFileDialog
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

def get_valid_moves(matrix):
    """获取当前棋盘状态下的有效移动方向"""
    valid_moves = []
    
    # 测试每个方向是否会改变棋盘状态
    moves_to_test = [
        ('UP', up),
        ('DOWN', down), 
        ('LEFT', left),
        ('RIGHT', right)
    ]
    
    for move_name, move_func in moves_to_test:
        # 创建副本进行测试
        test_matrix = [row[:] for row in matrix]  # 更快的浅拷贝
        result, changed = move_func(test_matrix)
        if changed:
            valid_moves.append(move_name)
    
    return valid_moves

# ==================== AI WORKER THREAD ====================
class AIWorker(QThread):
    move_signal = Signal(str)
    error_signal = Signal(str)
    thinking_signal = Signal(str)
    
    # 简单的AI决策缓存
    _move_cache = {}
    
    def __init__(self, matrix, model_name, move_delay=2000, strategy_mode='snake'):
        super().__init__()
        self.matrix = matrix
        self.model_name = model_name
        self.move_delay = move_delay
        self.running = True
        self.strategy_mode = strategy_mode  # 添加策略模式
        
    def run(self):
        if not ollama:
            self.error_signal.emit("Ollama not installed. Please install: pip install ollama")
            return
            
        try:
            # 首先获取当前棋盘的有效移动
            valid_moves = get_valid_moves(self.matrix)
            
            if not valid_moves:
                # 没有有效移动，游戏结束
                self.error_signal.emit("No valid moves available - game over")
                return
            
            # 获取选择的策略模式
            strategy_mode = getattr(self, 'strategy_mode', 'snake')  # 默认蛇形策略
            
            # 创建包含有效移动和策略的缓存键
            board_state = tuple(tuple(row) for row in self.matrix)
            valid_moves_key = tuple(sorted(valid_moves))
            cache_key = (board_state, valid_moves_key, strategy_mode)
            
            # 检查缓存
            if cache_key in AIWorker._move_cache:
                ai_move = AIWorker._move_cache[cache_key]
                print(f"Using cached move: {ai_move} (strategy: {strategy_mode}, valid: {valid_moves})")
            else:
                # 没有缓存，需要调用AI模型
                board_str = matrix_to_string(self.matrix)
                valid_moves_str = ', '.join(valid_moves)
                
                # 分析棋盘状态并生成智能策略建议
                max_tile = max(max(row) for row in self.matrix)
                
                # 找到最大数字的位置
                max_pos = None
                for i in range(len(self.matrix)):
                    for j in range(len(self.matrix[0])):
                        if self.matrix[i][j] == max_tile:
                            max_pos = (i, j)
                            break
                    if max_pos:
                        break
                
                # 生成基于位置的策略建议
                strategy_advice = ""
                if max_pos:
                    row, col = max_pos
                    if max_tile >= 256:
                        if row >= 2 and col >= 2:  # 在右下角附近
                            strategy_advice = "Good! Keep building in bottom-right corner. "
                        else:
                            strategy_advice = "Move largest tile to bottom-right corner! "
                    elif max_tile >= 64:
                        strategy_advice = "Start moving large tiles to corners. "
                    else:
                        strategy_advice = "Build up tiles before positioning. "
                
                # 基于可用移动给出具体建议
                move_advice = ""
                if len(valid_moves) > 1:
                    if max_tile >= 128:
                        if 'RIGHT' in valid_moves and 'DOWN' in valid_moves:
                            move_advice = "Prefer RIGHT/DOWN to build corner."
                        elif 'RIGHT' in valid_moves:
                            move_advice = "RIGHT keeps corner strategy."
                        elif 'DOWN' in valid_moves:
                            move_advice = "DOWN maintains corner build."
                
                # 策略模式已在前面获取
                
                # 多策略系统 - 不同的2048游戏策略
                strategies = {
                    'snake': {
                        'name': 'Snake Pattern (Classic Optimal)',
                        'description': 'Maintain monotonic rows in snake pattern',
                        'strategy': """
OPTIMAL 2048 STRATEGY - SNAKE PATTERN:
===========================================

CORE PRINCIPLE: "SNAKE" or "MONOTONIC" FILLING
1. **CORNER DOMINANCE**: Always keep the largest tile in one corner (bottom-right preferred)
2. **SNAKE PATTERN**: Fill the board in a snake-like pattern to maintain order
   
   IDEAL BOARD LAYOUT (example with bottom-right corner):
   [  32][  64][ 128][ 256]  ← Row 2: Right-to-left decreasing (snake up)
   [ 512][1024][2048][   4]  ← Row 1: Left-to-right increasing (largest in corner)
   
   Or vertically:
   [2048][ 512][  32][   4]  ← Column 1: Top-to-bottom decreasing
   [1024][ 256][  64][   8]  ← Column 2: Bottom-to-top decreasing (snake right)

3. **MOVE PRIORITY**: RIGHT > DOWN > LEFT > UP
4. **FORBIDDEN**: Never break corner dominance or monotonic sequences
"""
                    },
                    
                    'corner_focus': {
                        'name': 'Corner Focus Strategy',
                        'description': 'Build maximum value in chosen corner with flexible patterns',
                        'strategy': """
CORNER FOCUS STRATEGY:
=====================

CORE PRINCIPLE: "FLEXIBLE CORNER BUILDING"
1. **CORNER SELECTION**: Choose and stick to one corner (any of 4 corners)
2. **VALUE CONCENTRATION**: Keep 3-4 highest values near chosen corner
3. **ADAPTIVE PATTERN**: Allow flexible patterns as long as corner is protected
4. **MERGE PRIORITY**: Always merge toward the corner
5. **MOVE PRIORITY**: Prioritize moves that build toward corner
6. **ESCAPE ROUTES**: Maintain paths for smaller tiles to escape
"""
                    },
                    
                    'edge_priority': {
                        'name': 'Edge Priority Strategy', 
                        'description': 'Build along edges before filling center',
                        'strategy': """
EDGE PRIORITY STRATEGY:
======================

CORE PRINCIPLE: "EDGE-TO-CENTER BUILDING"
1. **EDGE DOMINANCE**: Build strongest tiles along edges first
2. **PERIMETER CONTROL**: Control board perimeter before center
3. **GRADUAL INWARD**: Move from edges toward center gradually
4. **MULTIPLE FRONTS**: Can work on multiple edges simultaneously
5. **CENTER LAST**: Only fill center when edges are strong
6. **FLEXIBILITY**: More flexible than snake pattern, allows adaptation
"""
                    },
                    
                    'dynamic_adaptive': {
                        'name': 'Dynamic Adaptive Strategy',
                        'description': 'Adapt strategy based on current board state',
                        'strategy': """
DYNAMIC ADAPTIVE STRATEGY:
=========================

CORE PRINCIPLE: "SITUATIONAL ADAPTATION"
1. **STATE ANALYSIS**: Analyze current board configuration
2. **STRATEGY SWITCHING**: Change approach based on board state
3. **OPPORTUNITY BASED**: Prioritize immediate merge opportunities
4. **THREAT RESPONSE**: React to dangerous situations dynamically  
5. **PATTERN RECOGNITION**: Identify beneficial patterns and build on them
6. **FLEXIBLE GOALS**: Adjust goals based on achievable outcomes
"""
                    },
                    
                    'ai_innovation': {
                        'name': 'AI Innovation Mode',
                        'description': 'Let AI analyze and create its own optimal strategy',
                        'strategy': """
AI INNOVATION MODE:
==================

MISSION: You are a 2048 strategy researcher and innovator.

YOUR TASK:
1. **ANALYZE** the current board state deeply
2. **IDENTIFY** patterns, opportunities, and threats
3. **INNOVATE** your own strategy based on this specific situation
4. **EXPLAIN** your reasoning (internally) 
5. **EXECUTE** your chosen move

INNOVATION GUIDELINES:
- Don't just follow existing strategies blindly
- Look for unique patterns in this specific board
- Consider unconventional approaches if they make sense
- Balance risk vs reward based on current state
- Create your own rules for this particular game state

THINK CREATIVELY: What would be the absolute best move for THIS specific situation?
"""
                    }
                }
                
                # 选择当前策略
                current_strategy = strategies.get(strategy_mode, strategies['snake'])
                detailed_strategy = current_strategy['strategy']

                # 分析当前局面并给出具体建议
                max_tile = max(max(row) for row in self.matrix)
                max_pos = None
                for i in range(len(self.matrix)):
                    for j in range(len(self.matrix[0])):
                        if self.matrix[i][j] == max_tile:
                            max_pos = (i, j)
                            break
                    if max_pos:
                        break

                # 检查当前棋盘的单调性
                def check_monotonicity():
                    """检查棋盘的单调性和蛇形结构"""
                    bottom_row = self.matrix[3]  # 最底行
                    second_row = self.matrix[2]  # 倒数第二行
                    
                    # 检查底行是否从左到右递增（忽略0）
                    bottom_increasing = True
                    bottom_non_zero = [x for x in bottom_row if x > 0]
                    if len(bottom_non_zero) > 1:
                        for i in range(len(bottom_non_zero) - 1):
                            if bottom_non_zero[i] > bottom_non_zero[i + 1]:
                                bottom_increasing = False
                                break
                    
                    # 检查第二行是否从右到左递增（蛇形）
                    snake_correct = True
                    second_non_zero = [x for x in reversed(second_row) if x > 0]
                    if len(second_non_zero) > 1:
                        for i in range(len(second_non_zero) - 1):
                            if second_non_zero[i] > second_non_zero[i + 1]:
                                snake_correct = False
                                break
                    
                    return bottom_increasing, snake_correct

                bottom_mono, snake_mono = check_monotonicity()

                # 基于当前局面的具体分析
                situation_analysis = ""
                recommended_move = ""
                
                if max_pos:
                    row, col = max_pos
                    if max_tile >= 512:
                        if row == 3 and col == 3:  # 在右下角
                            situation_analysis = f"EXCELLENT: {max_tile} secured in bottom-right corner. "
                            if bottom_mono and snake_mono:
                                situation_analysis += "Snake pattern maintained! "
                                if 'RIGHT' in valid_moves and 'DOWN' in valid_moves:
                                    recommended_move = "RIGHT or DOWN (perfect snake structure)"
                                elif 'RIGHT' in valid_moves:
                                    recommended_move = "RIGHT (maintain bottom row)"
                                elif 'DOWN' in valid_moves:
                                    recommended_move = "DOWN (build column)"
                            else:
                                situation_analysis += "Need to restore snake pattern. "
                                if 'RIGHT' in valid_moves:
                                    recommended_move = "RIGHT (restore bottom monotonicity)"
                                elif 'DOWN' in valid_moves:
                                    recommended_move = "DOWN (safe move)"
                        else:
                            situation_analysis = f"CRITICAL: {max_tile} NOT in corner at [{row},{col}]! Must relocate! "
                            # 推荐能将大数字向右下角移动的方向
                            if row < 3 and col < 3:
                                recommended_move = "RIGHT then DOWN (move to corner)"
                            elif row < 3 and 'DOWN' in valid_moves:
                                recommended_move = "DOWN (move to bottom row)"
                            elif col < 3 and 'RIGHT' in valid_moves:
                                recommended_move = "RIGHT (move to right column)"
                    elif max_tile >= 128:
                        situation_analysis = f"BUILDING: {max_tile} growing, establish snake pattern. "
                        if not bottom_mono:
                            recommended_move = "RIGHT (fix bottom row monotonicity)"
                        elif 'RIGHT' in valid_moves and 'DOWN' in valid_moves:
                            recommended_move = "RIGHT or DOWN (build toward corner)"
                        elif 'RIGHT' in valid_moves:
                            recommended_move = "RIGHT (strengthen bottom row)"
                        elif 'DOWN' in valid_moves:
                            recommended_move = "DOWN (build column)"
                    else:
                        situation_analysis = f"EARLY GAME: Focus on corner establishment. "
                        if 'RIGHT' in valid_moves and 'DOWN' in valid_moves:
                            recommended_move = "RIGHT or DOWN (start corner strategy)"
                        elif 'RIGHT' in valid_moves:
                            recommended_move = "RIGHT"
                        elif 'DOWN' in valid_moves:
                            recommended_move = "DOWN"

                # 检查当前棋盘的合并机会和蛇形结构
                merge_opportunities = ""
                structure_analysis = ""
                
                # 分析底行结构
                bottom_row = self.matrix[3]
                bottom_non_zero = [(i, val) for i, val in enumerate(bottom_row) if val > 0]
                if len(bottom_non_zero) >= 2:
                    is_increasing = all(bottom_non_zero[i][1] <= bottom_non_zero[i+1][1] 
                                      for i in range(len(bottom_non_zero)-1))
                    if is_increasing:
                        structure_analysis += "✓ Bottom row monotonic (good snake foundation). "
                    else:
                        structure_analysis += "✗ Bottom row needs reordering for snake pattern. "

                # 检查合并机会
                for i in range(len(self.matrix)):
                    for j in range(len(self.matrix[0]) - 1):
                        if self.matrix[i][j] == self.matrix[i][j+1] and self.matrix[i][j] > 0:
                            merge_opportunities += f"→Merge {self.matrix[i][j]} horizontally at row {i}. "
                
                for i in range(len(self.matrix) - 1):
                    for j in range(len(self.matrix[0])):
                        if self.matrix[i][j] == self.matrix[i+1][j] and self.matrix[i][j] > 0:
                            merge_opportunities += f"↓Merge {self.matrix[i][j]} vertically at col {j}. "

                # 特殊策略建议
                strategic_advice = ""
                if max_tile >= 1024:
                    strategic_advice = "HIGH-VALUE GAME: Extreme caution! Only RIGHT/DOWN moves!"
                elif max_tile >= 256:
                    strategic_advice = "MID-GAME: Maintain snake pattern, avoid UP moves."
                else:
                    strategic_advice = "EARLY-GAME: Establish corner dominance with RIGHT/DOWN preference."

                # 根据策略模式调整提示词
                if strategy_mode == 'ai_innovation':
                    # AI创新模式 - 让AI自己分析和创造策略
                    prompt = f"""You are a 2048 STRATEGY INNOVATOR and RESEARCHER.

{detailed_strategy}

CURRENT GAME SITUATION:
======================
Board State:
{board_str}

📊 ANALYSIS DATA:
- Max tile: {max_tile} at position {max_pos}
- Valid moves: {valid_moves_str}
- Merge opportunities: {merge_opportunities}
- Board structure: {structure_analysis}

YOUR INNOVATION CHALLENGE:
=========================
1. **DEEP ANALYSIS**: What makes this board state unique?
2. **PATTERN RECOGNITION**: What patterns do you see?
3. **STRATEGY CREATION**: What's YOUR optimal approach for THIS specific situation?
4. **REASONING**: Why is your chosen move the best?
5. **INNOVATION**: Can you do better than traditional strategies?

Don't just follow rules - THINK CREATIVELY and INNOVATE!
Create your own strategy for this exact board state.

AVAILABLE MOVES: {valid_moves_str}
CHOOSE ONE WORD: {' | '.join(valid_moves)}"""
                
                else:
                    # 传统策略模式
                    strategy_name = current_strategy['name']
                    prompt = f"""You are a 2048 EXPERT using {strategy_name}.

{detailed_strategy}

CURRENT BOARD ANALYSIS:
======================
Board State:
{board_str}

🎯 ANALYSIS: {situation_analysis}
🔍 STRUCTURE: {structure_analysis}
⚡ MERGES: {merge_opportunities}
📍 Max tile: {max_tile} at position {max_pos}
🎮 STRATEGY: {strategic_advice}

VALID MOVES ONLY: {valid_moves_str}
🎯 RECOMMENDED: {recommended_move}

STRATEGY CHECKLIST:
===================
- Current strategy: {strategy_name}
- Max tile position: {max_pos}
- Board structure assessment: {structure_analysis}
- Immediate opportunities: {merge_opportunities}

RESPOND WITH EXACTLY ONE WORD: {' | '.join(valid_moves)}"""

                response = ollama.chat(
                    model=self.model_name,
                    messages=[
                        {
                            'role': 'system', 
                            'content': 'You are an expert 2048 player. Always respond with only one word: UP, DOWN, LEFT, or RIGHT. Never use thinking tags or explanations.'
                        },
                        {
                            'role': 'user', 
                            'content': prompt
                        }
                    ],
                    options={
                        'num_predict': 3,  # 允许稍多token以获得完整单词
                        'temperature': 0.0,  # 完全确定性
                        'top_p': 1.0,
                        'top_k': 4,  # 限制选择到4个有效移动
                        'stop': ['\n', '.', ':', '(', '<', 'because', 'since'],  # 停止解释性文本
                        'repeat_penalty': 1.1  # 轻微避免重复
                    }
                )
                
                ai_response = response['message']['content'].strip()
                print(f"AI原始响应: '{ai_response}'")
                
                # 更全面的文本清理
                ai_move = ai_response.upper()
                
                # 移除所有可能的思考标签和解释性文本
                cleanup_patterns = [
                    '<THINK>', '</THINK>', '<think>', '</think>',
                    'THINK:', 'THINKING:', 'THOUGHT:', 'ANALYSIS:',
                    'MOVE:', 'ANSWER:', 'RESPONSE:', 'CHOICE:',
                    'BECAUSE', 'SINCE', 'AS', 'THE', 'BEST', 'RECOMMENDED',
                    '(', ')', '[', ']', '{', '}', '"', "'",
                    'IS', 'TO', 'MOVE', 'DIRECTION', 'STRATEGY'
                ]
                
                for pattern in cleanup_patterns:
                    ai_move = ai_move.replace(pattern, '')
                
                # 移除数字和多余的空格
                ai_move = ''.join(char for char in ai_move if char.isalpha() or char.isspace())
                ai_move = ' '.join(ai_move.split())  # 标准化空格
                
                # 提取第一个有效的移动词
                words = ai_move.split()
                valid_words = ['UP', 'DOWN', 'LEFT', 'RIGHT']
                ai_move = ''
                
                for word in words:
                    if word in valid_words:
                        ai_move = word
                        break
                
                print(f"清理后的AI移动: '{ai_move}'")
                
                # 验证AI选择的移动是否有效
                if ai_move not in valid_moves:
                    print(f"AI原始输出: '{ai_response}'")
                    print(f"处理后: '{ai_move}'")
                    print(f"有效移动: {valid_moves}")
                    
                    # 更智能的匹配策略
                    best_match = None
                    
                    # 1. 精确匹配任何有效移动
                    for move in valid_moves:
                        if move in ai_move:
                            best_match = move
                            print(f"找到精确匹配: {move}")
                            break
                    
                    # 2. 如果没有精确匹配，尝试部分匹配
                    if not best_match:
                        for move in valid_moves:
                            if any(char in ai_move for char in move):
                                best_match = move
                                print(f"找到部分匹配: {move}")
                                break
                    
                    # 3. 基于策略的智能选择
                    if not best_match:
                        max_tile = max(max(row) for row in self.matrix)
                        if max_tile >= 64:
                            # 优先选择不破坏角落结构的移动
                            if 'RIGHT' in valid_moves and 'DOWN' in valid_moves:
                                best_match = random.choice(['RIGHT', 'DOWN'])
                            elif 'RIGHT' in valid_moves:
                                best_match = 'RIGHT'
                            elif 'DOWN' in valid_moves:
                                best_match = 'DOWN'
                            else:
                                best_match = valid_moves[0]
                        else:
                            best_match = random.choice(valid_moves)
                        print(f"策略选择: {best_match}")
                    
                    ai_move = best_match
                else:
                    print(f"AI有效选择: {ai_move} (从 {valid_moves})")
                
                # 缓存决策 (限制缓存大小避免内存爆炸)
                if len(AIWorker._move_cache) < 1000:
                    AIWorker._move_cache[cache_key] = ai_move
                    print(f"New AI move cached: {ai_move} (strategy: {strategy_mode}, valid: {valid_moves}) - cache size: {len(AIWorker._move_cache)}")
            
            # 移除延迟，让响应更快
            # self.msleep(100)  # 已移除，提高响应速度
            
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
        
        # 确保对话框颜色对比清晰
        self.setStyleSheet("background-color: white; color: black;")
        
        layout = QVBoxLayout(self)
        
        tabs = QTabWidget()
        # 确保tabs有清晰的颜色对比
        tabs.setStyleSheet("background-color: white; color: black;")
        
        # Game Stats Tab
        stats_tab = QWidget()
        stats_tab.setStyleSheet("background-color: white; color: black;")  # 确保清晰对比
        stats_layout = QVBoxLayout(stats_tab)
        
        stats_text = QTextEdit()
        stats_text.setReadOnly(True)
        stats_text.setStyleSheet("background-color: white; color: black; border: 1px solid #ccc;")  # 确保文字清晰可见
        stats_content = self.format_stats(stats)
        stats_text.setPlainText(stats_content)
        stats_layout.addWidget(stats_text)
        
        tabs.addTab(stats_tab, "Statistics")
        
        # Game History Tab
        history_tab = QWidget()
        history_tab.setStyleSheet("background-color: white; color: black;")  # 确保清晰对比
        history_layout = QVBoxLayout(history_tab)
        
        # 添加导出按钮
        export_layout = QHBoxLayout()
        export_btn = QPushButton("📊 导出CSV")
        export_btn.setStyleSheet("QPushButton { background-color: white; color: black; border: 1px solid #ccc; padding: 8px; border-radius: 3px; font-weight: bold; }")
        export_btn.clicked.connect(lambda: self.export_to_csv(stats))
        export_layout.addWidget(export_btn)
        export_layout.addStretch()  # 将按钮推到左边
        history_layout.addLayout(export_layout)
        
        self.history_table = QTableWidget()
        self.history_table.setStyleSheet("background-color: white; color: black; border: 1px solid #ccc;")  # 确保表格清晰可见
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Date", "Mode", "Score", "Time (s)", "Moves", "Max Tile"
        ])
        
        games = stats.get('games', [])
        self.history_table.setRowCount(len(games))
        
        for i, game in enumerate(games):
            self.history_table.setItem(i, 0, QTableWidgetItem(game.get('date', 'N/A')))
            self.history_table.setItem(i, 1, QTableWidgetItem(game.get('mode', 'N/A')))
            self.history_table.setItem(i, 2, QTableWidgetItem(str(game.get('score', 0))))
            self.history_table.setItem(i, 3, QTableWidgetItem(f"{game.get('time', 0):.1f}"))
            self.history_table.setItem(i, 4, QTableWidgetItem(str(game.get('moves', 0))))
            self.history_table.setItem(i, 5, QTableWidgetItem(str(game.get('max_tile', 0))))
        
        history_layout.addWidget(self.history_table)
        tabs.addTab(history_tab, "Game History")
        
        layout.addWidget(tabs)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.setStyleSheet("QPushButton { background-color: white; color: black; border: 1px solid #ccc; padding: 5px; border-radius: 3px; }")
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
    
    def export_to_csv(self, stats):
        """导出游戏数据到CSV文件"""
        try:
            # 打开文件保存对话框
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出游戏数据",
                f"2048_game_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV files (*.csv);;All files (*.*)"
            )
            
            if not file_path:  # 用户取消了保存
                return
            
            games = stats.get('games', [])
            if not games:
                QMessageBox.warning(self, "导出警告", "没有游戏数据可导出")
                return
            
            # 写入CSV文件
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['Date', 'Mode', 'Score', 'Time_Seconds', 'Moves', 'Max_Tile']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # 写入表头
                writer.writeheader()
                
                # 写入数据
                for game in games:
                    writer.writerow({
                        'Date': game.get('date', 'N/A'),
                        'Mode': game.get('mode', 'N/A'),
                        'Score': game.get('score', 0),
                        'Time_Seconds': round(game.get('time', 0), 1),
                        'Moves': game.get('moves', 0),
                        'Max_Tile': game.get('max_tile', 0)
                    })
            
            # 显示成功消息
            msg = QMessageBox(self)
            msg.setWindowTitle("导出成功")
            msg.setText(f"游戏数据已成功导出到:\n{file_path}\n\n共导出 {len(games)} 条游戏记录")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setStyleSheet("QMessageBox { background-color: white; color: black; } QMessageBox QPushButton { background-color: white; color: black; border: 1px solid #ccc; padding: 5px; }")
            msg.exec()
            
        except Exception as e:
            # 显示错误消息
            error_msg = QMessageBox(self)
            error_msg.setWindowTitle("导出失败")
            error_msg.setText(f"导出CSV文件时发生错误:\n{str(e)}")
            error_msg.setIcon(QMessageBox.Icon.Critical)
            error_msg.setStyleSheet("QMessageBox { background-color: white; color: black; } QMessageBox QPushButton { background-color: white; color: black; border: 1px solid #ccc; padding: 5px; }")
            error_msg.exec()

# ==================== MODEL SELECTION DIALOG ====================
class ModelSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select AI Model")
        self.setMinimumSize(500, 400)
        
        # 确保对话框颜色清晰
        self.setStyleSheet("background-color: white; color: black;")
        
        layout = QVBoxLayout(self)
        
        # 标题和说明
        title = QLabel("🤖 AI Model Selection")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px; color: black; background-color: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        instructions = QLabel(
            "Choose an Ollama model to control the 2048 game.\n"
            "Different models may have different playing strategies.\n\n"
            "📋 Requirements:\n"
            "• Ollama server must be running (ollama serve)\n"
            "• At least one model must be installed (ollama pull <model>)"
        )
        instructions.setStyleSheet("margin: 10px; padding: 10px; border: 1px solid gray; border-radius: 5px; color: black; background-color: #f8f8f8;")  # 确保清晰对比
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
        self.model_combo.setStyleSheet("background-color: white; color: black; border: 1px solid #ccc; padding: 5px; border-radius: 3px;")
        model_layout.addWidget(self.model_combo)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 Refresh Models")
        refresh_btn.setStyleSheet("background-color: white; color: black; border: 1px solid #ccc; padding: 8px; border-radius: 3px;")
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
        delay_label.setStyleSheet("color: black; background-color: transparent;")  # 确保清晰可见
        delay_layout.addWidget(delay_label)
        
        self.delay_spin = QSpinBox()
        self.delay_spin.setMinimum(500)
        self.delay_spin.setMaximum(10000)
        self.delay_spin.setValue(2000)
        self.delay_spin.setSuffix(" ms")
        self.delay_spin.setToolTip("Time between AI moves.\n500ms = very fast\n2000ms = comfortable to watch\n5000ms+ = slow, easy to analyze")
        self.delay_spin.setStyleSheet("background-color: white; color: black; border: 1px solid #ccc; padding: 5px; border-radius: 3px;")
        delay_layout.addWidget(self.delay_spin)
        
        delay_help = QLabel("(Longer delay = easier to observe AI thinking)")
        delay_help.setStyleSheet("font-style: italic; font-size: 11px; color: black; background-color: transparent;")  # 确保清晰可见
        
        settings_layout.addLayout(delay_layout)
        settings_layout.addWidget(delay_help)
        
        layout.addWidget(settings_group)
        
        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-style: italic; margin: 5px; color: black; background-color: transparent;")  # 确保清晰可见
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("▶️ Start AI")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("❌ Cancel")
        buttons.setStyleSheet("QPushButton { background-color: white; color: black; border: 1px solid #ccc; padding: 8px; border-radius: 3px; }")
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
                error_msg += "⚠️ No AI models are installed.\n\n"
                error_msg += "📦 To install models:\n"
                error_msg += "• ollama pull llama2 (General purpose)\n"
                error_msg += "• ollama pull mistral (Faster)\n"
                error_msg += "• ollama pull codellama (Logic-focused)"
            else:
                error_msg += "⚠️ Please select a valid AI model.\n\n"
                error_msg += "💡 Troubleshooting:\n"
                error_msg += "1. Start Ollama: ollama serve\n"
                error_msg += "2. Install a model: ollama pull llama2\n"
                error_msg += "3. Click 'Refresh Models'"
            
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("AI Startup Error")
            msg_box.setText(error_msg)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setStyleSheet("QMessageBox { background-color: white; color: black; } QMessageBox QPushButton { background-color: white; color: black; border: 1px solid #ccc; padding: 5px; }")
            msg_box.exec()

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
        
        # 启动时将焦点设置到游戏区域，确保键盘控制立即可用
        QTimer.singleShot(100, lambda: self.game_container.setFocus())
    
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
        self.info_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px; color: black; background-color: white; padding: 5px; border-radius: 3px;")
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
        
        # 设置游戏容器可以接收焦点和鼠标点击
        self.game_container.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.game_container.mousePressEvent = self.on_game_area_clicked
        
        # 创建游戏容器的居中布局
        game_layout_wrapper = QHBoxLayout()
        game_layout_wrapper.addStretch()
        game_layout_wrapper.addWidget(self.game_container)
        game_layout_wrapper.addStretch()
        main_layout.addLayout(game_layout_wrapper)
        
        # 添加少量间距，避免遮挡游戏区域
        main_layout.addSpacing(15)
        
        # 合并的指令和状态栏
        self.status_label = QLabel("🎮 方向键/WASD移动 | 🤖 选择模型后点击'开始AI' | ESC: 停止AI/退出 | F11: 全屏 | 准备就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 12px; margin: 5px; font-weight: bold; color: black; background-color: white; padding: 4px; border-radius: 3px;")
        main_layout.addWidget(self.status_label)
        
        self.setStyleSheet("background-color: #faf8ef;")  # 浅米色背景，确保对比度
    
    def create_control_panel(self):
        """Create the control panel with AI model selection and controls"""
        panel = QFrame()
        panel.setFixedHeight(200)
        panel.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 2px solid #333;
                border-radius: 8px;
            }
            QLabel { 
                font-weight: bold; 
                font-size: 14px;
                color: black;
                background-color: transparent;
            }
            QPushButton { 
                padding: 8px 16px; 
                font-weight: bold; 
                font-size: 14px;
                color: black;
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QComboBox {
                padding: 6px;
                font-size: 14px;
                font-weight: bold;
                color: black;
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QComboBox QAbstractItemView {
                font-weight: bold;
                font-size: 14px;
                color: black;
                background-color: white;
            }
            QSpinBox {
                padding: 6px;
                font-size: 14px;
                font-weight: bold;
                color: black;
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
        """)  # 强制设置黑字白底，确保可见性
        
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
        self.model_combo.setMinimumWidth(200)
        # 当模型选择改变时，自动将焦点返回游戏区域
        self.model_combo.currentTextChanged.connect(lambda: QTimer.singleShot(50, lambda: self.game_container.setFocus()))
        first_row.addWidget(self.model_combo)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(35, 35)
        refresh_btn.clicked.connect(self.refresh_models)
        first_row.addWidget(refresh_btn)
        
        # 策略选择
        strategy_label = QLabel("策略:")
        strategy_label.setFixedWidth(50)
        first_row.addWidget(strategy_label)
        
        self.strategy_combo = QComboBox()
        self.strategy_combo.setFixedHeight(35)
        self.strategy_combo.setMinimumWidth(180)
        self.strategy_combo.addItem("🐍 蛇形策略 (经典最优)", "snake")
        self.strategy_combo.addItem("🎯 角落专注策略", "corner_focus") 
        self.strategy_combo.addItem("📐 边缘优先策略", "edge_priority")
        self.strategy_combo.addItem("🔄 动态适应策略", "dynamic_adaptive")
        self.strategy_combo.addItem("🧠 AI创新模式", "ai_innovation")
        self.strategy_combo.setToolTip(
            "选择AI使用的策略模式:\n"
            "• 蛇形策略: 经典最优，单调性排列\n"
            "• 角落专注: 灵活的角落建设\n" 
            "• 边缘优先: 从边缘向中心建设\n"
            "• 动态适应: 根据局面调整策略\n"
            "• AI创新: 让AI自己设计策略"
        )
        # 当策略选择改变时，自动将焦点返回游戏区域
        self.strategy_combo.currentTextChanged.connect(lambda: QTimer.singleShot(50, lambda: self.game_container.setFocus()))
        first_row.addWidget(self.strategy_combo)
        
        first_row.addStretch()
        layout.addLayout(first_row)
        
        # 第二行：控制按钮
        second_row = QHBoxLayout()
        second_row.setSpacing(15)
        
        # AI控制按钮
        self.start_ai_btn = QPushButton("🤖 开始AI")
        self.start_ai_btn.setFixedSize(120, 40)
        self.start_ai_btn.setStyleSheet("")  # 使用默认样式
        self.start_ai_btn.clicked.connect(self.start_ai_mode)
        second_row.addWidget(self.start_ai_btn)
        
        self.stop_ai_btn = QPushButton("⏹️ 停止AI")
        self.stop_ai_btn.setFixedSize(120, 40)
        self.stop_ai_btn.setStyleSheet("")  # 使用默认样式
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
        
        # 获取选择的策略
        strategy_data = self.strategy_combo.currentData()
        strategy_name = self.strategy_combo.currentText().split(' ')[1] if ' ' in self.strategy_combo.currentText() else "策略"
        
        # 开始AI模式
        self.selected_model = current_data
        self.selected_strategy = strategy_data
        self.move_delay = 150  # 减少到150ms，让AI游戏非常快速
        
        self.ai_mode = True
        self.game_mode = f"AI ({self.selected_model} - {strategy_name})"
        self.start_ai_btn.setEnabled(False)
        self.stop_ai_btn.setEnabled(True)
        self.model_combo.setEnabled(False)
        self.strategy_combo.setEnabled(False)
        
        self.status_label.setText(f"🤖 AI游戏中: {self.selected_model} | {strategy_name}")
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
        self.strategy_combo.setEnabled(True)
        self.status_label.setText("🎮 人类控制 | AI已停止")
    
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
            self.model_combo.addItem(f"❌ Connection error: {str(e)}", None)
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
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("AI模型错误")
        msg_box.setText(error_msg)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setStyleSheet("QMessageBox { background-color: white; color: black; } QMessageBox QPushButton { background-color: white; color: black; border: 1px solid #ccc; padding: 5px; }")
        msg_box.exec()
    
    def make_ai_move(self):
        """Make an AI move"""
        if not self.ai_mode:
            return
        
        # Check if game is over
        state = game_state(self.matrix)
        if state in ['win', 'lose']:
            self.stop_ai_mode()
            return
        
        # Create AI worker with strategy
        strategy_mode = getattr(self, 'selected_strategy', 'snake')
        self.ai_worker = AIWorker(
            copy.deepcopy(self.matrix), 
            self.selected_model, 
            self.move_delay,
            strategy_mode
        )
        self.ai_worker.move_signal.connect(self.handle_ai_move)
        self.ai_worker.error_signal.connect(self.handle_ai_error)
        # 移除thinking信号连接以提高性能
        # self.ai_worker.thinking_signal.connect(self.handle_ai_thinking)
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
            # 保存移动前的矩阵状态
            old_matrix = copy.deepcopy(self.matrix)
            
            # 执行移动
            self.execute_move(move_map[move])
            
            # 验证移动是否真的改变了游戏状态
            if self.matrix == old_matrix:
                print(f"警告: AI移动 {move} 没有改变游戏状态!")
                # 如果移动无效，立即尝试下一步（避免卡住）
                QTimer.singleShot(50, self.make_ai_move)
                return
            
            # 减少状态更新频率，只显示关键信息
            if self.moves_count % 10 == 0:  # 每10步更新一次状态
                score = calculate_score(self.matrix)
                self.status_label.setText(f"🤖 AI: {self.selected_model} | 移动: {self.moves_count} | 分数: {score}")
            
            # Continue AI play if still in AI mode and game not over
            if self.ai_mode:
                state = game_state(self.matrix)
                if state == 'not over':
                    # 快速连续AI移动，只保留最小延迟确保UI更新
                    QTimer.singleShot(self.move_delay, self.make_ai_move)
                else:
                    # 游戏结束，显示最终结果
                    score = calculate_score(self.matrix)
                    max_tile = max(max(row) for row in self.matrix)
                    if state == 'win':
                        self.status_label.setText(f"🎉 AI获胜! 分数: {score} | 最大方块: {max_tile}")
                    else:
                        self.status_label.setText(f"😞 AI游戏结束 | 分数: {score} | 最大方块: {max_tile}")
                    self.stop_ai_mode()
    
    def handle_ai_error(self, error_msg):
        """Handle AI error"""
        self.status_label.setText(error_msg)
        self.stop_ai_mode()
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("AI Error")
        msg_box.setText(error_msg)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setStyleSheet("QMessageBox { background-color: white; color: black; } QMessageBox QPushButton { background-color: white; color: black; border: 1px solid #ccc; padding: 5px; }")
        msg_box.exec()
    
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
        
        # 清理AI缓存以获得新鲜的决策
        AIWorker._move_cache.clear()
        
        self.matrix = new_game(GRID_LEN)
        self.history_matrixs = []
        self.moves_count = 0
        self.start_time = time.time()
        self.game_mode = "Human"
        
        # 恢复控件状态
        self.start_ai_btn.setEnabled(True)
        self.stop_ai_btn.setEnabled(False)
        self.model_combo.setEnabled(True)
        self.strategy_combo.setEnabled(True)
        
        self.update_grid_cells()
        self.update_info()
        self.status_label.setText("🎮 新游戏开始 | 方向键/WASD移动 | 可选择AI模型自动游戏")
    
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
        
        # 检查焦点是否在控制组件上（如下拉菜单、按钮等）
        focused_widget = QApplication.focusWidget()
        is_control_focused = (
            focused_widget and (
                isinstance(focused_widget, (QComboBox, QPushButton, QSpinBox)) or
                focused_widget.parent() in [self.model_combo, self.strategy_combo]
            )
        )
        
        # 全局快捷键（无论焦点在哪里都响应）
        if key == Qt.Key.Key_Escape:
            if self.ai_mode:
                # ESC键停止AI，不退出游戏
                self.stop_ai_mode()
                self.status_label.setText("🎮 AI已停止 | 可手动游戏或重新开始AI")
            else:
                # 只有在非AI模式下ESC才退出游戏
                if self.moves_count > 0:
                    self.save_game_result()
                self.close()
        elif key == Qt.Key.Key_Space and self.ai_mode:
            # 空格键也可以停止AI
            self.stop_ai_mode()
            self.status_label.setText("🎮 AI已停止 | 空格键停止")
        elif key == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        
        # 游戏控制键（只有在控件没有焦点时才响应）
        elif not is_control_focused:
            if key == Qt.Key.Key_B and len(self.history_matrixs) > 1 and not self.ai_mode:
                self.matrix = self.history_matrixs.pop()
                self.moves_count = max(0, self.moves_count - 1)
                self.update_grid_cells()
                self.update_info()
            elif key in self.commands and not self.ai_mode:
                self.execute_move(self.commands[key])
        
        # 如果焦点在控件上且是方向键，让控件处理（不调用游戏移动）
        elif is_control_focused and key in self.commands:
            # 让控件自己处理方向键（如下拉菜单导航）
            event.ignore()
            return
        
        # 对于其他情况，调用父类的事件处理
        super().keyPressEvent(event)
    
    def on_game_area_clicked(self, event):
        """游戏区域被点击时，设置焦点到游戏区域以确保键盘控制正常工作"""
        self.game_container.setFocus()
        # 显示提示信息
        if not self.ai_mode:
            self.status_label.setText("🎮 游戏区域已聚焦 | 键盘控制已激活")
    
    def show_game_result(self, text1, text2):
        """Display game result"""
        if GRID_LEN >= 2:
            if self.ai_mode:
                display_text1 = f"AI"
                display_text2 = text2
                result_text = f"🤖 AI{text2} | 模型: {self.selected_model}"
            else:
                display_text1 = text1
                display_text2 = text2
                result_text = f"🎮 {text2} | 游戏结束"
            
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
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Ollama Not Found")
        msg_box.setText("Ollama is not installed. AI features will be disabled.\n"
                       "To enable AI features, install Ollama:\n"
                       "pip install ollama")
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setStyleSheet("QMessageBox { background-color: white; color: black; } QMessageBox QPushButton { background-color: white; color: black; border: 1px solid #ccc; padding: 5px; }")
        msg_box.exec()
    
    game = GameGrid()
    game.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 