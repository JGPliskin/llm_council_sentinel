#!/usr/bin/env python3
"""
NIM API 测试脚本 (异步并发版)
测试英伟达 NIM API 服务的多模型响应质量和性能

功能：
- 异步并发测试 (Asyncio + HTTPX)
- 并发数控制
- 速率限制 (RPM控制)
- 记录思考过程（reasoning_content 或 <think> 标签）
- 记录详细性能指标
"""

import asyncio
import json
import os
import re
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

import httpx
from dotenv import load_dotenv

# ============ 配置 ============
NIM_API_BASE = "https://integrate.api.nvidia.com/v1"
REQUEST_TIMEOUT = 120  # 秒
RPM_LIMIT = 20  # 每分钟请求数 (安全起见，全局限速)
MAX_CONCURRENCY = 3  # 最大并发数
MAX_RETRIES = 0  # 禁用重试

# 每次尝试获取令牌的间隔（秒），用于平滑请求
TOKEN_INTERVAL = 60.0 / RPM_LIMIT

# 时区
CST = timezone(timedelta(hours=8))


def load_config():
    """加载配置：API Key、模型列表、问题列表"""
    # 加载 .env (从当前文件位置向上3级)
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)
    
    api_key = os.getenv("NIM_API_KEY")
    if not api_key:
        raise ValueError("未找到 NIM_API_KEY，请在 .env 文件中配置")
    
    # 加载模型列表
    models_path = Path(__file__).parent / "nim_test_models.json"
    with open(models_path, "r", encoding="utf-8") as f:
        models = json.load(f)
    
    # 加载问题列表
    questions_path = Path(__file__).parent / "nim_test_questions.json"
    with open(questions_path, "r", encoding="utf-8") as f:
        questions = json.load(f)
    
    return api_key, models, questions


def extract_thinking_from_content(content: str) -> tuple[str, str]:
    """
    从 content 中提取 <think>...</think> 标签内容
    返回: (thinking_content, answer_content)
    """
    think_pattern = re.compile(r"<think>(.*?)</think>", re.DOTALL | re.IGNORECASE)
    match = think_pattern.search(content)
    
    if match:
        thinking = match.group(1).strip()
        answer = think_pattern.sub("", content).strip()
        return thinking, answer
    
    return "", content


class RateLimiter:
    """简单的速率限制器"""
    def __init__(self, interval: float):
        self.interval = interval
        self.last_request_time = 0.0
        self.lock = asyncio.Lock()

    async def wait(self):
        async with self.lock:
            now = time.perf_counter()
            elapsed = now - self.last_request_time
            wait_time = self.interval - elapsed
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self.last_request_time = time.perf_counter()


