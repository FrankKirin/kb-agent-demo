#!/usr/bin/env python3
"""
@trace 装饰器使用示例和最佳实践

这个文件展示了 observability.py 中 @trace 装饰器的各种用法。
"""

import sys
import os
sys.path.insert(0, 'src')

from observability import trace, trace_llm, trace_tool, trace_retrieval
import time
import json

def demonstrate_basic_usage():
    """基本用法示例"""
    print("=== 基本用法示例 ===")
    
    # 方法1: 使用 trace(kind) 装饰器
    @trace(kind="llm")
    def call_llm_api(prompt: str):
        """调用 LLM API"""
        time.sleep(0.05)
        return f"Response to: {prompt}"
    
    # 方法2: 使用快捷装饰器
    @trace_llm
    def another_llm_call(prompt: str):
        """另一种 LLM 调用"""
        time.sleep(0.05)
        return {"response": f"Answer: {prompt}"}
    
    result1 = call_llm_api("Hello")
    result2 = another_llm_call("World")
    print(f"Result 1: {result1}")
    print(f"Result 2: {result2}")

def demonstrate_class_methods():
    """类方法装饰示例"""
    print("\n=== 类方法装饰示例 ===")
    
    class AIAgent:
        def __init__(self, name: str):
            self.name = name
        
        @trace_tool
        def process(self, input_data: str) -> str:
            """处理输入数据"""
            time.sleep(0.03)
            return f"{self.name} processed: {input_data}"
        
        @classmethod
        @trace(kind="tool")
        def utility_method(cls, data: dict) -> dict:
            """工具类方法"""
            time.sleep(0.02)
            return {"processed": True, "data": data}
    
    agent = AIAgent("Agent1")
    result1 = agent.process("test data")
    result2 = AIAgent.utility_method({"key": "value"})
    
    print(f"Agent result: {result1}")
    print(f"Utility result: {result2}")

def demonstrate_error_handling():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")
    
    @trace(kind="llm")
    def unreliable_api_call():
        """模拟不可靠的 API 调用"""
        import random
        time.sleep(0.02)
        if random.random() < 0.5:
            raise ConnectionError("API connection failed")
        return "Success"
    
    successes = 0
    failures = 0
    
    for i in range(3):
        try:
            result = unreliable_api_call()
            print(f"Attempt {i+1}: ✅ {result}")
            successes += 1
        except ConnectionError as e:
            print(f"Attempt {i+1}: ❌ {e}")
            failures += 1
    
    print(f"\nSummary: {successes} successes, {failures} failures")
    print("Note: All errors are logged to traces.jsonl")

def demonstrate_custom_kinds():
    """自定义跟踪类型示例"""
    print("\n=== 自定义跟踪类型示例 ===")
    
    # 自定义 kind 类型
    @trace(kind="database")
    def query_database(sql: str):
        """数据库查询"""
        time.sleep(0.06)
        # 模拟查询结果
        return {
            "rows": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ],
            "count": 2,
            "query": sql
        }
    
    @trace(kind="external_api")
    def call_external_api(endpoint: str, params: dict):
        """调用外部 API"""
        time.sleep(0.07)
        return {
            "status": "success",
            "endpoint": endpoint,
            "response": {"data": "sample"}
        }
    
    db_result = query_database("SELECT * FROM users")
    api_result = call_external_api("/users", {"id": 1})
    
    print(f"Database result: {db_result['count']} rows")
    print(f"API result: {api_result['status']}")

def demonstrate_context_info():
    """添加上下文信息示例"""
    print("\n=== 添加上下文信息示例 ===")
    
    import uuid
    import threading
    
    # 在装饰器内部添加额外上下文
    @trace(kind="workflow")
    def complex_workflow(task_id: str, priority: int = 1):
        """复杂工作流"""
        # 可以添加线程/进程信息
        context_info = {
            "task_id": task_id,
            "priority": priority,
            "thread": threading.current_thread().name,
            "timestamp": time.time()
        }
        
        time.sleep(0.1)
        
        # 返回结果时可以包含上下文信息
        return {
            "task_completed": True,
            "context": context_info,
            "result": f"Task {task_id} completed"
        }
    
    task_id = str(uuid.uuid4())[:8]
    result = complex_workflow(task_id, priority=3)
    print(f"Workflow completed: {result['result']}")
    print(f"Context: {result['context']['thread']}, Priority: {result['context']['priority']}")

def main():
    """主函数：运行所有示例"""
    print("=" * 60)
    print("@trace 装饰器示例和最佳实践")
    print("=" * 60)
    
    # 清理旧的跟踪文件
    if os.path.exists("traces.jsonl"):
        print(f"Clearing previous traces.jsonl")
        os.remove("traces.jsonl")
    
    # 运行所有示例
    demonstrate_basic_usage()
    demonstrate_class_methods()
    demonstrate_error_handling()
    demonstrate_custom_kinds()
    demonstrate_context_info()
    
    # 显示生成的跟踪
    print("\n" + "=" * 60)
    print("跟踪记录汇总")
    print("=" * 60)
    
    if os.path.exists("traces.jsonl"):
        with open("traces.jsonl", "r", encoding="utf-8") as f:
            records = [json.loads(line) for line in f]
        
        print(f"总跟踪记录数: {len(records)}")
        
        # 统计信息
        from collections import Counter
        kind_counts = Counter(record["kind"] for record in records)
        
        print("\n跟踪类型分布:")
        for kind, count in sorted(kind_counts.items()):
            success_count = sum(1 for r in records if r["kind"] == kind and r["status"] == "ok")
            error_count = count - success_count
            print(f"  {kind}: {count} 条记录 ({success_count}✅ {error_count}❌)")
        
        # 性能统计
        durations = [r["duration_seconds"] for r in records]
        if durations:
            print(f"\n性能统计:")
            print(f"  平均耗时: {sum(durations)/len(durations):.4f} 秒")
            print(f"  最长耗时: {max(durations):.4f} 秒")
            print(f"  最短耗时: {min(durations):.4f} 秒")
    
    print("\n" + "=" * 60)
    print("所有示例完成!")
    print("跟踪记录已保存到 traces.jsonl")
    print("=" * 60)

if __name__ == "__main__":
    main()