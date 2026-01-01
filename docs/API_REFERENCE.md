# API_REFERENCE.md - LLM Council Sentinel API 接口文档

本文档提供 LLM Council Sentinel 后端 API 的完整参考，包括 REST 接口、SSE 流式事件、请求/响应格式及错误码。

---

## 1. API 概览

### 1.1 基础信息

| 项目 | 值 |
|---|---|
| **Base URL** | `http://localhost:8000` (开发) / `http://localhost/api` (Docker) |
| **协议** | HTTP/1.1 |
| **认证** | `X-Admin-Token` Header (仅删除操作) |
| **内容类型** | `application/json` |
| **流式响应** | `text/event-stream` (SSE) |

### 1.2 接口速览表

| 方法 | 路径 | 描述 | 认证 | Rate Limit |
|---|---|---|---|---|
| `GET` | `/` | 健康检查 | 否 | — |
| `GET` | `/health` | Docker 健康检查 | 否 | — |
| `GET` | `/api/councilors` | 获取 Councilor 列表 | 否 | — |
| `GET` | `/api/models` | 获取 Councilor (Legacy) | 否 | — |
| `GET` | `/api/conversations` | 获取对话列表 | 否 | — |
| `POST` | `/api/conversations` | 创建新对话 | 否 | — |
| `GET` | `/api/conversations/{id}` | 获取单个对话 | 否 | — |
| `DELETE` | `/api/conversations/{id}` | 删除对话 | **是** | — |
| `POST` | `/api/conversations/bulk-delete` | 批量删除对话 | **是** | — |
| `POST` | `/api/conversations/{id}/message` | 发送消息 (同步) | 否 | 5/min |
| `POST` | `/api/conversations/{id}/message/stream` | 发送消息 (流式) | 否 | 5/min |

---

## 2. 健康检查接口

### 2.1 GET `/`

**描述**: 服务健康检查

**请求**:
```http
GET / HTTP/1.1
```

**响应**:
```json
{
  "status": "ok",
  "service": "LLM Council API"
}
```

---

### 2.2 GET `/health`

**描述**: Docker 容器健康检查

**响应**:
```json
{
  "status": "ok"
}
```

---

## 3. Councilor 接口

### 3.1 GET `/api/councilors`

**描述**: 获取当前 Councilor 配置及健康状态

**查询参数**:

| 参数 | 类型 | 默认 | 描述 |
|---|---|---|---|
| `refresh` | boolean | `false` | 是否强制刷新健康状态 |

**请求示例**:
```http
GET /api/councilors?refresh=true HTTP/1.1
```

**响应结构**:
```json
{
  "version": "2.1-health-v3",
  "councilors": [
    {
      "id": "immanuel_kant",
      "name": "康德",
      "model": "xiaomi/mimo-v2-flash:free",
      "avatar": "🧠",
      "active": true,
      "healthy": true,
      "health_error": null,
      "health_checked_at": "2026-01-01T22:00:00Z"
    }
  ],
  "chairman": {
    "id": "chairman",
    "name": "共识主席",
    "model": "xiaomi/mimo-v2-flash:free",
    "avatar": "🪶",
    "active": true,
    "healthy": true
  },
  "meta": {
    "skipped": false,
    "next_allowed_at": "2026-01-01T22:01:00Z"
  }
}
```

**响应字段说明**:

| 字段 | 类型 | 描述 |
|---|---|---|
| `version` | string | API 版本标识 |
| `councilors` | array | Councilor 列表 |
| `councilors[].id` | string | Councilor 唯一标识 |
| `councilors[].name` | string | 显示名称 |
| `councilors[].model` | string | 当前使用的模型 ID |
| `councilors[].avatar` | string | Emoji 头像 |
| `councilors[].active` | boolean | 是否激活 |
| `councilors[].healthy` | boolean | 是否健康可用 |
| `councilors[].health_error` | string | 健康检查错误信息 |
| `councilors[].health_checked_at` | string | 最后健康检查时间 (ISO 8601) |
| `chairman` | object | Chairman 信息 |
| `meta.skipped` | boolean | 是否跳过刷新 (冷却中) |
| `meta.next_allowed_at` | string | 下次允许刷新时间 |

---

### 3.2 GET `/api/models` (Legacy)

**描述**: `/api/councilors` 的别名，保持向后兼容

---

## 4. 对话接口

### 4.1 GET `/api/conversations`

**描述**: 获取所有对话的元数据列表