async def call_nim_api_async(
    client: httpx.AsyncClient,
    api_key: str,
    model: str,
    question: str
) -> dict:
    """异步调用 NIM API"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": question}
        ],
        "stream": False,
        "max_tokens": 4096,
    }
    
    start_time = time.perf_counter()
    
    try:
        response = await client.post(
            f"{NIM_API_BASE}/chat/completions",
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        
        end_time = time.perf_counter()
        total_latency_ms = (end_time - start_time) * 1000
        
        if response.status_code != 200:
            return {
                "status": "error",
                "error_message": f"HTTP {response.status_code}: {response.text[:500]}",
                "total_latency_ms": total_latency_ms,
            }
        
        data = response.json()
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        
        reasoning_content = message.get("reasoning_content", "")
        content = message.get("content", "")
        
        if not reasoning_content:
            thinking_from_tag, answer_from_tag = extract_thinking_from_content(content)
            thinking_content = thinking_from_tag
            answer_content = answer_from_tag
        else:
            thinking_content = reasoning_content
            answer_content = content
        
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        
        thinking_tokens = usage.get("reasoning_tokens", 0)
        if not thinking_tokens and thinking_content:
            thinking_tokens = len(thinking_content) // 2
        
        tokens_per_second = completion_tokens / (total_latency_ms / 1000) if total_latency_ms > 0 else 0
        
        return {
            "status": "success",
            "thinking_content": thinking_content,
            "thinking_tokens": thinking_tokens,
            "answer_content": answer_content,
            "input_tokens": prompt_tokens,
            "output_tokens": completion_tokens,
            "total_latency_ms": round(total_latency_ms, 2),
            "tokens_per_second": round(tokens_per_second, 2),
            "error_message": None,
        }
        
    except httpx.TimeoutException:
        end_time = time.perf_counter()
        return {
            "status": "error",
            "error_message": f"请求超时（{REQUEST_TIMEOUT}秒）",
            "total_latency_ms": round((end_time - start_time) * 1000, 2),
        }
    except Exception as e:
        end_time = time.perf_counter()
        return {
            "status": "error",
            "error_message": f"错误: {str(e)}",
            "total_latency_ms": round((end_time - start_time) * 1000, 2),
        }


async def worker(
    name: int,
    queue: asyncio.Queue,
    client: httpx.AsyncClient,
    api_key: str,
    rate_limiter: RateLimiter,
    file_lock: asyncio.Lock,
    output_path: Path,
    progress_info: Dict[str, Any]
):
    """工作协程"""
    while True:
        try:
            task_item = queue.get_nowait()
        except asyncio.QueueEmpty:
            break
            
        model = task_item['model']
        question = task_item['question']
        
        try:
            # 速率限制等待
            await rate_limiter.wait()
            
            # 执行测试
            result = await call_nim_api_async(client, api_key, model, question["content"])
            
            # 记录结果
            timestamp = datetime.now(CST).isoformat()
            record = {
                "timestamp": timestamp,
                "model": model,
                "question_id": question["id"],
                "question_title": question["title"],
                "question": question["content"],
                **result,
                "retry_count": 0,
                "retry_errors": []
            }
            
            # 更新进度
            completed = progress_info['completed'] + 1
            progress_info['completed'] = completed
            total = progress_info['total']
            
            # 追加写入文件 (NDJSON)
            async with file_lock:
                try:
                    with open(output_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(record, ensure_ascii=False) + "\n")
                except Exception as e:
                    print(f"  [Warning] 写入文件失败: {e}")
            
            # 打印日志
            status_icon = "✓" if result["status"] == "success" else "✗"
            latency_str = f"{result.get('total_latency_ms', 0)/1000:.1f}s"
            
            elapsed = time.perf_counter() - progress_info['start_time']
            avg_time = elapsed / completed if completed > 0 else 0
            remaining = (total - completed) * avg_time
            eta_str = f"{remaining/60:.1f}m" if remaining > 60 else f"{remaining:.0f}s"
            
            if result["status"] == "success":
                print(f"  [{completed}/{total}] {model[:25]}.. Q{question['id']} | {status_icon} {latency_str} | ETA:{eta_str}")
            else:
                err_msg = result.get('error_message', '')[:40].replace('\n', ' ')
                print(f"  [{completed}/{total}] {model[:25]}.. Q{question['id']} | {status_icon} {err_msg} | ETA:{eta_str}")
                
        except Exception as e:
            print(f"  [Error] 任务执行异常: {model} Q{question['id']} - {e}")
        finally:
            queue.task_done()


async def run_tests_async():
    print("=" * 60)
    print("NIM API 批量测试脚本 (Async Pool)")
    print("=" * 60)
    
    api_key, models, questions = load_config()

    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description="NIM API Test Script")
    parser.add_argument("--questions", type=str, help="Filter questions by ID (comma separated), e.g. '7,8,9'")
    args = parser.parse_args()

    # 过滤问题
    if args.questions:
        target_ids = [int(x.strip()) for x in args.questions.split(",") if x.strip()]
        questions = [q for q in questions if q["id"] in target_ids]
        print(f"[过滤] 仅测试问题 ID: {target_ids}")
        if not questions:
            print("[错误] 未找到匹配的问题 ID")
            return
    
    total_tasks = len(models) * len(questions)
    
    print(f"\n[配置] 并发数: {MAX_CONCURRENCY} | 重试: {MAX_RETRIES} | 限速: {RPM_LIMIT} RPM")
    print(f"[任务] 模型: {len(models)} | 问题: {len(questions)} | 总计: {total_tasks}")
    
    timestamp_str = datetime.now(CST).strftime("%Y%m%d_%H%M%S")
    # 使用 .jsonl 后缀表示 NDJSON
    output_path = Path(__file__).parent / f"nim_test_results_{timestamp_str}.jsonl"
    print(f"[输出] {output_path.name}")
    print("-" * 60)

    # 准备队列
    queue = asyncio.Queue()
    for model in models:
        for q in questions:
            queue.put_nowait({
                'model': model, 
                'question': q,
                'q_idx': q['id']
            })
            
    rate_limiter = RateLimiter(TOKEN_INTERVAL)
    file_lock = asyncio.Lock()
    
    progress_info = {
        'completed': 0, 
        'total': total_tasks,
        'start_time': time.perf_counter()
    }
    
    # 启动 HTTP 客户端
    async with httpx.AsyncClient() as client:
        # 创建工作任务
        tasks = []
        for i in range(MAX_CONCURRENCY):
            task = asyncio.create_task(worker(
                i, queue, client, api_key, rate_limiter, file_lock, output_path, progress_info
            ))
            tasks.append(task)
            
        # 等待队列完成
        await asyncio.gather(*tasks)
        
    total_time = time.perf_counter() - progress_info['start_time']
    
    # 统计结果
    success_count = 0
    error_count = 0
    if output_path.exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        r = json.loads(line)
                        if r['status'] == 'success':
                            success_count += 1
                        else:
                            error_count += 1
                    except:
                        pass
    
    print("-" * 60)
    print(f"完成! 总耗时: {total_time/60:.1f}m")
    print(f"成功: {success_count} | 失败: {error_count}")
    print(f"文件: {output_path}")


if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_tests_async())
