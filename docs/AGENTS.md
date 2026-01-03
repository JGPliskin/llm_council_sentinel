# AGENTS.md - 技术架构与工作流（最新版）

本文件是 LLM Council Sentinel 的权威技术说明文档，覆盖架构、关键流程、数据结构、边界条件与运行规则。
文档内容以当前代码实现为准（以 `backend/` 与 `frontend/src/` 为准），要求“给任何人看都没有歧义”。

> 相关文档
> - [Architecture.md](./Architecture.md) - 系统架构总览
> - [API_REFERENCE.md](./API_REFERENCE.md) - API 接口参考
> - [DATA_SCHEMA.md](./DATA_SCHEMA.md) - 数据模型定义
> - [配置说明.md](./配置说明.md) - 环境配置指南
> - [UI_STYLE_GUIDE.md](./UI_STYLE_GUIDE.md) - 前端视觉规范
> - [开发文档/stage2-thinking-stream.md](./开发文档/stage2-thinking-stream.md) - Stage2 Thinking 方案

---

## 1. 系统概览

LLM Council 是一个三阶段异步协作系统：

- **Stage1**：多名 Councilor 并行产出回答（Markdown）
- **Stage2**：匿名互评、评分与排序（JSON）
- **Stage3**：Chairman 综合输出最终结论（Markdown）

系统具备：

- 模型健康管理（健康 / 冷却 / 不可用）
- 对话持久化（JSON 文件）
- 流式 SSE 输出（前端实时渲染）
- Thinking 工具调用（前端按阶段展示）
- 固定模型分配（创建对话时分配并固定，schema_version=3）

---

## 2. Active Councilors（当前配置）

> 数据来源：`backend/config.py`。注意：对话创建后可能使用 `model_assignments` 进行固定分配，实际运行模型可能与默认模型不同。

| ID | Name | Role | Default Model | Judge Style (Stage2) |
| :--- | :--- | :--- | :--- | :--- |
| `immanuel_kant` | 康德 | Councilor | `xiaomi/mimo-v2-flash:free` | 冷静、结构化、强调长期稳健性 |
| `donald_trump` | 特朗普 | Councilor | `xiaomi/mimo-v2-flash:free` | 可执行性、风险隔离、资源约束 |
| `hideo_kojima` | 小岛秀夫 | Councilor | `xiaomi/mimo-v2-flash:free` | 学术审慎、可验证性、避免偏误 |
| `chairman` | 共识主席 | Chairman | `xiaomi/mimo-v2-flash:free` | 中立综合、突出共识与分歧 |

**候选模型池**：见 `GLOBAL_MODEL_POOL`，Stage1/2/3 可能从候选池中切换（仅动态模式）。

---

## 3. 架构与模块

### 3.1 后端模块（`backend/`）

| 模块 | 作用 | 关键职责 |
|---|---|---|
| `main.py` | FastAPI 入口 | API 路由、SSE、对话存储、限流、输入校验、健康刷新调度 |
| `council.py` | 三阶段编排 | Stage1/2/3 执行、并发控制、重试策略、匿名映射、thinking 注入 |
| `model_assigner.py` | 固定分配 | 创建对话时分配模型，保存到 `model_assignments` |
| `openrouter.py` | LLM 客户端 | 流式请求、解析 tool_calls、回调 thinking |
| `storage.py` | 存储层 | JSON 持久化、对话列表、删除、schema 迁移 |
| `validation.py` / `health.py` | 健康系统 | 状态缓存、冷却与失败阈值、探测逻辑 |
| `persona_loader.py` | Persona 载入 | 启动预加载 persona 文件 |
| `config.py` | 全局配置 | 模型池、超时、并发、健康参数、路径配置 |

### 3.2 前端模块（`frontend/src/`）

| 模块 | 作用 | 关键职责 |
|---|---|---|
| `App.jsx` | 应用入口 | 会话加载、流式渲染、全局状态注入 |
| `hooks/useParliamentEngine.js` | 状态机 | Stage1/2/3 SSE 事件分发与状态维护 |
| `StageContentArea.jsx` | 内容区 | Stage1/Stage3 内容渲染与 Thinking 展示 |
| `DetailPanel.jsx` | 侧边栏 | Stage2 Thinking 与评审详情；Stage3 主席思考 |
| `TacticalHUD.jsx` | HUD | 底部状态栏、Councilor 卡片与共识提示 |
| `Sidebar.jsx` | 会话列表 | 新建 / 选择 / 删除对话 |
| `api.js` | API 客户端 | REST/SSE 请求封装 |
| `config/councilors.js` | UI 配置 | Councilor 颜色映射 |

---

## 4. Thinking 工具定义

### 4.1 工具 Schema（后端定义）

