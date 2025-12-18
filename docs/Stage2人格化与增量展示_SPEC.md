# Stage2 人格化 + 严格 JSON + 增量展示（SPEC v1）

本文档定义本项目对 Stage1/Stage2/前端展示的统一实现规格，用于后续开发与验收。

---

## 0. 目标与硬约束

| 项 | 说明 |
|---|---|
| Stage2 人格化 | 每个 judge 在 Stage2 使用各自 `judge_persona` 进行评审，避免“同模型=同评审风格”。 |
| Stage2 严格 JSON | Stage2 输出必须严格按 schema；拒绝任何额外字段；不得输出 Markdown、解释、代码块。 |
| Stage2 请求形态不变 | 每个 judge **一次请求**，一次性对所有候选做 ranking（不改为逐候选多次请求）。 |
| 前端显示真实名字 | Stage2 排名展示时显示回答者真实角色名；评审输入仍保持匿名（`anon_*`）。 |
| 增量展示 | Stage1/Stage2 不等全员完成：谁先完成先展示，其余保持 loading/思考态。 |
| 不落盘中间态 | 增量 SSE 仅用于 UI；对话存储仍在全部完成后一次性保存。 |
| 旧会话兼容 | 历史消息若缺 `answer_summary`，前端用截断的 `answer_markdown` fallback。 |

---

## 1. 配置与数据源

| 配置项 | 位置 | 说明 |
|---|---|---|
| `persona_path` | `backend/config.py` | Stage1 人设（回答风格） |
| `judge_persona_path` | `backend/config.py` | Stage2 人设（评审风格） |
| `judge_system_prompt` | `backend/config.py` | Stage2 rubric/标准（可作为 rubric 的一部分） |
| `stage_limits.stage1/stage2` | `backend/config.py` | token/timeout 限制（Stage2 需应用 `max_output_tokens`） |

---

## 2. 输出 Schema

### 2.1 Stage1 输出（每位议员一次）

Stage1 只输出一个 JSON object（不得有额外文本），包含以下字段：

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

约束：
- `answer_summary`：必填，长度 ≤ 500（按字符计）。
- `judge_card`：沿用现有约束（如 `core_reasons` 至少 2 条、长度压缩规则等）。

### 2.2 Stage2 输出（每位 judge 一次）

Stage2 只输出一个 JSON object（不得有额外文本），顶层字段只允许：

```json
{
  "ranking": ["anon_1", "anon_2", "anon_3"],
  "scores": { "anon_1": 8, "anon_2": 6 },
  "rationale": "string"
}
```

约束：
- 顶层 key **只允许** `ranking`, `scores`, `rationale`：出现任何其他 key => invalid（触发重试）。
- `ranking`：必填，必须包含全部 `anon_id` 且每个恰好一次。
- `scores`：可选；若存在，key 只能是 `anon_id`；value 必须为 1–10 的整数。
- `rationale`：可选；若存在，建议限制长度（例如 ≤ 600 chars）以提升稳定性。

---

## 3. Stage2 输入数据（匿名候选）

Stage2 输入维持匿名：候选使用 `anon_id` 标识，并携带摘要与 judge_card：

| 字段 | 必填 | 说明 |
|---|---:|---|
| `anon_id` | 是 | `anon_1`、`anon_2`… |
| `answer_summary` | 是 | 来自 Stage1 的 `answer_summary`（≤500） |
| `judge_card` | 是 | 来自 Stage1 的 `judge_card` |

---

## 4. Prompt 结构（叠加与“格式不被带跑”）

### 4.1 Stage1（每位议员一次）

system prompt 结构：
1) `persona`（来自 `persona_path`）  
2) Stage1 任务说明：输出 JSON object，必须包含 `answer_markdown/answer_summary/judge_card`  
3) 强约束：只输出 JSON；禁止 Markdown fence、解释、寒暄

### 4.2 Stage2（每位 judge 一次）

messages 固定叠加顺序（JSON 硬约束最后一段最强）：

| 顺序 | role | 内容 |
|---:|---|---|
| 1 | `system` | `judge_persona`（来自 `judge_persona_path`） |
| 2 | `system` | `judge_rubric`（统一评审标准/维度/排序原则，可融合 `judge_system_prompt`） |
| 3 | `system` | `json_guard`（只输出 JSON + schema + 禁止额外字段 + anon_id 完整性） |
| 4 | `user` | payload（JSON）：`question` + `candidates[]` |

---

## 5. SSE 事件（增量展示）

### 5.1 事件类型（新增 item 级事件；保留 complete 兼容）

```
meta
stage1_start
stage1_item        (新增：单个议员完成)
stage1_complete
stage2_start
stage2_item        (新增：单个 judge 完成)
stage2_complete
stage3_start
stage3_complete
title_complete
complete
error
```

### 5.2 前端增量渲染规则

| UI 区域 | 增量来源 | 行为 |
|---|---|---|
| Stage1 面板 | `stage1_item` | 立即追加/更新该议员回答；其他议员保持 loading |
| Stage2 面板 | `stage2_item` | 立即追加/更新该 judge 评审；其他 judge 保持 loading |
| Council Members 状态 | item 是否到达 | 未到达=thinking；到达=completed |

---

## 6. “真实名字”展示与匿名映射

### 6.1 匿名映射（评审时匿名，展示时实名）

- 后端维护：`anon_map: { anon_id -> councilor_id }`
- 前端展示：用 `councilorLookup[councilor_id].name` 显示真实角色名

### 6.2 “回答阶段显示模型名而不是角色名”修复目标

消息视图里 `CouncilAvatars` 必须拿到 `{id,name,model}` 的 councilor objects（或等价映射），避免 fallback 显示为 modelId。

---

## 7. 兼容性与非目标

### 7.1 兼容性

| 场景 | 处理 |
|---|---|
| 历史会话 Stage1 缺 `answer_summary` | 前端 fallback：截断 `answer_markdown` 作为摘要显示/使用 |
| 旧前端 | 仍可只依赖 `stage1_complete/stage2_complete`（新增事件不破坏） |

### 7.2 非目标（v1 不做）

- 不做中途落盘（断线/刷新不保证恢复中间态）
- 不改 Stage2 “每 judge 一次请求”的机制
- 不做逐候选多次 review

