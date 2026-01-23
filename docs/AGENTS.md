# AGENTS.md - 技术架构与工作流（权威版）

本文档是系统流程与行为约束的权威说明，内容以当前代码为准（`backend/` 与 `frontend/src/`）。目标是“给任何人看都无歧义”。

---

## 1. 范围与定义

- **范围**：后端三阶段编排、模型分配、SSE 事件协议、持久化结构、前端状态机。
- **不包含**：测试代码（按要求跳过）。

核心术语：
- **Councilor**：参与 Stage1/Stage2 的议员模型
- **Chairman**：负责 Stage3 综合结论的模型
- **Thinking**：通过 `emit_thinking` 工具输出的公开推理步骤

---

## 2. 总体流程（ASCII）

```
create_conversation
   |
   v
meta (resolved_councilors + chairman)
   |
   v
Stage1 -> Stage2 -> Stage3
   |
   v
persist assistant message + metadata
```

---

## 3. 模型固定分配（schema_version=3）

### 3.1 触发时机
- 创建会话时执行 `assign_models_for_councilors`。
- 若旧会话无分配但 schema_version >= 3，则在首次发送消息时补分配。

### 3.2 规则
- 优先使用 **healthy** 模型，其次 **unknown**。
- 目标：尽量避免重复模型，重复时允许。
- 若候选池与健康池无交集：抛出 `CandidateIntersectionEmptyError`。

### 3.3 输出
- `model_assignments`：`{ councilor_id: model_id, chairman: model_id }`
- `assignment_seed`：可复现随机种子
- `assignment_strategy`：`healthy_first` 或 `healthy_first_then_unknown`

---

## 4. Stage1（并行答复）

### 4.1 输入
- 用户问题（字符串）
- Councilor 列表（对象数组）

### 4.2 输出
- `stage1_results[]`（每位议员一条）

### 4.3 Thinking 规则
- 若 `enable_thinking=true` 且模型支持工具：
  - 通过 `emit_thinking` 多次输出思考步骤
  - 若模型错误地把 JSON 放入正文，会被 `extract_thinking_from_content` 抽取

### 4.4 SSE 事件
- `stage1_start`
- `eta_update`（queue_start / done）
- `thinking`
- `stage1_answer_delta`
- `stage1_answer_done`
- `stage1_item`
- `stage1_complete`

---

## 5. Stage2（匿名互评）

### 5.1 匿名规则
- 对 Stage1 有效答案按顺序分配 `anon_1..n`。
- 生成映射：`anon_map = {anon_id: councilor_id}`。

### 5.2 排名 JSON 约束
输出必须为 JSON 对象，仅允许字段：
- `ranking`（必填，数组，包含全部 anon_id，且不重复）
- `scores`（可选，1-10 整数）
- `rationale`（可选）
- `per_candidate_comments`（必填，匿名候选 -> 评语，单条最多 200 字符）

### 5.3 Thinking 规则
- **必须多次调用 `emit_thinking`**
- `title`、`detail` 必须中文
- **必须包含 `target_anon_id`**

### 5.4 跳过规则
- 若有效候选 < 2：Stage2 直接跳过
- `stage2_start` 会包含 `skipped=true`
- 仍会产生 `stage2_complete`（`skipped=true`）

---

## 6. Stage3（主席综合）

### 6.1 输入
- Stage1 结果 + Stage2 结果

### 6.2 行为
- 若 Stage2 被跳过，则在输入中加入“评审阶段已跳过”说明
- 支持 `emit_thinking` 输出综合思考过程

---

## 7. SSE 协议（关键摘要）

事件顺序（典型）：
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

完整字段定义见：`docs/API_REFERENCE.md`。

---

## 8. ETA 与进度

- `eta_update` 在阶段开始时发送（queue_start）。
- 当某个议员/评审完成时发送 `reason=done`。
- ETA 基于 `concurrency_tracker` 与模型并发上限估算。

---

## 9. 持久化与元数据

### 9.1 会话存储
- `data/conversations/{id}.json`
- `messages` 为用户与 assistant 消息数组

### 9.2 Thinking 持久化限制
- 每阶段每人最多 50 条
- 总计最多 200 条
- 仅流式 `/message/stream` 写入 `metadata.thinking`

---

## 10. 前端状态机（useParliamentEngine）

关键状态：
- `stage`：`idle` / `stage1` / `stage2` / `stage3`
- `thinkingByCouncilor`：Stage1/3 thinking
- `stage2ThinkingByJudge`：Stage2 thinking（按 judge + target）
- `evaluationComments`：Stage2 评论（按 target）
- `etaByCouncilor` / `stageEtaMs`：ETA
- `aggregateRankings`：综合排名

UI 行为：
- Stage2：只要任意 judge 仍为 `thinking`，DetailPanel 显示 Thinking 视图
- Stage2 全部完成后切换到 Review 视图

---

## 11. 运行约束

- `MAX_MESSAGE_LENGTH = 1000`
- `/message` 与 `/message/stream` 限流 `5/min`
- `schema_version >= 3` 时忽略请求中的 `councilor_ids`

---

Last updated: 2026-01-23

