# DATA_SCHEMA.md - 数据结构说明

本文档定义系统持久化与前后端交互的核心数据结构。所有结构以当前代码实现为准。

---

## 1. 存储路径

| 路径 | 内容 |
| --- | --- |
| `data/conversations/` | 会话 JSON 文件（每个会话 1 个文件） |
| `backend/personas/` | Persona Prompt 文本文件 |

---

## 2. Conversation 文件结构

文件路径：`data/conversations/{conversation_id}.json`

```json
{
  "id": "<uuid>",
  "created_at": "<iso8601>",
  "title": "New Conversation",
  "messages": [ ... ],
  "active_models": null,
  "active_councilor_ids": ["immanuel_kant", "donald_trump"],
  "active_chairman": "chairman",
  "schema_version": 3,
  "model_assignments": {
    "immanuel_kant": "openrouter:xiaomi/mimo-v2-flash:free",
    "donald_trump": "nim:deepseek-ai/deepseek-v3.1",
    "chairman": "openrouter:xiaomi/mimo-v2-flash:free"
  },
  "assignment_seed": "2026-01-03T03:01:00Z-xxxx",
  "assignment_strategy": "healthy_first"
}
```

### 2.1 schema_version

| 值 | 含义 |
| --- | --- |
| `1` | 旧结构，仅 `active_models` |
| `2` | 引入 `active_councilor_ids` |
| `3` | 固定模型分配（`model_assignments`） |

---

## 3. Message 结构

### 3.1 User Message
```json
{ "role": "user", "content": "..." }
```

### 3.2 Assistant Message
```json
{
  "role": "assistant",
  "stage1": [ ... ],
  "stage2": { ... },
  "stage3": { ... },
  "metadata": { ... }
}
```

说明：
- `stage2` 为对象（非数组）。
- `metadata.thinking` 仅在流式 `/message/stream` 时写入。

---

## 4. Stage1Result

```json
{
  "councilor_id": "immanuel_kant",
  "councilor_name": "康德",
  "model": "openrouter:xiaomi/mimo-v2-flash:free",
  "status": "ok",
  "answer_markdown": "...",
  "attempted_models": ["openrouter:xiaomi/mimo-v2-flash:free"],
  "fallback_used": false,
  "extracted_thinking_count": 0
}
```

失败示例：
```json
{
  "councilor_id": "immanuel_kant",
  "councilor_name": "康德",
  "model": "openrouter:xiaomi/mimo-v2-flash:free",
  "status": "failed",
  "answer_markdown": "",
  "attempted_models": ["openrouter:xiaomi/mimo-v2-flash:free"],
  "error": {"code": "EXECUTION_ERROR", "message": "...", "retryable": true}
}
```

---

## 5. Stage2Result

```json
{
  "skipped": false,
  "skipped_reason": null,
  "reviews": [ ... ],
  "anon_map": {"anon_1": "immanuel_kant", "anon_2": "donald_trump"},
  "judge_failures": []
}
```

`skipped_reason` 取值：
- `insufficient_candidates`
- `all_judges_failed`

### 5.1 Review

```json
{
  "judge_councilor_id": "immanuel_kant",
  "judge_councilor_name": "康德",
  "model": "openrouter:xiaomi/mimo-v2-flash:free",
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

约束：
- `ranking` 必须包含全部 `anon_id`，且不重复。
- `scores` 可选，区间 1-10。
- `per_candidate_comments` 必填，单条最多 200 字符。

### 5.2 Judge Failure

```json
{
  "judge_councilor_id": "immanuel_kant",
  "model": "openrouter:xiaomi/mimo-v2-flash:free",
  "error": {"code": "JUDGE_EXECUTION_ERROR", "message": "...", "retryable": false}
}
```

---

## 6. Stage3Result

```json
{
  "status": "ok",
  "model": "openrouter:xiaomi/mimo-v2-flash:free",
  "response": "...",
  "attempted_models": ["openrouter:xiaomi/mimo-v2-flash:free"],
  "fallback_used": false,
  "fallback_reason": null
}
```

失败示例：
```json
{
  "status": "failed",
  "model": "openrouter:xiaomi/mimo-v2-flash:free",
  "response": "最终总结生成失败: ...",
  "error": {"code": "CHAIRMAN_FAILED", "message": "..."},
  "attempted_models": ["..."]
}
```

---

## 7. Metadata

```json
{
  "anon_to_councilor": {"anon_1": "immanuel_kant"},
  "aggregate_rankings": [
    {"councilor_id": "immanuel_kant", "average_rank": 1.0, "rankings_count": 1}
  ],
  "spec_version": "stage2_v1.2",
  "thinking": {
    "stage1": {
      "immanuel_kant": {
        "model": "openrouter:...",
        "status": "done",
        "steps": [
          {"bullet_id": "immanuel_kant-stage1-1", "title": "...", "detail": null, "t": 0.5}
        ]
      }
    },
    "stage2": { ... },
    "stage3": { ... }
  }
}
```

### 7.1 Thinking Step

```json
{
  "bullet_id": "donald_trump-stage2-1",
  "title": "评估 anon_2 的可行性",
  "detail": "关注成本与时间权衡",
  "target_anon_id": "anon_2",
  "t": 2.31
}
```

约束：
- Stage2 必须包含 `target_anon_id`。
- `thinking` 持久化限制：每阶段每人最多 50 条，总计最多 200 条。

---

## 8. ID 规则

| ID 类型 | 规则 | 示例 |
| --- | --- | --- |
| `conversation_id` | `[a-zA-Z0-9_-]{1,64}` | `550e8400-e29b-41d4-a716-446655440000` |
| `councilor_id` | 小写字母+下划线 | `immanuel_kant` |
| `model` | 推荐带前缀 `provider:` | `openrouter:xiaomi/mimo-v2-flash:free` |
| `anon_id` | `anon_` + 数字 | `anon_1` |
| `bullet_id` | `{cid}-{stage}-{seq}` | `immanuel_kant-stage1-1` |

---

Last updated: 2026-01-23

