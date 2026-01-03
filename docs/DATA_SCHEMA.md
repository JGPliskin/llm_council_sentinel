# DATA_SCHEMA.md - LLM Council Sentinel 数据模型文档

本文档定义 LLM Council Sentinel 的核心数据结构、字段说明及数据关系，用于存储层与前后端数据交换。

---

## 1. 数据存储概览

### 1.1 存储路径

| 路径 | 描述 |
|---|---|
| `data/conversations/` | 对话 JSON 文件 |
| `backend/personas/` | Persona 文本文件 |

### 1.2 Conversation 文件结构

**文件路径**：`data/conversations/{conversation_id}.json`

```json
{
  "id": "<uuid>",
  "created_at": "<iso8601>",
  "title": "New Conversation",
  "messages": [ ... ],
  "active_models": null,
  "active_councilor_ids": ["immanuel_kant", "donald_trump", "hideo_kojima"],
  "active_chairman": "chairman",
  "model_assignments": {
    "immanuel_kant": "nvidia/nemotron-3-nano-30b-a3b:free",
    "donald_trump": "xiaomi/mimo-v2-flash:free",
    "chairman": "xiaomi/mimo-v2-flash:free"
  },
  "assignment_seed": "2026-01-03T03:01:00Z-xxxx",
  "assignment_strategy": "healthy_first",
  "schema_version": 3
}
```

---

## 2. Message 结构

### 2.1 User Message

```json
{ "role": "user", "content": "..." }
```

### 2.2 Assistant Message

```json
{
  "role": "assistant",
  "stage1": [ ... ],
  "stage2": { ... },
  "stage3": { ... },
  "metadata": { ... }
}
```

**注意**：
- `stage2` 为对象结构（非数组）
- 非流式请求不会写入 `metadata.thinking`

---

## 3. Stage1Result

```json
{
  "councilor_id": "immanuel_kant",
  "councilor_name": "康德",
  "model": "xiaomi/mimo-v2-flash:free",
  "status": "ok",
  "answer_markdown": "...",
  "attempted_models": ["xiaomi/mimo-v2-flash:free"],
  "fallback_used": false,
  "extracted_thinking_count": 0
}
```

失败示例：

```json
{
  "councilor_id": "immanuel_kant",
  "councilor_name": "康德",
  "model": "xiaomi/mimo-v2-flash:free",
  "status": "failed",
  "answer_markdown": "",
  "attempted_models": ["xiaomi/mimo-v2-flash:free"],
  "error": {"code": "EXECUTION_ERROR", "message": "...", "retryable": true}
}
```

---

## 4. Stage2Result

```json
{
  "skipped": false,
  "skipped_reason": null,
  "reviews": [ ... ],
  "anon_map": {"anon_1": "immanuel_kant", "anon_2": "donald_trump"},
  "judge_failures": []
}
```

### 4.1 Review 结构

```json
{
  "judge_councilor_id": "immanuel_kant",
  "judge_councilor_name": "康德",
  "model": "xiaomi/mimo-v2-flash:free",
  "ranking": ["anon_1", "anon_2"],
  "scores": {"anon_1": 8, "anon_2": 6},
  "rationale": "...",
  "per_candidate_comments": {
    "anon_1": "...",
    "anon_2": "..."
  },
  "raw_response": "{...}",
  "fallback_used": false
}
```

### 4.2 Judge Failure 结构

```json
{
  "judge_councilor_id": "immanuel_kant",
  "model": "xiaomi/mimo-v2-flash:free",
  "error": {"code": "JUDGE_EXECUTION_ERROR", "message": "...", "retryable": false}
}
```

**`skipped_reason` 值**：
- `insufficient_candidates`
- `all_judges_failed`

---

## 5. Stage3Result

```json
{
  "status": "ok",
  "model": "xiaomi/mimo-v2-flash:free",
  "response": "...",
  "attempted_models": ["xiaomi/mimo-v2-flash:free"],
  "fallback_used": false,
  "fallback_reason": null
}
```

失败示例：

```json
{
  "status": "failed",
  "model": "xiaomi/mimo-v2-flash:free",
  "response": "最终总结生成失败: ...",
  "error": {"code": "CHAIRMAN_FAILED", "message": "..."},
  "attempted_models": ["..."]
}
```

---

## 6. Metadata

```json
{
  "anon_to_councilor": {"anon_1": "immanuel_kant"},
  "aggregate_rankings": [{"councilor_id": "immanuel_kant", "average_rank": 1.0, "rankings_count": 1}],
  "spec_version": "stage2_v1.2",
  "thinking": {
    "stage1": {"immanuel_kant": {"model": "...", "status": "done", "steps": [ ... ]}},
    "stage2": {"donald_trump": {"model": "...", "status": "thinking", "steps": [ ... ]}},
    "stage3": {"chairman": {"model": "...", "status": "done", "steps": [ ... ]}}
  }
  }
}
```

### 6.1 Thinking Step 结构

```json
{
  "bullet_id": "donald_trump-stage2-1",
  "title": "评估 anon_2 的可行性",
  "detail": "关注成本与时间权衡",
  "target_anon_id": "anon_2",
  "t": 2.31
}
```

**注意**：`target_anon_id` 仅 Stage2 有意义，且仅当模型按约定返回时才存在。

---

## 7. ID 约束

| ID 类型 | 约束 | 示例 |
|---|---|---|
| `conversation_id` | UUID v4 | `550e8400-e29b-41d4-a716-446655440000` |
| `councilor_id` | 小写字母+下划线 | `immanuel_kant` |
| `model` | OpenRouter 格式 | `xiaomi/mimo-v2-flash:free` |
| `anon_id` | `anon_` + 数字 | `anon_1` |
| `bullet_id` | `{cid}-{stage}-{seq}` | `immanuel_kant-stage1-1` |

---

*Last updated: 2026-01-03*
