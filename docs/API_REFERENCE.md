# API_REFERENCE.md - LLM Council Sentinel API 接口文档

本文档提供 LLM Council Sentinel 后端 API 的完整参考，包括 REST 接口、SSE 流式事件、请求/响应格式及错误码。

---

## 1. 基础信息

### 1.1 Base URL

| 场景 | Base URL | 说明 |
|---|---|---|
| 本地开发（后端） | `http://localhost:8010` | `uvicorn main:app --port 8010` 默认端口 |
| Docker + Nginx | `http://localhost/api` | Nginx 反向代理 `/api/*` → `backend:8008` |

> 前端默认 `API_BASE` 固定为 `http://localhost:8010`（见 `frontend/src/api.js`）。
> 若使用 Docker/Nginx，需要手动修改 `API_BASE` 或提供与 8010 兼容的代理。

### 1.2 协议与认证

- 协议：HTTP/1.1
- 内容类型：`application/json`
- 流式响应：`text/event-stream` (SSE)
- 认证：`X-Admin-Token`（仅删除操作）

### 1.3 限流

| 接口 | 限流 |
|---|---|
| `/api/conversations/{id}/message` | 5/min (按 IP) |
| `/api/conversations/{id}/message/stream` | 5/min (按 IP) |

---

### 1.4 供应商与模型标识

- `model` 字段均为实际模型 ID，可能来自 OpenRouter 或 NIM。
- 当模型由 `GLOBAL_MODEL_POOL.provider` 指定为 `nim` 时，无需 `nim:` 前缀；若外部传入 `nim:` 前缀，会被剥离并标准化。
- API 响应中不直接返回 `provider` 字段，如需区分请对照 `GLOBAL_MODEL_POOL` 配置。

## 2. API 概览

| 方法 | 路径 | 描述 | 认证 |
|---|---|---|---|
| `GET` | `/` | 健康检查 | 否 |
| `GET` | `/health` | Docker 健康检查 | 否 |
| `GET` | `/api/councilors` | 获取 Councilor 列表 | 否 |
| `GET` | `/api/models` | `/api/councilors` 别名 | 否 |
| `GET` | `/api/conversations` | 获取对话列表 | 否 |
| `POST` | `/api/conversations` | 创建新对话 | 否 |
| `GET` | `/api/conversations/{id}` | 获取对话详情 | 否 |
| `DELETE` | `/api/conversations/{id}` | 删除对话 | 是 |
| `POST` | `/api/conversations/bulk-delete` | 批量删除 | 是 |
| `POST` | `/api/conversations/{id}/message` | 发送消息（同步） | 否 |
| `POST` | `/api/conversations/{id}/message/stream` | 发送消息（流式） | 否 |

---

## 3. Councilor 接口

### 3.1 GET `/api/councilors`

**查询参数**:

| 参数 | 类型 | 默认 | 描述 |
|---|---|---|---|
| `refresh` | boolean | `false` | 是否强制刷新健康状态 |

**响应示例**:

```json
{
  "version": "2.1-health-v3",
  "councilors": [
    {
      "id": "immanuel_kant",
      "name": "康德",
      "model": "xiaomi/mimo-v2-flash:free",
      "avatar": "??",
      "active": true,
      "healthy": true,
      "health_error": null,
      "health_checked_at": "2026-01-03T03:00:00Z"
    }
  ],
  "chairman": {
    "id": "chairman",
    "name": "共识主席",
    "model": "xiaomi/mimo-v2-flash:free",
    "avatar": "??",
    "active": true,
    "healthy": true
  },
  "meta": {
    "refresh_skipped": false,
    "server_time": "2026-01-03T03:00:01Z"
  }
}
```

**字段说明**:

| 字段 | 类型 | 描述 |
|---|---|---|
| `councilors[].id` | string | Councilor ID |
| `councilors[].model` | string | 默认模型 ID（非固定分配结果） |
| `healthy` | boolean | 当前健康状态 |
| `health_error` | string | 最近一次错误（如有） |

---

## 4. 对话接口

### 4.1 POST `/api/conversations`

**描述**：创建新对话并进行固定模型分配。

**请求体**:

```json
{
  "councilor_ids": ["immanuel_kant", "donald_trump"]
}
```

**响应示例**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-01-03T03:01:00Z",
  "title": "New Conversation",
  "messages": [],
  "active_councilor_ids": ["immanuel_kant", "donald_trump"],
  "active_chairman": "chairman",
  "schema_version": 3,
  "model_assignments": {
    "immanuel_kant": "nvidia/nemotron-3-nano-30b-a3b:free",
    "donald_trump": "xiaomi/mimo-v2-flash:free",
    "chairman": "xiaomi/mimo-v2-flash:free"
  },
  "assignment_seed": "2026-01-03T03:01:00Z-xxxx",
  "assignment_strategy": "healthy_first"
}
```

**说明**：
- 固定分配失败时，`model_assignments` 可能为空，`schema_version` 回退为 2。

---

### 4.2 GET `/api/conversations/{id}`

**描述**：获取单个对话详情。

**错误响应**：
- `404` 对话不存在

---

### 4.3 DELETE `/api/conversations/{id}`

**描述**：删除单个对话。

**认证**：`X-Admin-Token`

---

### 4.4 POST `/api/conversations/bulk-delete`

**描述**：批量删除对话。

**请求体**:

```json
{ "ids": ["uuid1", "uuid2"] }
```

**响应示例**:

```json
{
  "deletedIds": ["uuid1"],
  "failed": [{"id": "uuid2", "reason": "not_found"}]
}
```

---

## 5. 消息接口

### 5.1 POST `/api/conversations/{id}/message`

**描述**：同步执行三阶段并返回完整结果。

**请求体**:

```json
{
  "content": "...",
  "councilor_ids": ["immanuel_kant", "donald_trump"],
  "enable_thinking": true
}
```

**规则**：
- `councilor_ids` 在 `schema_version >= 3` 时会被忽略
- 同步接口不返回 thinking 流式事件，且 **不会持久化** thinking

---

### 5.2 POST `/api/conversations/{id}/message/stream`

**描述**：流式 SSE 返回三阶段过程。

**请求体**：同 5.1

---

## 6. SSE 事件协议

### 6.1 事件流顺序

```
meta → stage1_start → [eta_update]* → [thinking]* → [stage1_item]* → stage1_complete
     → stage2_start → [eta_update]* → [thinking]* → [stage2_item]* → stage2_complete
     → stage3_start → [thinking]* → stage3_complete
     → [title_complete] → complete
