"""
observability.py 提供 @trace(kind) 装饰器。
- 记录：函数名、kind、开始时间、耗时、状态（ok/error）、错误信息
- 按 kind 记录额外字段：
  - kind="llm"：prompt_tokens、completion_tokens、tool_calls 数量
  - kind="tool"：工具名、结果长度
  - kind="retrieval"：命中数、来源列表
- 输出到 traces.jsonl，每行一个 JSON
- 异常时也记录，然后重新抛出
"""
import functools
import json
import time
import traceback
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
import threading

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

# 线程安全的文件写入锁
_write_lock = threading.Lock()

def _write_trace_to_file(trace_data: Dict[str, Any], filename: str = "traces.jsonl") -> None:
    """
    将跟踪数据写入 JSONL 文件（线程安全）
    
    Args:
        trace_data: 要写入的跟踪数据字典
        filename: 输出文件名，默认为 traces.jsonl
    """
    try:
        with _write_lock:
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(json.dumps(trace_data, ensure_ascii=False) + '\n')
    except Exception as e:
        # 如果写入文件失败，至少打印到 stderr 避免静默失败
        import sys
        print(f"Warning: Failed to write trace to {filename}: {e}", file=sys.stderr)


def trace(kind: str) -> Callable[[F], F]:
    """
    创建跟踪装饰器
    
    Args:
        kind: 跟踪类型，支持 "llm", "tool", "retrieval" 或其他自定义类型
    
    Returns:
        装饰器函数
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 基础跟踪信息
            start_time = time.time()
            start_datetime = datetime.now().isoformat()
            func_name = func.__name__
            status = "ok"
            error_info = None
            
            # 根据 kind 初始化额外字段
            extra_fields: Dict[str, Any] = {}
            
            if kind == "llm":
                extra_fields = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "tool_calls": 0
                }
            elif kind == "tool":
                extra_fields = {
                    "tool_name": None,
                    "result_length": 0
                }
            elif kind == "retrieval":
                extra_fields = {
                    "hit_count": 0,
                    "sources": []
                }
            
            try:
                # 执行被装饰的函数
                result = func(*args, **kwargs)
                
                # 根据 kind 提取额外信息
                if kind == "llm":
                    # 假设结果是一个元组或包含 token 信息的对象
                    if isinstance(result, tuple) and len(result) >= 3:
                        extra_fields["prompt_tokens"] = result[0] if len(result) > 0 else 0
                        extra_fields["completion_tokens"] = result[1] if len(result) > 1 else 0
                        extra_fields["tool_calls"] = result[2] if len(result) > 2 else 0
                    elif hasattr(result, '__dict__'):
                        # 如果是对象，尝试获取属性
                        result_dict = result.__dict__
                        extra_fields["prompt_tokens"] = result_dict.get("prompt_tokens", 0)
                        extra_fields["completion_tokens"] = result_dict.get("completion_tokens", 0)
                        extra_fields["tool_calls"] = result_dict.get("tool_calls", 0)
                
                elif kind == "tool":
                    # 假设第一个参数是工具名，或者从函数名/参数中提取
                    if args and isinstance(args[0], str):
                        extra_fields["tool_name"] = args[0]
                    else:
                        extra_fields["tool_name"] = func_name
                    
                    # 计算结果长度
                    if result is not None:
                        if isinstance(result, str):
                            extra_fields["result_length"] = len(result)
                        elif isinstance(result, (list, dict)):
                            extra_fields["result_length"] = len(str(result))
                        else:
                            extra_fields["result_length"] = 1
                
                elif kind == "retrieval":
                    # 假设结果是一个包含命中信息的字典或列表
                    if isinstance(result, dict):
                        extra_fields["hit_count"] = result.get("hit_count", 0)
                        extra_fields["sources"] = result.get("sources", [])
                    elif isinstance(result, list):
                        extra_fields["hit_count"] = len(result)
                        extra_fields["sources"] = result
                    elif result is not None:
                        extra_fields["hit_count"] = 1
                        extra_fields["sources"] = [str(result)]
                
                return result
                
            except Exception as e:
                # 捕获异常，记录错误信息
                status = "error"
                error_info = {
                    "type": type(e).__name__,
                    "message": str(e),
                    "traceback": traceback.format_exc()
                }
                raise  # 重新抛出异常
            
            finally:
                # 计算耗时
                end_time = time.time()
                duration_seconds = end_time - start_time
                
                # 构建跟踪记录
                trace_record = {
                    "function_name": func_name,
                    "kind": kind,
                    "start_time": start_datetime,
                    "duration_seconds": duration_seconds,
                    "status": status,
                    "error_info": error_info,
                    **extra_fields  # 合并额外字段
                }
                
                # 写入文件
                _write_trace_to_file(trace_record)
        
        return wrapper  # type: ignore
    
    return decorator

# 为了方便使用，提供常用类型的快捷装饰器
def trace_llm(func: F) -> F:
    """用于 LLM 调用的跟踪装饰器快捷方式"""
    return trace(kind="llm")(func)

def trace_tool(func: F) -> F:
    """用于工具调用的跟踪装饰器快捷方式"""
    return trace(kind="tool")(func)

def trace_retrieval(func: F) -> F:
    """用于检索调用的跟踪装饰器快捷方式"""
    return trace(kind="retrieval")(func)


# 示例使用说明
if __name__ == "__main__":
    # 示例函数
    @trace(kind="llm")
    def call_llm(prompt: str) -> tuple:
        """模拟 LLM 调用"""
        # 模拟处理时间
        time.sleep(0.1)
        # 返回 (prompt_tokens, completion_tokens, tool_calls)
        return (len(prompt.split()), 50, 3)
    
    @trace(kind="tool")
    def call_tool(tool_name: str, input_data: str) -> str:
        """模拟工具调用"""
        time.sleep(0.05)
        return f"Result from {tool_name}: processed {len(input_data)} chars"
    
    @trace(kind="retrieval")
    def retrieve_documents(query: str) -> dict:
        """模拟文档检索"""
        time.sleep(0.08)
        return {
            "hit_count": 3,
            "sources": ["doc1.pdf", "doc2.txt", "doc3.md"]
        }
    
    # 运行示例
    try:
        print("Testing trace decorator...")
        
        # 测试正常调用
        result1 = call_llm("Hello, how are you?")
        print(f"LLM result: {result1}")
        
        result2 = call_tool("calculator", "1 + 1 = 2")
        print(f"Tool result: {result2}")
        
        result3 = retrieve_documents("Python programming")
        print(f"Retrieval result: {result3}")
        
        # 测试异常情况
        @trace(kind="tool")
        def failing_tool():
            raise ValueError("Something went wrong!")
        
        try:
            failing_tool()
        except ValueError as e:
            print(f"Caught expected error: {e}")
        
        print("\nCheck traces.jsonl for trace records")
        
    except Exception as e:
        print(f"Error in example: {e}")