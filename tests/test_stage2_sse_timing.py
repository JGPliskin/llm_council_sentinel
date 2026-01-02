#!/usr/bin/env python3
"""
测试脚本：验证 Stage 2 SSE 事件的发送时序

目的：确认后端是否在每个议员 review 完成后立即发送 stage2_item 事件，
还是等所有议员完成后一起发送。

使用方法：
1. 确保后端服务运行在 localhost:8010
2. 运行: python tests/test_stage2_sse_timing.py

观察输出中 stage2_item 事件的时间戳差异。
"""

import asyncio
import aiohttp
import json
import time


async def test_stage2_timing():
    """发送一个请求并监控 SSE 事件时序"""
    
    base_url = "http://localhost:8010"
    
    # 1. 创建会话
    async with aiohttp.ClientSession() as session:
        # 创建对话
        async with session.post(f"{base_url}/api/conversations") as resp:
            conv = await resp.json()
            conv_id = conv["id"]
            print(f"✅ 创建对话: {conv_id}")
        
        # 2. 发送消息并订阅 SSE
        url = f"{base_url}/api/conversations/{conv_id}/message/stream"
        payload = {
            "content": "请用一句话解释什么是区块链",
            "enable_thinking": False  # 关闭 thinking 减少噪音
        }
        
        print("\n📡 开始监控 SSE 事件...\n")
        start_time = time.time()
        
        stage2_items = []
        
        async with session.post(url, json=payload) as resp:
            async for line in resp.content:
                line = line.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue
                
                data = json.loads(line[5:].strip())
                event_type = data.get("type")
                elapsed = time.time() - start_time
                
                # 打印关键事件
                if event_type == "meta":
                    councilors = [c["name"] for c in data.get("resolved_councilors", [])]
                    print(f"[{elapsed:6.2f}s] META: 议员 = {councilors}")
                
                elif event_type == "stage1_complete":
                    print(f"[{elapsed:6.2f}s] STAGE1_COMPLETE")
                
                elif event_type == "stage2_start":
                    print(f"[{elapsed:6.2f}s] STAGE2_START")
                
                elif event_type == "stage2_item":
                    item = data.get("data", {})
                    judge = item.get("judge_councilor_name") or item.get("judge_councilor_id") or item.get("model")
                    stage2_items.append({"time": elapsed, "judge": judge})
                    print(f"[{elapsed:6.2f}s] ⭐ STAGE2_ITEM: {judge} 完成评审!")
                
                elif event_type == "stage2_complete":
                    print(f"[{elapsed:6.2f}s] STAGE2_COMPLETE")
                
                elif event_type == "stage3_complete":
                    print(f"[{elapsed:6.2f}s] STAGE3_COMPLETE")
                
                elif event_type == "complete":
                    print(f"[{elapsed:6.2f}s] ✅ 完成")
                    break
        
        # 分析结果
        print("\n" + "=" * 60)
        print("📊 Stage 2 时序分析:")
        print("=" * 60)
        
        if len(stage2_items) >= 2:
            gaps = []
            for i in range(1, len(stage2_items)):
                gap = stage2_items[i]["time"] - stage2_items[i-1]["time"]
                gaps.append(gap)
                print(f"  {stage2_items[i-1]['judge']} → {stage2_items[i]['judge']}: {gap:.2f}s 间隔")
            
            avg_gap = sum(gaps) / len(gaps) if gaps else 0
            print(f"\n  平均间隔: {avg_gap:.2f}s")
            
            if avg_gap < 0.5:
                print("\n⚠️ 结论: 事件几乎同时发送，可能是模型响应过快或存在批量发送问题")
            else:
                print("\n✅ 结论: 事件是增量发送的，间隔明显")
        else:
            print("  ⚠️ 收到的 stage2_item 事件少于 2 个，无法分析")


if __name__ == "__main__":
    print("=" * 60)
    print("Stage 2 SSE 时序测试")
    print("=" * 60)
    try:
        asyncio.run(test_stage2_timing())
    except KeyboardInterrupt:
        print("\n已中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