**响应结构**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2026-01-01T10:00:00Z",
    "title": "如何评价AI的发展",
    "message_count": 3
  }
]
```

**响应字段说明**:

| 字段 | 类型 | 描述 |
|---|---|---|
| `id` | string | 对话 UUID |
| `created_at` | string | 创建时间 (ISO 8601) |
| `title` | string | 对话标题 |
| `message_count` | integer | 消息数量 |

---

### 4.2 POST `/api/conversations`

**描述**: 创建新对话

**请求体**:
```json
{
  "councilor_ids": ["immanuel_kant", "donald_trump"]
}
```

| 字段 | 类型 | 必填 | 描述 |
|---|---|---|---|
| `councilor_ids` | array | 否 | 指定参与的 Councilor ID 列表 |

**响应结构**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-01-01T10:00:00Z",
  "title": "新对话",
  "messages": [],
  "active_councilor_ids": ["immanuel_kant", "donald_trump"],
  "active_chairman": "chairman",
  "schema_version": 2
}
```

---

### 4.3 GET `/api/conversations/{id}`

**描述**: 获取单个对话详情

**路径参数**:

| 参数 | 类型 | 描述 |
|---|---|---|
| `id` | string | 对话 UUID |

**响应结构**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-01-01T10:00:00Z",
  "title": "如何评价AI的发展",
  "messages": [
    {
      "role": "user",
      "content": "如何评价AI的发展？"
    },
    {
      "role": "assistant",
      "stage1": [...],
      "stage2": {...},
      "stage3": {...},
      "metadata": {...}
    }
  ],
  "active_councilor_ids": ["immanuel_kant", "donald_trump", "hideo_kojima"],
  "active_chairman": "chairman",
  "schema_version": 2
}
```

**错误响应**:
| 状态码 | 描述 |
|---|---|
| 404 | 对话不存在 |

---

### 4.4 DELETE `/api/conversations/{id}`

**描述**: 删除单个对话

**认证**: 需要 `X-Admin-Token` Header

**请求示例**:
```http
DELETE /api/conversations/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
X-Admin-Token: your-secret-token
```

**成功响应**: `204 No Content`

**错误响应**:
| 状态码 | 错误码 | 描述 |
|---|---|---|
| 400 | — | 无效的对话 ID 格式 |
| 401 | — | 未授权 (Token 无效) |
| 500 | `DELETE_FAILED` | 删除失败 (权限/文件锁定) |

---

### 4.5 POST `/api/conversations/bulk-delete`

**描述**: 批量删除对话

**认证**: 需要 `X-Admin-Token` Header

**请求体**:
```json
{
  "ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "660e8400-e29b-41d4-a716-446655440001"
  ]
}
```

| 字段 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `ids` | array | 最多 50 个 | 要删除的对话 ID 列表 |

**响应结构**:
```json
{
  "deletedIds": ["550e8400-e29b-41d4-a716-446655440000"],
  "failed": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "reason": "not_found"
    }
  ]
}
```

---

## 5. 消息接口

### 5.1 POST `/api/conversations/{id}/message` (同步)

**描述**: 发送消息并等待完整响应

**Rate Limit**: 5 请求/分钟

**请求体**:
```json
{
  "content": "如何评价AI的发展？",
  "councilor_ids": ["immanuel_kant", "donald_trump"],
  "enable_thinking": true
}
```

| 字段 | 类型 | 必填 | 约束 | 描述 |
|---|---|---|---|---|
| `content` | string | 是 | 最大 1000 字符 | 用户消息内容 |
| `councilor_ids` | array | 否 | — | 临时指定参与的 Councilor |
| `enable_thinking` | boolean | 否 | 默认 `true` | 是否启用 Thinking 工具 |

**响应结构**:
```json
{
  "stage1": [
    {
      "councilor_id": "immanuel_kant",
      "councilor_name": "康德",
      "model": "xiaomi/mimo-v2-flash:free",
      "status": "ok",
      "answer_markdown": "## 我的观点\n...",
      "answer_summary": "AI发展需考虑伦理...",
      "judge_card": {
        "stance": "谨慎乐观",
        "core_reasons": ["..."],
        "assumptions": ["..."],
        "risks": ["..."],
        "actionables": ["..."]
      },
      "attempted_models": ["xiaomi/mimo-v2-flash:free"],
      "fallback_used": false
    }
  ],
  "stage2": {
    "skipped": false,
    "reviews": [
      {
        "judge_councilor_id": "immanuel_kant",
        "judge_councilor_name": "康德",
        "model": "xiaomi/mimo-v2-flash:free",
        "ranking": ["anon_1", "anon_2"],
        "scores": {"anon_1": 8, "anon_2": 6},
        "rationale": "..."
      }
    ],
    "anon_map": {"anon_1": "immanuel_kant", "anon_2": "donald_trump"}
  },
  "stage3": {
    "status": "ok",
    "model": "xiaomi/mimo-v2-flash:free",
    "response": "## 综合观点\n...",
    "attempted_models": ["xiaomi/mimo-v2-flash:free"],
    "fallback_used": false
  },
  "metadata": {
    "anon_to_councilor": {...},
    "aggregate_rankings": [
      {"councilor_id": "immanuel_kant", "average_rank": 1.5, "rankings_count": 2}
    ],
    "spec_version": "stage2_v1.2"
  }
}
```

---

### 5.2 POST `/api/conversations/{id}/message/stream` (流式)

**描述**: 发送消息并通过 SSE 流式接收响应

**Rate Limit**: 5 请求/分钟

**请求体**: 同 5.1

**响应类型**: `text/event-stream`

**SSE 事件流详见 [第 6 节](#6-sse-事件协议)**

---

## 6. SSE 事件协议

### 6.1 事件流序列图

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SSE 事件流时序                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────┐                                                                       │
│  │ meta │ ─────▶ 解析 councilor、chairman 信息                                  │
│  └──────┘                                                                       │
│      │                                                                          │
│      ▼                                                                          │
│  ┌──────────────┐   ┌──────────┐   ┌──────────────┐   ┌────────────────┐        │
│  │ stage1_start │ ─▶│ thinking │*─▶│ stage1_item  │*─▶│ stage1_complete│        │
│  └──────────────┘   └──────────┘   └──────────────┘   └────────────────┘        │
│                                                             │                   │
│                                                             ▼                   │
│  ┌──────────────┐   ┌──────────┐   ┌──────────────┐   ┌────────────────┐        │
│  │ stage2_start │ ─▶│ thinking │*─▶│ stage2_item  │*─▶│ stage2_complete│        │
│  └──────────────┘   └──────────┘   └──────────────┘   └────────────────┘        │
│                                                             │                   │
│                                                             ▼                   │
│  ┌──────────────┐   ┌──────────┐   ┌────────────────┐                           │
│  │ stage3_start │ ─▶│ thinking │*─▶│ stage3_complete│                           │
│  └──────────────┘   └──────────┘   └────────────────┘                           │
│                                           │                                     │
│                                           ▼                                     │
│  ┌────────────────┐   ┌──────────┐                                              │
│  │ title_complete │ ─▶│ complete │                                              │
│  └────────────────┘   └──────────┘                                              │
│                                                                                 │
│  * = 可出现 0 到多次                                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 事件类型详解

#### 6.2.1 `meta` - 元信息

连接建立后首条事件，包含解析后的 Councilor 和 Chairman 信息。

```json
{
  "type": "meta",
  "resolved_councilor_ids": ["immanuel_kant", "donald_trump", "hideo_kojima"],
  "resolved_councilors": [
    {"id": "immanuel_kant", "name": "康德", "avatar": "🧠", "model": "xiaomi/mimo-v2-flash:free"}
  ],
  "chairman": {"id": "chairman", "name": "共识主席", "avatar": "🪶", "model": "xiaomi/mimo-v2-flash:free"},
  "ignored_ids": [],
  "spec_version": "stage2_v1.2"
}
```

---

#### 6.2.2 `stage1_start` - Stage1 开始

```json
{"type": "stage1_start"}
```

---

#### 6.2.3 `thinking` - 思考过程

实时推送 Councilor 的思考标题流。

```json
{
  "type": "thinking",
  "stage": "stage1",
  "councilor_id": "immanuel_kant",
  "model": "xiaomi/mimo-v2-flash:free",
  "bullet_id": "immanuel_kant-stage1-1",
  "title": "分析问题背景",
  "detail": "首先需要理解用户提问的具体语境...",
  "op": "append",
  "t": 1.23
}
```

| 字段 | 类型 | 描述 |
|---|---|---|
| `stage` | string | 当前阶段: `stage1` / `stage2` / `stage3` |
| `councilor_id` | string | 发出 Thinking 的 Councilor ID |
| `model` | string | 使用的模型 |
| `bullet_id` | string | Thinking 条目唯一 ID |
| `title` | string | Thinking 标题 |
| `detail` | string | Thinking 详情 (可选) |
| `op` | string | 操作类型: `append` (新增) / `update` (更新) |
| `t` | number | 相对时间戳 (秒) |

---

#### 6.2.4 `stage1_item` - Stage1 结果项

单个 Councilor 完成响应时触发。

```json
{
  "type": "stage1_item",
  "data": {
    "councilor_id": "immanuel_kant",
    "councilor_name": "康德",
    "model": "xiaomi/mimo-v2-flash:free",
    "status": "ok",
    "answer_markdown": "## 我的观点\n...",
    "answer_summary": "...",
    "judge_card": {...},
    "attempted_models": ["xiaomi/mimo-v2-flash:free"],
    "fallback_used": false
  }
}
```

---

#### 6.2.5 `stage1_answer_delta` - Stage1 回答增量

流式回答文本增量。

```json
{
  "type": "stage1_answer_delta",
  "councilor_id": "immanuel_kant",
  "delta": "## 我的"
}
```

---

#### 6.2.6 `stage1_answer_done` - Stage1 回答完成

某个 Councilor 回答完成。

```json
{
  "type": "stage1_answer_done",
  "councilor_id": "immanuel_kant"
}
```

---

#### 6.2.7 `stage1_complete` - Stage1 全部完成

所有 Councilor 完成 Stage1。

```json
{
  "type": "stage1_complete",
  "data": [...]
}
```

---

#### 6.2.8 `stage2_start` - Stage2 开始

```json
{
  "type": "stage2_start",
  "anon_map": {"anon_1": "immanuel_kant", "anon_2": "donald_trump"},
  "skipped": false
}
```

若跳过 Stage2：
```json
{
  "type": "stage2_start",
  "skipped": true,
  "skipped_reason": "insufficient_candidates"
}
```

---

#### 6.2.9 `stage2_item` - Stage2 评审项

```json
{
  "type": "stage2_item",
  "data": {
    "judge_councilor_id": "immanuel_kant",
    "judge_councilor_name": "康德",
    "model": "xiaomi/mimo-v2-flash:free",
    "ranking": ["anon_1", "anon_2"],
    "scores": {"anon_1": 8, "anon_2": 6},
    "rationale": "..."
  }
}
```

---

#### 6.2.10 `stage2_complete` - Stage2 完成

```json
{
  "type": "stage2_complete",
  "data": {
    "skipped": false,
    "reviews": [...],
    "anon_map": {...},
    "judge_failures": []
  },
  "metadata": {
    "anon_to_councilor": {...},
    "aggregate_rankings": [
      {"councilor_id": "immanuel_kant", "average_rank": 1.5, "rankings_count": 2}
    ]
  }
}
```

---

#### 6.2.11 `stage3_start` - Stage3 开始

```json
{"type": "stage3_start"}
```

---

#### 6.2.12 `stage3_answer_delta` - Stage3 回答增量

```json
{
  "type": "stage3_answer_delta",
  "councilor_id": "chairman",
  "delta": "## 综合"
}
```

---

#### 6.2.13 `stage3_complete` - Stage3 完成

```json
{
  "type": "stage3_complete",
  "data": {
    "status": "ok",
    "model": "xiaomi/mimo-v2-flash:free",
    "response": "## 综合观点\n...",
    "attempted_models": ["xiaomi/mimo-v2-flash:free"],
    "fallback_used": false
  }
}
```

---

#### 6.2.14 `title_complete` - 标题生成完成

仅首条消息时触发。

```json
{
  "type": "title_complete",
  "data": {"title": "AI发展讨论"}
}
```

---

#### 6.2.15 `complete` - 流程完成

```json
{"type": "complete"}
```

---

#### 6.2.16 `error` - 错误

```json
{
  "type": "error",
  "message": "Error description"
}
```

---

## 7. 错误码

### 7.1 HTTP 状态码

| 状态码 | 描述 |
|---|---|
| 200 | 成功 |
| 204 | 成功 (无内容) |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

### 7.2 业务错误码

| 错误码 | 描述 | HTTP 状态码 |
|---|---|---|
| `RATE_LIMIT_EXCEEDED` | 请求频率超限 | 429 |
| `CONTENT_TOO_LONG` | 消息内容超过 1000 字符 | 400 |
| `VALIDATION_ERROR` | 请求参数校验失败 | 400 |
| `DELETE_FAILED` | 删除操作失败 | 500 |

### 7.3 错误响应格式

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求过于频繁，请稍后再试",
    "message_en": "Too many requests, please try again later",
    "details": {
      "retry_after": 60
    }
  }
}
```

