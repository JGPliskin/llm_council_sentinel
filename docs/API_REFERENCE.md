# API_REFERENCE.md - LLM Council Sentinel API 参考

本文档定义后端 API 与 SSE 协议，基于当前实现（`backend/main.py`）。

---

## 1. 基本信息

### 1.1 Base URL

| 场景 | Base URL | 说明 |
| --- | --- | --- |
| 本地开发 | `http://localhost:8010` | `uv run python -m backend.main` |
| Docker + Nginx | `http://localhost/api` | Nginx 反向代理 `/api/*` -> `backend:8008` |

### 1.2 请求协议
- REST：`Content-Type: application/json`
- SSE：`Content-Type: text/event-stream`

### 1.3 认证
- 管理接口需要 `X-Admin-Token`。
- 当前后端为调试模式：`verify_admin` 直接放行（见 `backend/main.py`）。

### 1.4 速率限制

| 接口 | 限流 | 说明 |
| --- | --- | --- |
| `/api/conversations/{id}/message` | 5/min | 按 IP |
| `/api/conversations/{id}/message/stream` | 5/min | 按 IP |

---

## 2. 通用错误返回格式

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求过于频繁，请稍后再试",
    "message_en": "Too many requests, please try again later",
    "details": {"retry_after": 60}
  }
}
```

常见 `code`：
- `CONTENT_TOO_LONG`
- `VALIDATION_ERROR`
- `RATE_LIMIT_EXCEEDED`
- `DELETE_FAILED`

---

## 3. 接口概览

| 方法 | 路径 | 描述 | 认证 |
| --- | --- | --- | --- |
| `GET` | `/` | 服务状态 | 否 |
| `GET` | `/health` | Docker 健康检查 | 否 |
| `GET` | `/api/councilors` | 获取议员与主席配置 | 否 |
| `GET` | `/api/models` | `/api/councilors` 别名 | 否 |
| `GET` | `/api/conversations` | 会话列表 | 否 |
| `POST` | `/api/conversations` | 创建会话 | 否 |
| `GET` | `/api/conversations/{id}` | 获取会话详情 | 否 |
| `DELETE` | `/api/conversations/{id}` | 删除会话 | 是 |
| `POST` | `/api/conversations/bulk-delete` | 批量删除 | 是 |
| `POST` | `/api/conversations/{id}/message` | 同步问答 | 否 |
| `POST` | `/api/conversations/{id}/message/stream` | 流式 SSE | 否 |

---

## 4. Councilor 接口

### 4.1 GET `/api/councilors`

**查询参数**

| 参数 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `refresh` | boolean | `false` | 是否强制刷新健康状态 |

**响应示例**

```json
{
  "version": "2.1-health-v3",
  "councilors": [
    {
      "id": "immanuel_kant",
      "name": "康德",
      "model": "openrouter:xiaomi/mimo-v2-flash:free",
      "avatar": "/avatars/immanuel_kant.png",
      "active": true,
      "healthy": true,
      "health_error": null,
      "health_checked_at": "2026-01-03T03:00:00Z"
    }
  ],
  "chairman": {
    "id": "chairman",
    "name": "共识主席",
    "model": "openrouter:xiaomi/mimo-v2-flash:free",
    "avatar": "/avatars/chairman.png",
    "active": true,
    "healthy": true
  },
  "meta": {
    "refresh_skipped": false,
    "server_time": "2026-01-03T03:00:01Z"
  }
}
```

**字段说明**

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `councilors[].id` | string | 议员 ID |
| `councilors[].model` | string | 当前默认模型（不一定是固定分配） |
| `healthy` | boolean | 健康状态 |
| `health_error` | string | 最近一次健康异常说明 |

---

## 5. 会话接口

### 5.1 POST `/api/conversations`
创建新会话并执行模型固定分配（schema_version=3）。

**请求体**
```json
{ "councilor_ids": ["immanuel_kant", "donald_trump"] }
```

**行为规则**
- `councilor_ids` 可为空；为空时使用当前健康的默认议员。
- 若包含模型 ID，会通过 `normalize_councilor_ids` 映射为议员 ID。
- 不合法 ID 会被忽略，若全部无效则回退为默认议员。

**响应示例**
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
    "immanuel_kant": "openrouter:nvidia/nemotron-3-nano-30b-a3b:free",
    "donald_trump": "openrouter:xiaomi/mimo-v2-flash:free",
    "chairman": "openrouter:xiaomi/mimo-v2-flash:free"
  },
  "assignment_seed": "2026-01-03T03:01:00Z-xxxx",
  "assignment_strategy": "healthy_first"
}
```

### 5.2 GET `/api/conversations/{id}`
返回会话完整 JSON（见 `docs/DATA_SCHEMA.md`）。

### 5.3 GET `/api/conversations`
返回会话列表（仅元数据）。

### 5.4 DELETE `/api/conversations/{id}`
删除单个会话，返回 `204`。

### 5.5 POST `/api/conversations/bulk-delete`
**请求体**
```json
{ "ids": ["uuid1", "uuid2"] }
```

