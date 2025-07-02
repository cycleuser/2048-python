#!/usr/bin/env python3
"""
AI Performance Test - 测试AI响应速度和缓存效果
"""

import time
import copy
from ai_game import AIWorker, new_game

def test_ai_performance():
    """测试AI性能"""
    print("🚀 AI Performance Test")
    print("=" * 40)
    
    # 创建测试棋盘
    matrix = new_game(4)
    model_name = "llama2"  # 默认模型，可以根据实际安装的模型修改
    
    print(f"测试模型: {model_name}")
    print(f"测试棋盘:")
    for row in matrix:
        print(row)
    
    # 显示有效移动
    from ai_game import get_valid_moves
    valid_moves = get_valid_moves(matrix)
    print(f"有效移动: {valid_moves}")
    print()
    
    # 测试第一次调用（无缓存）
    print("测试 1: 第一次AI调用（无缓存）")
    start_time = time.time()
    
    worker = AIWorker(copy.deepcopy(matrix), model_name)
    worker.run()  # 直接调用run方法进行同步测试
    
    first_call_time = time.time() - start_time
    print(f"第一次调用耗时: {first_call_time:.3f} 秒")
    print()
    
    # 测试第二次调用（使用缓存）
    print("测试 2: 第二次AI调用（使用缓存）")
    start_time = time.time()
    
    worker2 = AIWorker(copy.deepcopy(matrix), model_name)
    worker2.run()  # 直接调用run方法进行同步测试
    
    second_call_time = time.time() - start_time
    print(f"第二次调用耗时: {second_call_time:.3f} 秒")
    print()
    
    # 计算性能提升
    if first_call_time > 0 and second_call_time > 0:
        speedup = first_call_time / second_call_time
        print(f"⚡ 性能提升: {speedup:.1f}x 倍")
        print(f"💾 缓存命中率: {(1 - second_call_time/first_call_time)*100:.1f}%")
    
    print(f"📊 缓存大小: {len(AIWorker._move_cache)} 条记录")
    
    # 测试无效移动检测
    print("\n测试 3: 无效移动检测")
    test_matrix = [[2, 4, 8, 16], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    test_valid_moves = get_valid_moves(test_matrix)
    print(f"测试棋盘的有效移动: {test_valid_moves}")
    print("预期: DOWN应该是无效的，因为所有数字都在顶行")
    
    # 测试AI策略智能性
    print("\n测试 4: AI策略智能性")
    strategic_matrix = [[2, 4, 8, 16], [4, 8, 16, 32], [0, 0, 64, 128], [0, 0, 0, 256]]
    strategic_valid = get_valid_moves(strategic_matrix)
    print("策略测试棋盘（大数字在右下）:")
    for row in strategic_matrix:
        print(row)
    print(f"有效移动: {strategic_valid}")
    
    # 测试AI决策
    if strategic_valid:
        print("测试AI在策略棋盘上的决策...")
        worker3 = AIWorker(strategic_matrix, model_name)
        start_time = time.time()
        worker3.run()
        strategy_time = time.time() - start_time
        print(f"策略决策耗时: {strategy_time:.3f} 秒")

if __name__ == "__main__":
    try:
        test_ai_performance()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("请确保:")
        print("1. Ollama 服务正在运行")
        print("2. 已安装至少一个模型 (如 llama2)")
        print("3. ai_game.py 文件存在")
    
    input("\n按Enter键退出...") 