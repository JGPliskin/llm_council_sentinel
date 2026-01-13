#!/usr/bin/env python3
"""
NIM API 测试结果分析脚本
读取 .jsonl 结果文件，生成统计报告
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
import statistics

def analyze_results(file_path: str, output_path: str = None):
    path = Path(file_path)
    if not path.exists():
        print(f"Error: 文件 {file_path} 不存在", file=sys.stderr)
        return

    print(f"Loading {path.name}...", file=sys.stderr)
    
    total = 0
    success = 0
    errors = 0
    
    # 统计数据结构
    model_stats = defaultdict(lambda: {
        "count": 0, 
        "success": 0, 
        "latency": [], 
        "ttft": [], # Time To First Token (if available)
        "input_tokens": [],
        "output_tokens": [],
        "total_tokens": [],
        "tps": [], # Tokens Per Second
        "errors": []
    })
    
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                total += 1
                model = data.get("model", "unknown")
                status = data.get("status")
                
                model_stats[model]["count"] += 1
                
                if status == "success":
                    success += 1
                    model_stats[model]["success"] += 1
                    
                    # 延时
                    latency = data.get("total_latency_ms", 0)
                    model_stats[model]["latency"].append(latency)
                    
                    # Token 统计
                    in_tok = data.get("input_tokens", 0)
                    out_tok = data.get("output_tokens", 0)
                    model_stats[model]["input_tokens"].append(in_tok)
                    model_stats[model]["output_tokens"].append(out_tok)
                    model_stats[model]["total_tokens"].append(in_tok + out_tok)
                    
                    # TPS
                    tps = data.get("tokens_per_second", 0)
                    if tps:
                        model_stats[model]["tps"].append(tps)
                    elif latency > 0:
                        # 如果没有直接提供 TPS，尝试计算
                        model_stats[model]["tps"].append(out_tok / (latency / 1000))

                else:
                    errors += 1
                    err_msg = data.get("error_message", "unknown")
                    model_stats[model]["errors"].append(err_msg)
                    
            except json.JSONDecodeError:
                continue

    # 准备输出内容
    lines = []
    lines.append("\n# NIM API 测试报告\n")
    lines.append(f"- **总请求数**: {total}")
    lines.append(f"- **成功**: {success} ({success/total*100:.1f}%)" if total > 0 else "- **成功**: 0")
    lines.append(f"- **失败**: {errors} ({errors/total*100:.1f}%)\n" if total > 0 else "- **失败**: 0")
    
    lines.append("## 模型性能排行\n")
    # 更新表头，增加 Token 和 TPS 指标
    lines.append("| 模型 | 请求数 | 成功率 | 平均延时(ms) | P99延时(ms) | 平均TPS | 平均Output Tokens | 错误信息 |")
    lines.append("|---|---|---|---|---|---|---|---|")
    
    # 计算统计数据并排序
    valid_models = []
    for model, stats in model_stats.items():
        count = stats["count"]
        succ = stats["success"]
        lats = stats["latency"]
        tps_list = stats["tps"]
        out_toks = stats["output_tokens"]
        
        avg_lat = statistics.mean(lats) if lats else 0
        p99_lat = sorted(lats)[int(len(lats)*0.99)] if lats else 0
        
        avg_tps = statistics.mean(tps_list) if tps_list else 0
        avg_out_tok = statistics.mean(out_toks) if out_toks else 0
        
        err_msgs = [e.replace('\n', ' ') for e in list(set(stats["errors"]))]
        err_str = "; ".join(err_msgs)[:50] + "..." if err_msgs else "-"
        
        valid_models.append({
            "model": model,
            "count": count,
            "success_rate": succ/count*100 if count > 0 else 0,
            "avg_latency": avg_lat,
            "p99_latency": p99_lat,
            "avg_tps": avg_tps,
            "avg_out_tok": avg_out_tok,
            "errors": err_str
        })
        
    # 按平均延时排序 (成功的排前面，失败的排后面)
    valid_models.sort(key=lambda x: (x["success_rate"] == 0, x["avg_latency"]))
    
    for m in valid_models:
        lines.append(f"| {m['model']} | {m['count']} | {m['success_rate']:.0f}% | {m['avg_latency']:.0f} | {m['p99_latency']:.0f} | {m['avg_tps']:.1f} | {m['avg_out_tok']:.1f} | {m['errors']} |")

    # 写入文件
    if not output_path:
        output_path = path.with_suffix('.md')
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"报告已生成: {output_path}", file=sys.stderr)
    except Exception as e:
        print(f"写入报告失败: {e}", file=sys.stderr)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        analyze_results(input_file, output_file)
    else:
        # 自动查找最新的 jsonl 文件
        base_dir = Path(__file__).parent
        files = list(base_dir.glob("nim_test_results_*.jsonl"))
        if not files:
            print("未找到结果文件", file=sys.stderr)
        else:
            # 按修改时间排序，取最新的
            latest_file = max(files, key=lambda p: p.stat().st_mtime)
            analyze_results(latest_file)