**响应体**
```json
{ "deletedIds": ["uuid1"], "failed": [{"id": "uuid2", "reason": "not_found"}] }
```

---

## 6. 消息接口

### 6.1 POST `/api/conversations/{id}/message`
同步执行三阶段，并一次性返回结果。

**请求体**
```json
{
  "content": "...",
  "councilor_ids": ["immanuel_kant", "donald_trump"],
  "enable_thinking": true
}
```

**注意**
- 当 `schema_version >= 3` 且已有 `model_assignments` 时，`councilor_ids` 会被忽略。
- 同步接口不会写入 `metadata.thinking`。

**响应体**
```json
{
  "stage1": [...],
  "stage2": {...},
  "stage3": {...},
  "metadata": {
    "anon_to_councilor": {...},
    "aggregate_rankings": [...]
  }
}
```

### 6.2 POST `/api/conversations/{id}/message/stream`
流式 SSE，逐步返回阶段事件。

---

## 7. SSE 事件协议

### 7.1 事件顺序（典型）
```
meta
 -> stage1_start
 -> eta_update / thinking / stage1_answer_delta / stage1_item / stage1_complete
 -> stage2_start
 -> eta_update / thinking / stage2_item / stage2_complete
 -> stage3_start
 -> thinking / stage3_answer_delta / stage3_complete
 -> title_complete
 -> complete
```

### 7.2 事件定义

#### 7.2.1 `meta`
```json
{
  "type": "meta",
  "resolved_councilor_ids": ["immanuel_kant", "donald_trump"],
  "resolved_councilors": [
    {"id": "immanuel_kant", "name": "康德", "avatar": "/avatars/immanuel_kant.png", "model": "openrouter:..."}
  ],
  "chairman": {"id": "chairman", "name": "共识主席", "avatar": "/avatars/chairman.png", "model": "openrouter:..."},
  "ignored_ids": [],
  "spec_version": "stage2_v1.2",
  "model_assignments": {"immanuel_kant": "...", "chairman": "..."}
}
```

#### 7.2.2 `eta_update`
```json
{
  "type": "eta_update",
  "stage": "stage1",
  "councilor_id": "immanuel_kant",
  "eta_ms_remaining": 5200,
  "model": "openrouter:...",
  "reason": "queue_start"
}
```
- `reason`: `queue_start` | `done`

#### 7.2.3 `thinking`
```json
{
  "type": "thinking",
  "stage": "stage2",
  "councilor_id": "donald_trump",
  "model": "openrouter:...",
  "bullet_id": "donald_trump-stage2-1",
  "title": "评估 anon_2 的可行性",
  "detail": "关注成本与时间权衡",
  "op": "append",
  "target_anon_id": "anon_2",
  "t": 2.31
}
```
- Stage2 必须包含 `target_anon_id`。

#### 7.2.4 `stage1_answer_delta`
```json
{ "type": "stage1_answer_delta", "councilor_id": "immanuel_kant", "delta": "..." }
```

#### 7.2.5 `stage1_answer_done`
```json
{ "type": "stage1_answer_done", "councilor_id": "immanuel_kant" }
```

#### 7.2.6 `stage1_item`
```json
{ "type": "stage1_item", "data": { ...Stage1Result... } }
```

#### 7.2.7 `stage1_complete`
```json
{ "type": "stage1_complete", "data": [ ...Stage1Result... ] }
```

#### 7.2.8 `stage2_start`
```json
{ "type": "stage2_start", "anon_map": {"anon_1": "immanuel_kant"} }
```
若跳过：
```json
{ "type": "stage2_start", "skipped": true, "skipped_reason": "insufficient_candidates" }
```

#### 7.2.9 `stage2_item`
```json
{ "type": "stage2_item", "data": { ...Review... } }
```

#### 7.2.10 `stage2_complete`
```json
{
  "type": "stage2_complete",
  "data": { ...Stage2Result... },
  "metadata": {
    "anon_to_councilor": {"anon_1": "immanuel_kant"},
    "aggregate_rankings": [{"councilor_id": "immanuel_kant", "average_rank": 1.0, "rankings_count": 1}]
  }
}
```

#### 7.2.11 `stage3_start`
```json
{ "type": "stage3_start" }
```

#### 7.2.12 `stage3_answer_delta`
```json
{ "type": "stage3_answer_delta", "councilor_id": "chairman", "delta": "..." }
```

#### 7.2.13 `stage3_complete`
```json
{ "type": "stage3_complete", "data": { ...Stage3Result... } }
```

#### 7.2.14 `title_complete`
```json
{ "type": "title_complete", "data": {"title": "..."} }
```
仅首条消息时触发。

#### 7.2.15 `complete`
```json
{ "type": "complete" }
```

---

## 8. HTTP 状态码

| 状态码 | 含义 |
| --- | --- |
| 200 | 成功 |
| 204 | 删除成功（无内容） |
| 400 | 参数错误/校验失败 |
| 401 | 未授权（管理接口） |
| 404 | 资源不存在 |
| 429 | 触发限流 |
| 500 | 服务器内部错误 |

---

Last updated: 2026-01-23