---

## 8. Rate Limit

### 8.1 限制策略

| 接口 | 限制 |
|---|---|
| `/api/conversations/{id}/message` | 5 请求/分钟 (按 IP) |
| `/api/conversations/{id}/message/stream` | 5 请求/分钟 (按 IP) |

### 8.2 IP 识别

优先级：`X-Forwarded-For` → `X-Real-IP` → 直连 IP

### 8.3 超限响应

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
Content-Type: application/json

{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求过于频繁，请稍后再试"
  }
}
```

---

## 9. 示例代码

### 9.1 JavaScript (Fetch)

```javascript
// 创建对话
const response = await fetch('/api/conversations', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({councilor_ids: ['immanuel_kant', 'donald_trump']})
});
const conversation = await response.json();

// 流式发送消息
const eventSource = new EventSource(
  `/api/conversations/${conversation.id}/message/stream`
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.type, data);
};
```

### 9.2 Python (httpx)

```python
import httpx
import json

async def send_message_stream(conversation_id: str, content: str):
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            f"http://localhost:8000/api/conversations/{conversation_id}/message/stream",
            json={"content": content, "enable_thinking": True}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event = json.loads(line[6:])
                    print(event["type"], event)
```

---

*文档版本: 1.0.0 | 最后更新: 2026-01-01*
