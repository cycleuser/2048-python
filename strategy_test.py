#!/usr/bin/env python3
"""
2048 Multi-Strategy Test
测试不同AI策略在相同棋盘状态下的决策差异
"""

import copy
import time
from ai_game import AIWorker, new_game, get_valid_moves

def test_strategy_comparison():
    """测试不同策略的决策差异"""
    print("🧪 2048 Multi-Strategy Test")
    print("=" * 50)
    
    # 创建一个有趣的测试棋盘（确保有有效移动）
    test_matrix = [
        [2, 4, 8, 0],
        [4, 8, 16, 32], 
        [8, 16, 64, 128],
        [16, 32, 128, 256]
    ]
    
    print("测试棋盘状态:")
    for i, row in enumerate(test_matrix):
        print(f"Row {i}: {row}")
    
    valid_moves = get_valid_moves(test_matrix)
    print(f"\n有效移动: {valid_moves}")
    print("-" * 50)
    
    # 测试所有策略
    strategies = [
        ('snake', '🐍 蛇形策略'),
        ('corner_focus', '🎯 角落专注策略'),
        ('edge_priority', '📐 边缘优先策略'), 
        ('dynamic_adaptive', '🔄 动态适应策略'),
        ('ai_innovation', '🧠 AI创新模式')
    ]
    
    model_name = "llama2"  # 可根据实际安装的模型修改
    
    strategy_results = {}
    
    for strategy_id, strategy_name in strategies:
        print(f"\n🎮 测试 {strategy_name}")
        print("-" * 30)
        
        try:
            # 创建AI工作器
            worker = AIWorker(
                copy.deepcopy(test_matrix),
                model_name,
                move_delay=100,
                strategy_mode=strategy_id
            )
            
            # 记录开始时间
            start_time = time.time()
            
            # 运行策略分析
            worker.run()
            
            # 记录耗时
            elapsed_time = time.time() - start_time
            
            # 从信号中获取结果（简化版，直接从缓存获取）
            cache_key = (
                tuple(tuple(row) for row in test_matrix),
                tuple(sorted(valid_moves)),
                strategy_id
            )
            
            result_move = AIWorker._move_cache.get(cache_key, "未知")
            
            strategy_results[strategy_id] = {
                'name': strategy_name,
                'move': result_move,
                'time': elapsed_time
            }
            
            print(f"✅ 策略决策: {result_move}")
            print(f"⏱️ 分析耗时: {elapsed_time:.3f}秒")
            
        except Exception as e:
            print(f"❌ 策略测试失败: {e}")
            strategy_results[strategy_id] = {
                'name': strategy_name,
                'move': 'ERROR',
                'time': 0
            }
    
    # 显示对比结果
    print("\n" + "=" * 50)
    print("📊 策略对比结果")
    print("=" * 50)
    
    move_counts = {}
    for strategy_id, result in strategy_results.items():
        move = result['move']
        name = result['name']
        time_taken = result['time']
        
        print(f"{name:25} → {move:8} ({time_taken:.3f}s)")
        
        if move in move_counts:
            move_counts[move] += 1
        else:
            move_counts[move] = 1
    
    print("\n📈 移动选择统计:")
    for move, count in sorted(move_counts.items()):
        percentage = (count / len(strategies)) * 100
        print(f"  {move}: {count}个策略选择 ({percentage:.1f}%)")
    
    print("\n🤔 分析:")
    if len(move_counts) == 1:
        print("  所有策略都选择了相同的移动 - 可能存在明显的最优解")
    elif len(move_counts) == len(strategies):
        print("  每个策略都选择了不同的移动 - 策略差异显著")
    else:
        print("  策略之间存在部分分歧 - 体现了不同的战略思维")

def test_innovation_mode():
    """专门测试AI创新模式"""
    print("\n🧠 AI创新模式专项测试")
    print("=" * 40)
    
    # 创建一个复杂的棋盘状态
    complex_matrix = [
        [2, 0, 4, 8],
        [0, 2, 0, 16],
        [4, 0, 8, 32], 
        [0, 0, 0, 64]
    ]
    
    print("复杂棋盘状态:")
    for i, row in enumerate(complex_matrix):
        print(f"Row {i}: {row}")
    
    valid_moves = get_valid_moves(complex_matrix)
    print(f"有效移动: {valid_moves}")
    
    print("\n🎯 测试AI创新能力...")
    print("观察AI是否能提出创新的策略思路")
    
    try:
        worker = AIWorker(
            complex_matrix,
            "llama2",
            move_delay=100,
            strategy_mode='ai_innovation'
        )
        
        start_time = time.time()
        worker.run()
        elapsed_time = time.time() - start_time
        
        cache_key = (
            tuple(tuple(row) for row in complex_matrix),
            tuple(sorted(valid_moves)),
            'ai_innovation'
        )
        
        result_move = AIWorker._move_cache.get(cache_key, "未知")
        
        print(f"✅ AI创新决策: {result_move}")
        print(f"⏱️ 创新分析时间: {elapsed_time:.3f}秒")
        print("\n💡 AI创新模式的特点:")
        print("  - AI会分析当前棋盘的独特性")
        print("  - 创造适合当前状态的策略")
        print("  - 不拘泥于传统策略规则")
        print("  - 基于具体情况做出创新决策")
        
    except Exception as e:
        print(f"❌ AI创新测试失败: {e}")

def main():
    """主测试函数"""
    print("🚀 Starting Multi-Strategy AI Test")
    print("需要确保Ollama服务正在运行，并已安装模型")
    print()
    
    try:
        # 清理缓存确保新鲜测试
        AIWorker._move_cache.clear()
        
        # 运行策略对比测试
        test_strategy_comparison()
        
        # 运行AI创新测试
        test_innovation_mode()
        
        print(f"\n📊 总缓存大小: {len(AIWorker._move_cache)} 条记录")
        print("\n✅ 多策略测试完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("\n🔧 请检查:")
        print("1. Ollama服务是否运行 (ollama serve)")
        print("2. 是否安装了llama2模型 (ollama pull llama2)")
        print("3. ai_game.py文件是否存在")

if __name__ == "__main__":
    main()
    input("\n按Enter键退出...") 