```json
{
  "type": "function",
  "function": {
    "name": "emit_thinking",
    "description": "Emit a thinking step payload for UI display.",
    "parameters": {
      "type": "object",
      "properties": {
        "bullet_id": {
          "type": "string",
          "description": "Unique identifier of the thinking step."
        },
        "title": {
          "type": "string",
          "description": "Concise title of the thinking step."
        },
        "detail": {
          "type": "string",
          "description": "1-3 lines of public-facing detail."
        },
        "op": {
          "type": "string",
          "enum": ["append", "update"],
          "description": "append to add, update to modify a prior step."
        },
        "target_anon_id": {
          "type": "string",
          "description": "(Stage2 only) Indicates which anonymous candidate this thinking step is evaluating (e.g. anon_1, anon_2)."
        }
      },
      "required": ["title"]
    }
  }
}
```

### 4.2 Stage2 思考要求（行为约束）

Stage2 评审提示词要求：

- **必须多次调用** `emit_thinking`
- **必须中文**输出 `title` 与 `detail`
- **必须提供** `target_anon_id`

示例：

```json
{
  "title": "评估 anon_1 的逻辑一致性",
  "detail": "检查关键假设是否可验证",
  "target_anon_id": "anon_1",
  "op": "append"
}
```

---

## 5. SSE 事件协议（关键摘要）

### 5.1 事件序列（流式）

```
meta → stage1_start → [thinking]* → [stage1_item]* → stage1_complete
     → stage2_start → [thinking]* → [stage2_item]* → stage2_complete
     → stage3_start → [thinking]* → stage3_complete
     → [title_complete] → complete
```

### 5.2 Thinking 事件（Stage2 支持 target_anon_id）

```json
{
  "type": "thinking",
  "stage": "stage2",
  "councilor_id": "donald_trump",
  "model": "xiaomi/mimo-v2-flash:free",
  "bullet_id": "donald_trump-stage2-1",
  "title": "评估 anon_2 的可行性",
  "detail": "关注成本与时间的权衡",
  "op": "append",
  "target_anon_id": "anon_2",
  "t": 2.31
}
```

**说明**：
- `councilor_id` 表示评审者（judge）
- `target_anon_id` 表示被评审对象（匿名 ID）
- 前端通过 `stage2_start.anon_map` 映射为真实 `councilor_id`

---

## 6. 关键数据结构

### 6.1 Stage1Result

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

### 6.2 Stage2 Review

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

### 6.3 Stage3 Result

```json
{
  "status": "ok",
  "model": "xiaomi/mimo-v2-flash:free",
  "response": "...",
  "attempted_models": ["xiaomi/mimo-v2-flash:free"],
  "fallback_used": false
}
```

### 6.4 Metadata.thinking（流式持久化）

```json
"thinking": {
  "stage1": {
    "immanuel_kant": {
      "model": "xiaomi/mimo-v2-flash:free",
      "status": "done",
      "steps": [
        {"bullet_id": "immanuel_kant-stage1-1", "title": "...", "detail": null, "t": 0.5}
      ]
    }
  },
  "stage2": {
    "donald_trump": {
      "model": "xiaomi/mimo-v2-flash:free",
      "status": "thinking",
      "steps": [
        {"bullet_id": "donald_trump-stage2-1", "title": "...", "detail": "...", "target_anon_id": "anon_2", "t": 2.3}
      ]
    }
  },
  "stage3": {}
}
```

**持久化限制**：每阶段每人最多 50 条，总计最多 200 条。

---

## 7. 模型分配与回退规则

- **动态模式（无固定分配）**：从候选池中选择健康/未知模型，失败后回退到下一个候选。
- **固定模式（schema_version=3）**：使用 `model_assignments` 中的固定模型，失败不回退。
- `councilor_ids` 在 fixed 模式下会被忽略。

---

## 8. 前端状态与 UI 行为

关键状态（`useParliamentEngine`）：

- `stage`: idle / stage1 / stage2 / stage3
- `thinkingByCouncilor`: Stage1 thinking
- `stage2ThinkingByJudge`: Stage2 thinking（按 judge + target 分组）
- `stage3AnswerStream`: Stage3 文本增量
- `evaluationComments`: Stage2 评审 comments（按 target 分组）

Stage2 DetailPanel 行为：

- 只要任意 judge 仍为 `thinking`，DetailPanel 保持 Thinking 模式（无混合 Review）
- 全部 judge 变为 `done` 后，整体切换为 Review 模式（动画衔接）

---

## 9. 运行要点与边界条件

- `MAX_MESSAGE_LENGTH = 1000`
- `/message` 与 `/message/stream` 限流：`5/min`
- Stage2 跳过条件：有效候选 < 2
- Stage2 自评 **允许**（评审者可以对自己匿名答案评分）
- 非流式请求不会记录 thinking 到 metadata

---

*Last updated: 2026-01-03*
