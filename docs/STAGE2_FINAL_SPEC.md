# SPEC v1.2 Final：Stage2 人格化 + 严格 JSON + 增量展示 + 进度条 + 头像

本文档为最终落地规格（Final）。如与其他草案冲突，以本文件为准。

---

## 目录

- [1. 用户场景与需求（无歧义）](#1-用户场景与需求无歧义)
- [2. 不在范围（明确非目标）](#2-不在范围明确非目标)
- [3. 核心约束与验收口径](#3-核心约束与验收口径)
- [4. 数据结构（Schema）](#4-数据结构schema)
- [5. Prompt 结构（叠加与 JSON Guard）](#5-prompt-结构叠加与-json-guard)
- [6. 技术方案（端到端）](#6-技术方案端到端)
- [7. 技术架构图与流程图](#7-技术架构图与流程图)
- [8. SSE 事件协议（增量展示）](#8-sse-事件协议增量展示)
- [9. 前端 UI 规格（头像 + 进度条）](#9-前端-ui-规格头像--进度条)
- [10. 兼容性与迁移策略](#10-兼容性与迁移策略)
- [11. 需要改动的代码文件与关键修改点](#11-需要改动的代码文件与关键修改点)
- [12. 验收清单](#12-验收清单)

**已确定的方案选择**

| 冲突点 | 选择 | 含义 |
|---|---|---|
| 冲突1：SSE 由谁消费 | B | SSE 事件由前端 `ChatInterface` 消费并维护增量 UI 状态 |
| 冲突2：头像字段放哪 | A | `avatar` 字段由后端配置并通过 `/api/councilors` 下发 |
| 冲突3：匿名映射在哪提供 | A | `anon_map` 在 `stage2_start` 一次性下发 |

---

## 1. 用户场景与需求（无歧义）

### 1.1 用户场景（User Stories）

| 场景ID | 用户看到的体验 | 必须满足 |
|---|---|---|
| US-1 | 用户发送问题后，Stage1 的议员回答会**陆续出现**（谁先算完先出现），未完成的保持“Thinking” | Stage1 必须支持 item 级增量事件；前端可对单人显示 completed/thinking |
| US-2 | Stage2 的评审同样**陆续出现**，用户能看到每个 judge 的评审 tab/内容逐步变为可用 | Stage2 必须支持 item 级增量事件（每 judge 一次请求） |
| US-3 | Stage2 排名列表里显示的是“康德/特朗普/小岛秀夫”等真实角色名（可带头像），而不是 `anon_1` | 必须能去匿名化显示（使用 `anon_map` + councilor metadata） |
| US-4 | Council Members 区域在回答阶段显示的是角色名与头像，不是模型名 | 修复前端数据源/props，确保渲染使用 `{id,name,avatar}` |
| US-5 | Stage2 的评审风格明显不同（同模型也要不同风格） | Stage2 prompt 必须叠加 `judge_persona` |
| US-6 | Stage2 输出始终是严格 JSON（人格不会带跑格式） | Stage2 JSON Guard + 解析器严格 schema（拒绝额外字段） |
| US-7 | 显示 Stage1/Stage2 的进度条与每个成员状态（✓/…/✕） | 必须在 UI 中展示并跟随 SSE item 事件更新 |

### 1.2 需求描述（Requirements）

| 编号 | 需求 | 细则 |
|---|---|---|
| R-1 | Stage2 人格化 | 每个 judge 使用 `judge_persona_path`（无则 fallback `persona_path`） |
| R-2 | Stage2 严格 JSON | Stage2 顶层只允许 `ranking/scores/rationale`，出现其他字段 => 判 invalid 重试 |
| R-3 | Stage2 one-shot | 每个 judge 仅 1 次请求，对所有候选一次性 ranking |
| R-4 | Stage2 输入看摘要 | Stage1 必须输出 `answer_summary`（≤500），Stage2 输入包含 `answer_summary + judge_card` |
| R-5 | 实名展示 | 排名展示使用实名（+头像），默认不展示 `anon_*` |
| R-6 | 增量展示 | Stage1/Stage2 必须提供 `stage*_item` 事件，前端逐条渲染 |
| R-7 | 进度条 | Stage1/Stage2 都有进度条与成员状态列表，成功/失败都计为“完成一个” |
| R-8 | 头像字段 | `avatar` 从后端下发；UI 显示 `avatar + name` 为主标签 |
| R-9 | 不落盘中间态 | 不把 item 级结果写入 conversation storage；最终仍在 complete 后一次性写入 |
| R-10 | 历史兼容 | 老会话缺 `answer_summary`：前端用截断 `answer_markdown`（≤500）作为 fallback |

---

## 2. 不在范围（明确非目标）

| 编号 | 非目标 | 说明 |
|---|---|---|
| NG-1 | 中途落盘/断线恢复中间态 | 本版明确不做，避免写入多次与部分状态一致性问题 |
| NG-2 | Stage2 改为逐候选多次 review | 保持 one-shot 机制不变 |
| NG-3 | 随机化/洗牌 anon_id | 本版不要求，anon_id 可稳定生成 |
| NG-4 | 重新设计全套 UI 交互 | 仅在现有组件上补齐增量、进度条、头像展示与 bug 修复 |

---

## 3. 核心约束与验收口径

### 3.1 约束（不可违反）

| 约束 | 描述 |
|---|---|
| C-1 | Stage2 输出必须是单个 JSON object，且顶层字段集合严格等于允许集合（`ranking/scores/rationale`） |
| C-2 | `ranking` 必须覆盖全部 `anon_id` 且恰好一次 |
| C-3 | Stage2 one-shot：每个 judge 一次请求完成对全部候选 ranking |
| C-4 | 增量展示必须真实：不等待“全员完成”再一次性显示 |
| C-5 | Council Members 主标签必须是 `avatar+name`（模型名只能放 tooltip/次要信息） |

### 3.2 质量目标（推荐但可调）

| 目标 | 推荐值 | 说明 |
|---|---|---|
| `rationale` 长度上限 | ≤ 600 chars | 降低模型跑长文导致的不稳定风险 |

---

## 4. 数据结构（Schema）

| 维度 | 要求 |
|---|---|
| Stage2 人格化 | 每个 judge 的评审风格必须不同：使用 `judge_persona` + rubric |
| 严格 JSON | Stage2 必须输出严格 JSON：**拒绝任何额外字段**，不得 markdown/解释/代码块 |
| Stage2 机制不改 | 每个 judge **一次请求**，一次性 rank 全部候选（不做逐个 review） |
| 看回答摘要 | Stage2 输入看 **`answer_summary`（≤500） + `judge_card`** |
| 实名展示 | 前端展示排名时必须显示真实角色名（可带头像/emoji），不显示 `anon_*` |
| 增量展示 | Stage1/Stage2 **谁先完成先展示**，未完成保持 loading/思考 |
| 不落盘中间态 | item 级 SSE 只影响 UI；最终仍在 `complete` 后一次性存储 |
| 旧会话兼容 | 缺 `answer_summary`：前端用截断的 `answer_markdown` fallback（≤500） |
| 本版必须包含 | **进度条** + **Emoji/头像字段与 UI 展示增强** |

---

## 1. 后端配置与公开字段（新增 avatar）

### 1.1 后端配置字段

后端 `COUNCILORS/CHAIRMAN` 必须配置：

| 字段 | 类型 | 说明 |
|---|---|---|
| `avatar` | string | Emoji（推荐）或图片 URL；为空则前端 fallback |

### 1.2 `/api/councilors` 下发字段（必须包含 avatar）

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 稳定 councilor id |
| `name` | string | 角色名（如“康德”） |
| `model` | string | 模型 id |
| `avatar` | string | Emoji 或图片 URL |
| `active/healthy/...` | - | 现有健康字段保留 |

---

## 2. Schema（输出/输入）

### 2.1 Stage1 输出（每位议员一次，严格 JSON）

Stage1 只允许输出 **一个 JSON object**（不得有额外文本），包含：

```json
{
  "councilor_id": "string",
  "answer_markdown": "string",
  "answer_summary": "string (<=500 chars)",
  "judge_card": {
    "stance": "string",
    "core_reasons": ["string", "string"],
    "assumptions": ["string"],
    "risks": ["string"],
    "actionables": ["string"]
  }
}
```

硬约束：
- `answer_summary` 必填，≤500 字符（按字符计）。
- `judge_card` 规则沿用现有约束（如 `core_reasons` 至少 2 条、压缩规则等）。

### 2.2 Stage2 输入（匿名候选，摘要 + judge_card）

每个候选项（匿名）：

| 字段 | 必填 | 说明 |
|---|---:|---|
| `anon_id` | 是 | `anon_1/anon_2/...` |
| `answer_summary` | 是 | Stage1 提供的摘要（≤500） |
| `judge_card` | 是 | Stage1 提供的 `judge_card` |

匿名映射（后端维护）：
- `anon_map: { "anon_1": "immanuel_kant", ... }`

### 2.3 Stage2 输出（每位 judge 一次，严格 JSON，拒绝额外字段）

允许字段集合：`{"ranking","scores","rationale"}`（除此之外出现任何 key => invalid 重试）

```json
{
  "ranking": ["anon_1", "anon_2", "anon_3"],
  "scores": { "anon_1": 8, "anon_2": 6 },
  "rationale": "string"
}
```

约束：

| 字段 | 必填 | 规则 |
|---|---:|---|
| `ranking` | 是 | 必须包含全部 anon_id 且恰好一次 |
| `scores` | 否 | key 只能是 anon_id；value 必须 1–10 整数 |
| `rationale` | 否 | 建议 ≤600 字符（提升稳定性） |

---

## 3. Prompt 结构（persona 叠加 + JSON guard 最强）

### 3.1 Stage2 System Prompt 三层叠加（顺序固定）

| 顺序 | role | 内容 |
|---:|---|---|
| 1 | system | `judge_persona`（来自 `judge_persona_path`） |
| 2 | system | `judge_rubric`（来自 `judge_system_prompt` + 通用评审维度） |
| 3 | system | `json_guard`（最强、最后：只输出 JSON + schema + 禁止额外字段 + ranking 完整性） |
| 4 | user | payload JSON：`question` + `candidates[]` |

JSON Guard（示例）：

```text
HARD CONSTRAINTS (MUST FOLLOW):
1) Output EXACTLY ONE JSON object and nothing else.
2) NO markdown fences, NO commentary.
3) Allowed top-level fields ONLY: ranking, scores, rationale. No extra keys.
4) ranking must include ALL anon_ids exactly once.
5) scores (optional) must be integers 1-10 keyed by anon_id only.
```

Persona 边界控制：
- persona 只能影响 `rationale` 的用词/视角；
- 不得影响字段名/字段类型/anon_id 完整性/输出是否夹杂额外文本。

---

## 4. SSE 事件流（增量展示 + 进度条必要数据）

### 4.1 事件类型（必须支持）

```
meta
stage1_start
stage1_item
stage1_complete
stage2_start
stage2_item
stage2_complete
stage3_start
stage3_complete
title_complete
complete
error
```

### 4.2 事件载荷规范（关键点：anon_map 在 stage2_start 一次性下发）

建议 payload（结构化，便于前端实现）：

| 事件 | payload（建议字段） |
|---|---|
| `meta` | `{ resolved_councilor_ids: string[], ignored_ids: string[], councilors: [{id,name,avatar,model,active,healthy,...}], chairman: {id,name,avatar,model,...} }` |
| `stage1_item` | `{ item: Stage1ResultWithStatus }` |
| `stage2_start` | `{ anon_map: { [anon_id]: councilor_id } }` |
| `stage2_item` | `{ item: Stage2ReviewWithStatus }` |
| `stage*_complete` | 保留全量快照字段以兼容旧逻辑（全量 + metadata） |

`Stage1ResultWithStatus` / `Stage2ReviewWithStatus` 最少字段要求：
- Stage1：`councilor_id`, `councilor_name`, `model`, `status(ok/failed)`, `error?`, `answer_markdown?`, `answer_summary?`, `judge_card?`
- Stage2：`judge_councilor_id`, `judge_councilor_name`, `model`, `status(ok/failed)`, `error?`, `ranking?`, `scores?`, `rationale?`

---

## 5. 前端架构（SSE 由 ChatInterface 消费）

### 5.1 职责划分（强制）

| 层级 | 职责 |
|---|---|
| `App.jsx` | 路由/会话列表/加载会话；将 `conversation` 传给 `ChatInterface`；接收完成回调更新列表 |
| `ChatInterface.jsx` | **唯一 SSE 消费者**：调用 `api.sendMessageStream`，维护本轮 assistant message 的增量 state（stage1/stage2/stage3/loading/progress）并渲染 |

---

## 6. UI/交互规范（必须包含头像 + 进度条）

### 6.1 Council Members 区（修复 bug + 头像）

- 必须显示：`avatar + name`
- 不显示模型名作为主标签（模型名仅允许在 tooltip/次要信息里出现）
- thinking/completed/error 状态按“人”显示

ASCII 原型：

```
COUNCIL MEMBERS
[🧠 康德]  [🧱 特朗普]  [🎮 小岛秀夫]
   ✓         …thinking…      ✕
```

### 6.2 Stage1/Stage2 Card Header 进度条（必须）

进度定义：
- Stage1 total = `meta.resolved_councilor_ids.length`
- Stage1 done = 已收到的 `stage1_item` 数量（ok/failed 都计入 done）
- Stage2 total = 默认与 Stage1 相同（本轮参与者均为 judge）
- Stage2 done = 已收到的 `stage2_item` 数量（ok/failed 都计入 done）

ASCII 原型（Stage2）：

```
┌──────────────────────────────────────────────┐
│ Stage 2 评审阶段   进度 2/3  [███████░░░] 66% │
│ 🧠康德 ✓   🧱特朗普 …   🎮小岛 ✓              │
└──────────────────────────────────────────────┘
```

### 6.3 Stage2 排名展示实名 + 头像（必须）

渲染规则（不得直接展示 anon_id）：
1) 从 `stage2_start.anon_map` 得到 `anon_id -> councilor_id`
2) 从 `meta.councilors`（或 `/api/councilors` 缓存）得到 `councilor_id -> {name,avatar}`
3) 展示为：`avatar + name`
4) 仅在映射缺失的异常路径，fallback 显示 `anon_id`（并记录/提示异常）

---

## 7. avatar 值格式约定

| avatar 值 | 含义 | UI 处理 |
|---|---|---|
| 单个 Emoji（推荐） | 例如 `🧠` | 直接渲染为文本头像 |
| 图片 URL | 例如 `https://.../kant.png` | 用图片渲染；失败 fallback |
| 空/缺失 | - | fallback 到 name 首字/默认占位 |

---

## 8. 旧会话兼容（必需）

当 `answer_summary` 缺失：
- 前端生成：`summary = truncate(answer_markdown, 500)`（只用于显示/历史查看，不反写）

---

---

## 6. 技术方案（端到端）

### 6.1 Stage1（生成回答 + 摘要 + judge_card）

| 步骤 | 后端行为 | 输出/事件 |
|---:|---|---|
| 1 | 为每个 councilor 构建 Stage1 prompt（persona + JSON 要求）并并发请求 | `stage1_start` |
| 2 | 每个 councilor 完成后立即产出结构化结果（含 `answer_summary` ≤ 500） | `stage1_item`（单人） |
| 3 | 全部完成后（或超时策略结束）发送全量（可选保留兼容） | `stage1_complete` |

### 6.2 Stage2（匿名评审：摘要+judge_card + persona 叠加 + 严格 JSON）

| 步骤 | 后端行为 | 输出/事件 |
|---:|---|---|
| 1 | 根据 Stage1 成功的候选生成 `anon_id` 与 `anon_map` | `stage2_start`（携带 `anon_map`） |
| 2 | 对每个 judge 构建三层叠加 prompt（persona→rubric→json_guard）并并发请求（one-shot） | - |
| 3 | 每个 judge 完成后立刻解析并校验 schema（拒绝额外字段）；成功则发 item，失败按策略重试/标记失败 | `stage2_item`（单人） |
| 4 | 全部完成后发送全量（可选保留兼容） | `stage2_complete` |

### 6.3 前端（增量渲染 + 进度条 + 头像）

| 步骤 | 前端行为 | UI 结果 |
|---:|---|---|
| 1 | `ChatInterface` 发送请求并进入“本轮消息”状态机 | 立即出现 Council Members 占位 + 进度条 0% |
| 2 | 收到 `meta` 初始化参与者列表（含 avatar/name），渲染每人占位卡与状态 | Council Members 立即显示头像/姓名 |
| 3 | 收到 `stage1_item` 逐个渲染 Stage1 内容，并推进 Stage1 进度条 | 已完成者 ✓，未完成者 … |
| 4 | 收到 `stage2_start` 保存 `anon_map` | 之后 Stage2 ranking 可即时实名化 |
| 5 | 收到 `stage2_item` 逐个渲染 Stage2 tab/内容并推进 Stage2 进度条 | 排名显示实名 + 头像 |

---

## 7. 技术架构图与流程图

### 7.1 组件/数据流架构图（简化）

```
┌───────────────┐     SSE events      ┌───────────────────────┐
│   Backend API │ ────────────────▶   │ Frontend ChatInterface │
│  (FastAPI)    │                    │  (SSE consumer)         │
└───────┬───────┘                    └───────┬───────────────┘
        │                                    │
        │ OpenRouter calls                   │ UI renders
        ▼                                    ▼
┌───────────────────┐                ┌────────────────────────┐
│ stage1_collect... │                │ CouncilAvatars / Stage1 │
│ stage2_collect... │                │ Stage2 / Stage3         │
└───────────────────┘                └────────────────────────┘
```

### 7.2 时序流程图（增量事件）

```
Client(ChatInterface)         Backend(main.py)             Models(OpenRouter)
        │                           │                           │
        │ POST /message/stream      │                           │
        │──────────────────────────▶│                           │
        │◀──────── meta ─────────── │                           │
        │◀──── stage1_start ─────── │                           │
        │                           │── stage1 req (A,B,C) ───▶│
        │◀──── stage1_item(A) ───── │◀──── response(A) ─────── │
        │◀──── stage1_item(B) ───── │◀──── response(B) ─────── │
        │◀──── stage1_item(C) ───── │◀──── response(C) ─────── │
        │◀──── stage1_complete ──── │                           │
        │◀──── stage2_start(+map) ─ │                           │
        │                           │── stage2 req (judge A) ─▶│
        │                           │── stage2 req (judge B) ─▶│
        │                           │── stage2 req (judge C) ─▶│
        │◀──── stage2_item(A) ───── │◀──── response(A) ─────── │
        │◀──── stage2_item(B) ───── │◀──── response(B) ─────── │
        │◀──── stage2_item(C) ───── │◀──── response(C) ─────── │
        │◀──── stage2_complete ──── │                           │
        │◀──── stage3_start ─────── │                           │
        │◀──── stage3_complete ──── │                           │
        │◀──── complete ─────────── │                           │
```

---

## 8. SSE 事件协议（增量展示）

### 8.1 事件类型（必须支持）

```
meta
stage1_start
stage1_item
stage1_complete
stage2_start
stage2_item
stage2_complete
stage3_start
stage3_complete
title_complete
complete
error
```

### 8.2 事件载荷（推荐结构）

| 事件 | 字段 | 说明 |
|---|---|---|
| `meta` | `resolved_councilor_ids` | 本轮参与者稳定 id 列表 |
|  | `ignored_ids` | 被过滤的 id 列表 |
|  | `councilors[]` | `{id,name,avatar,model,active,healthy,...}`（用于占位、头像、进度总数） |
|  | `chairman` | `{id,name,avatar,model,...}` |
| `stage1_item` | `item` | 单个议员结果（含 status/error） |
| `stage2_start` | `anon_map` | `{ anon_id: councilor_id }`（一次性下发） |
| `stage2_item` | `item` | 单个 judge 评审结果（含 status/error） |

---

## 9. 前端 UI 规格（头像 + 进度条）

### 9.1 Council Members（必须：头像+姓名为主标签）

- 主标签：`avatar + name`
- 模型名：仅 tooltip/次要信息展示
- 单人状态：thinking/completed/error

ASCII 原型：

```
COUNCIL MEMBERS
[🧠 康德]  [🧱 特朗普]  [🎮 小岛秀夫]
   ✓         …thinking…      ✕
```

### 9.2 Stage1/Stage2 Header 进度条（必须）

进度定义：
- Stage1 total = `meta.resolved_councilor_ids.length`
- Stage1 done = 已收到的 `stage1_item` 数量（ok/failed 都算 done）
- Stage2 total = 默认与 Stage1 相同（本轮参与者均为 judge）
- Stage2 done = 已收到的 `stage2_item` 数量（ok/failed 都算 done）

ASCII 原型（Stage2）：

```
┌──────────────────────────────────────────────┐
│ Stage 2 评审阶段   进度 2/3  [███████░░░] 66% │
│ 🧠康德 ✓   🧱特朗普 …   🎮小岛 ✓              │
└──────────────────────────────────────────────┘
```

### 9.3 Stage2 排名（必须：实名 + 头像）

渲染规则（不得直接展示 `anon_id`）：
1) 从 `stage2_start.anon_map` 得到 `anon_id -> councilor_id`
2) 从 `meta.councilors`（或 `/api/councilors` 缓存）得到 `councilor_id -> {name,avatar}`
3) 展示为：`avatar + name`
4) 仅在映射缺失的异常路径，fallback 显示 `anon_id`（并记录/提示异常）

---

## 10. 兼容性与迁移策略

### 10.1 旧会话缺 `answer_summary`

前端 fallback：
- `summary = truncate(answer_markdown, 500)`（只用于显示/历史查看，不反写）

### 10.2 旧前端兼容

后端保留（可选但建议）：
- `stage1_complete` / `stage2_complete` 仍提供全量快照字段，避免老逻辑完全失效

---

## 11. 需要改动的代码文件与关键修改点

> 本节为“实现清单”，用于开发时对照修改范围；不要求逐行展开，但必须覆盖关键点。

### 11.1 后端

| 文件 | 必改点 | 关键修改 |
|---|---|---|
| `backend/config.py` | 新增 `avatar` | 为每个 councilor/chairman 增加 `avatar` 字段 |
| `backend/main.py` | SSE 增量事件 | 在 `/message/stream` 中新增 `stage1_item/stage2_item`；`stage2_start` 下发 `anon_map`；`meta` 下发 `councilors/chairman` 公共信息 |
| `backend/council.py` | Stage1 新字段、Stage2 人格化与严格 schema | Stage1 输出增加 `answer_summary`；Stage2 构建三层叠加 prompt；Stage2 解析严格拒绝额外字段；Stage2 应用 `max_output_tokens` |
| `backend/persona_loader.py` | 读取 judge persona | 确保 `judge_persona_path` 已缓存并可 fetch（当前已有，但需确保配置一致） |
| `backend/openrouter.py` | 输出上限 | Stage2 请求传入 `max_output_tokens`（如当前调用路径缺失） |

### 11.2 前端

| 文件 | 必改点 | 关键修改 |
|---|---|---|
| `frontend/src/components/ChatInterface.jsx` | SSE 消费者迁移 + 进度/头像 | 将 SSE 处理从 `App.jsx` 移入；维护 stage1/stage2 item 状态；渲染进度条与每人状态；使用 meta 初始化头像/姓名 |
| `frontend/src/App.jsx` | 精简职责 | 移除/下放 SSE 处理逻辑，保留会话列表与路由；接收 `ChatInterface` 的完成回调刷新列表 |
| `frontend/src/components/CouncilAvatars.jsx` | 头像字段展示 | 使用后端下发的 `avatar`（emoji/url）；主标签显示 `avatar+name`；模型名仅 tooltip |
| `frontend/src/components/Stage1.jsx` | Tab 显示头像+姓名 | tabs/标题支持 `avatar+name`；兼容旧数据缺 avatar |
| `frontend/src/components/Stage2.jsx` | 排名实名化 + 头像 | 使用 `anon_map` + `councilorLookup` 显示真实姓名/头像；支持增量追加 judge tabs |
| `frontend/src/api.js` | 无强制改动（视实现方式） | 若仍复用 `sendMessageStream`，可保持；否则为 ChatInterface 提供统一回调接口 |

---

## 12. 验收清单

| 项 | 通过标准 |
|---|---|
| Stage2 人格化 | 不同 judge 的 `rationale` 风格明显不同 |
| Stage2 严格 JSON | 无额外字段；无 fence；ranking 完整且无重复 |
| 增量展示 | Stage1/Stage2 先完成者先展示；其他保持 loading |
| 实名+头像 | 排名与成员区都显示 `avatar+name`，不出现 `anon_*`（除非映射异常） |
| Council Members bug | 回答阶段不再显示模型名作为主标签 |
| 进度条 | Stage1/Stage2 进度随 item 事件实时变化，成功/失败都推进进度 |
| 历史兼容 | 旧会话不报错；summary fallback 正常 |

| 项 | 通过标准 |
|---|---|
| Stage2 人格化 | 不同 judge 的 `rationale` 风格明显不同 |
| Stage2 严格 JSON | 无额外字段；无 fence；ranking 完整且无重复 |
| 增量展示 | Stage1/Stage2 先完成者先展示；其他保持 loading |
| 实名+头像 | 排名与成员区都显示 `avatar+name`，不出现 `anon_*`（除非映射异常） |
| Council Members bug | 回答阶段不再显示模型名作为主标签 |
| 进度条 | Stage1/Stage2 进度随 item 事件实时变化，成功/失败都推进进度 |
| 历史兼容 | 旧会话不报错；summary fallback 正常 |