```

### 6.2 事件定义

#### 6.2.1 `meta`

```json
{
  "type": "meta",
  "resolved_councilor_ids": ["immanuel_kant", "donald_trump"],
  "resolved_councilors": [
    {"id": "immanuel_kant", "name": "康德", "avatar": "??", "model": "xiaomi/mimo-v2-flash:free"}
  ],
  "chairman": {"id": "chairman", "name": "共识主席", "avatar": "??", "model": "xiaomi/mimo-v2-flash:free"},
  "ignored_ids": [],
  "spec_version": "stage2_v1.2",
  "model_assignments": {"immanuel_kant": "...", "chairman": "..."}
}
```

#### 6.2.2 `thinking`

```json
{
  "type": "thinking",
  "stage": "stage2",
  "councilor_id": "donald_trump",
  "model": "xiaomi/mimo-v2-flash:free",
  "bullet_id": "donald_trump-stage2-1",
  "title": "评估 anon_2 的可行性",
  "detail": "关注成本与时间权衡",
  "op": "append",
  "target_anon_id": "anon_2",
  "t": 2.31
}
```

**说明**：
- `stage` 可为 `stage1`, `stage2`, `stage3`。
- `target_anon_id` 仅 Stage2 有意义；若缺失，前端可视为 global 并忽略或标注。
- `title` 和 `detail` 字段用于流式结构化思考展示。Stage 3 时，这些字段来自 Chairman 的 `emit_thinking` tool calls。

#### 6.2.3 `stage1_answer_delta`

```json
{ "type": "stage1_answer_delta", "councilor_id": "immanuel_kant", "delta": "..." }
```

#### 6.2.4 `stage1_answer_done`

```json
{ "type": "stage1_answer_done", "councilor_id": "immanuel_kant" }
```

#### 6.2.5 `eta_update`

```json
{
  "type": "eta_update",
  "stage": "stage1",
  "councilor_id": "immanuel_kant",
  "eta_ms_remaining": 5200,
  "model": "xiaomi/mimo-v2-flash:free",
  "reason": "queue_start"
}
```

**说明**：
- `councilor_id` 在 stage2 仍使用同字段承载 judge_id。
- `reason`: `queue_start` / `done`。
- Stage2 被跳过时，后端会对每个 judge 推送一次 `eta_update`（`reason=done`）以结束 HUD 进度。

#### 6.2.6 `stage2_start`

```json
{ "type": "stage2_start", "anon_map": {"anon_1": "immanuel_kant"}, "skipped": false }
```

若跳过：

```json
{ "type": "stage2_start", "skipped": true, "skipped_reason": "insufficient_candidates" }
```

#### 6.2.7 `stage2_item`

```json
{
  "type": "stage2_item",
  "data": {
    "judge_councilor_id": "immanuel_kant",
    "judge_councilor_name": "康德",
    "model": "xiaomi/mimo-v2-flash:free",
    "ranking": ["anon_1", "anon_2"],
    "scores": {"anon_1": 8, "anon_2": 6},
    "rationale": "...",
    "per_candidate_comments": {"anon_1": "...", "anon_2": "..."},
    "raw_response": "{...}",
    "fallback_used": false
  }
}
```

#### 6.2.8 `stage2_complete`

```json
{
  "type": "stage2_complete",
  "data": {
    "skipped": false,
    "reviews": [...],
    "anon_map": {"anon_1": "immanuel_kant"},
    "judge_failures": []
  },
  "metadata": {
    "anon_to_councilor": {"anon_1": "immanuel_kant"},
    "aggregate_rankings": [{"councilor_id": "immanuel_kant", "average_rank": 1.0, "rankings_count": 1}]
  }
}
```

#### 6.2.9 `stage3_answer_delta`

```json
{ "type": "stage3_answer_delta", "councilor_id": "chairman", "delta": "..." }
```

#### 6.2.10 `complete`

```json
{ "type": "complete" }
```

---

## 7. 错误码

### 7.1 HTTP 状态码

| 状态码 | 描述 |
|---|---|
| 400 | 参数错误 / 校验失败 |
| 401 | 未授权（删除接口） |
| 404 | 资源不存在 |
| 429 | 限流 |
| 500 | 服务端异常 |

### 7.2 业务错误码

| 错误码 | 描述 |
|---|---|
| `CONTENT_TOO_LONG` | 消息超过 1000 字符 |
| `VALIDATION_ERROR` | 参数校验失败 |
| `RATE_LIMIT_EXCEEDED` | 限流 |
| `DELETE_FAILED` | 删除失败 |

---

*Last updated: 2026-01-14*
