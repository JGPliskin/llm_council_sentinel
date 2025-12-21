# Thinking Stream Review - Issues & Fix Recommendations

> Scope: Review of current code vs. `docs/THINKING_STREAM_INTEGRATION_SPEC.md` and agreed UI/UX.
> Status: Findings + fixes only. No code changes included.

## 目录
1. 结论摘要
2. 阻断级问题（功能不工作）
3. 高优先级问题（明显偏离需求）
4. 中优先级问题（体验/一致性问题）
5. UI/审美问题（不符合约定展示方案）
6. 未实现功能清单
7. 修复建议（按优先级）
8. 全量修复方案（像 Gem 一样的完整实施想法）
9. 验收用例与检查清单（无歧义版）
10. 参考文件与定位

---

## 1. 结论摘要
当前实现与约定展示方案存在明显偏差：  
1) “全局 Console + 点击头像展开”未实现，仅做了头像气泡。  
2) Stage1 思考标题流经常不显示（解析逻辑有缩进错误）。  
3) Thinking 开关未实现。  
4) Stage3 thinking 回调未 await，事件可能被丢弃。  
5) 思考数据结构与前端展示存在多处不一致，导致部分模型不显示或只显示单人。

---

## 2. 阻断级问题（功能不工作）

### 2.1 Thinking 解析缩进错误，导致 Stage1 Thinking 不显示
在流式解析中，`tool_calls` 处理被缩进到 `content` 逻辑块内，若模型只输出 tool_call（标题）而没有 content，则 thinking 事件不会发出。
- 位置: `backend/openrouter.py:78-84`
- 影响: Stage1/Stage2/Stage3 可能完全无标题流。

### 2.2 Stage3 thinking 回调未 await
Stage3 的 `_think_cb` 是同步函数，调用 `on_thinking` 但没有 await，`on_thinking` 在 `main.py` 是 async，导致 thinking 事件可能不入队或被丢弃。
- 位置: `backend/council.py:1143-1147`
- 影响: Stage3 thinking 不稳定或缺失。

---

## 3. 高优先级问题（明显偏离需求）

### 3.1 未实现 “Thinking 开关”
需求明确存在 thinking toggle，但当前前端没有任何开关 UI，后端也没有 gating 参数。
- 位置: `frontend/src/App.jsx`, `frontend/src/components/ChatInterface.jsx`
- 影响: 无法控制 thinking 功能开关，违背 spec。

### 3.2 未实现 “全局 Console + 点击头像展开”
当前仅实现头像气泡，没有全局 Console 列表，也没有集中展示最新标题。
- 位置: `frontend/src/components/CouncilAvatars.jsx`
- 影响: UI 方案与约定完全不一致，信息分散难扫读。

### 3.3 Prompt 未强制 tool_call 输出标题
Stage1/2/3 的 system prompt 未要求 `emit_thinking`，导致多数模型不会输出 thinking。
- 位置: `backend/council.py:261-283` 及 Stage2/Stage3 prompt 区域
- 影响: thinking 事件非常不稳定。

---

## 4. 中优先级问题（体验/一致性问题）

### 4.1 思考标题键值不一致导致“只显示一人”
thinking 事件使用 `councilor_id` 为 key，但 UI 会使用 `model` 或 `id` fallback，导致匹配失败。
- 位置: `frontend/src/App.jsx:165-191`, `frontend/src/components/CouncilAvatars.jsx:371-393`
- 影响: 仅部分头像显示气泡（通常只有第一个匹配成功）。

### 4.2 思考清空时机不当
`stage1_complete` / `stage2_complete` / `stage3_complete` 全部清空 title，可能导致下一阶段标题刚出现就被覆盖或清空。
- 位置: `frontend/src/App.jsx:196-209` 和后续 stage complete 分支
- 影响: 标题闪烁、阅读断层。

### 4.3 Thinking 状态未做渲染节流
每个 thinking 事件都触发 `setState`，并发时会明显卡顿。
- 位置: `frontend/src/App.jsx:154-193`
- 影响: UI jitter、性能问题。

---

## 5. UI/审美问题（不符合约定展示方案）

### 5.1 气泡样式与布局不符合“Console + 展开”的清晰结构
目前 bubble 直接挂在头像上，缺少全局列表与结构化历史。  
视觉上：
- bubble 过小且靠近头像，不利于阅读长标题；
- 多人并发时排列混乱；
- 无集中信息区，用户需逐个头像找标题。

相关样式文件：
- `frontend/src/components/CouncilAvatars.css`
  - `.thinking-bubble` 设置为 `max-width: 140px` + `font-size: 10px`
  - 对于 6-18 字标题偏紧凑，易截断。

### 5.2 缺少“Console 区域”视觉层级
按 spec 应有独立区域显示“最新标题列表”，目前没有任何对应容器。

---

## 6. 未实现功能清单
以下功能在 spec 中要求，但当前未看到实现：
1) Thinking 开关（前端 UI + 后端参数 + prompt gating）。
2) 全局 Console 列表（默认显示最新标题）。
3) 点击头像展开历史（局部折叠面板与 Console 协同）。
4) Stage filter（可隐藏亦可，不存在任何入口）。

---

## 7. 修复建议（按优先级）

### P0（阻断修复）
1) 修复 `backend/openrouter.py` 缩进，确保 `tool_calls` 在所有 chunk 都解析。
2) Stage3 `on_thinking` 改为 async 并 await，或统一 async 回调约定。

### P1（需求对齐）
3) 增加 Thinking 开关（UI + 请求参数 + 后端 gating）。
4) 实现全局 Console 区域（显示每个 councilor 最新标题）。
5) 调整 UI 为 “Console + 点击头像展开历史”，保留 capsule 展开而非单一 bubble。

### P2（稳定性/性能）
6) 统一 thinking key 映射（强制 councilor_id -> model 映射）。
7) 修正清空时机，避免跨阶段标题闪烁。
8) 加入渲染节流（200ms 批量更新）。
9) 补 prompt 规则，强制 `emit_thinking` 调用。

---

## 8. 全量修复方案（像 Gem 一样的完整实施想法）

> 目的：把所有需求完整落地，包含 UI、协议、存储、可用性与美观。  
> 注意：以下是完整建议清单，不含代码实现。

### 8.1 统一数据协议与契约
1) SSE 事件统一为 `type: "thinking"`，并带 `stage` 字段。
2) Thinking 事件 payload 固定结构：
   - `stage`: "stage1" | "stage2" | "stage3"
   - `councilor_id`: 必须存在
   - `model`: 可选但建议带
   - `delta`: 标题文本（不得包含 reasoning）
   - `is_title`: 固定 true
   - `t`: 相对时间戳（秒）
3) 强制使用 `councilor_id` 作为前端 key，model 仅用于显示/ fallback。
4) prompt 里明确要求 `emit_thinking`，并限制频率与长度，确保标题出现。

### 8.2 后端处理原则
1) 工具调用解析必须在所有 chunk 都执行，不能依赖 content。
2) `on_thinking` 必须是 async 且统一 await。
3) Stage2 JSON 不能被 thinking 污染：thinking 必须只走 tool_call。
4) `thinking_log` 按 `stage -> councilor_id -> list` 结构持久化。
5) 超限策略：
   - 单模型单 stage 50 条
   - 单消息总计 200 条
   - 超限丢弃最旧

### 8.3 前端展示方案（落实“Console + Capsule”）
1) 新增全局 Console 区域：
   - 显示每位 councilor 当前最新标题
   - 没有标题时显示 "Thinking..." 或空
2) 点击头像展开 Capsule 历史：
   - 展示该 councilor 所有标题历史（按时间序）
3) Bubble 可保留但必须弱化（仅作为 hover/小提示），不能替代 Console。
4) 视觉建议：
   - Console 用横向列表，标题左对齐可扫读
   - 颜色弱化但层级清晰（低干扰但可见）

### 8.4 Thinking 开关
1) UI 加 toggle（输入框旁边，默认记忆上次选择）。
2) toggle OFF：后端不发送 thinking 事件，prompt 也不要求 tool_call。
3) toggle ON：后端允许 thinking，prompt 要求 emit_thinking。

### 8.5 性能与稳定性
1) 前端 thinking 事件做节流（200ms 批量 setState）。
2) 批量更新：缓冲入 ref，然后在 RAF/定时器中刷新。
3) 避免 stage complete 时清空所有标题；只清空对应 stage 或只把 title 设为空，但保留历史。

---

## 9. 验收用例与检查清单（无歧义版）

### 9.1 基础功能
1) 开启 Thinking：发送消息后 2-4 秒内出现 Console 标题。
2) 关闭 Thinking：发送消息后无 Console 标题，仅显示答案。
3) Stage1/2/3 均能产生标题（至少 1 条/阶段/模型）。

### 9.2 UI 展示
1) Console 显示每位 councilor 最新标题，顺序与 councilor 顺序一致。
2) 点击头像弹出历史列表，包含全部标题（按时间序）。
3) 不允许只有第一个头像有标题，其它为空（除非该模型无标题事件）。

### 9.3 数据持久化
1) 刷新页面后仍可看到历史标题。
2) `metadata.thinking` 结构为 `stage -> councilor_id -> list`，且条数未超过上限。

### 9.4 性能
1) 6 个模型并发时 UI 不出现明显卡顿。
2) thinking 事件高频时不应每条都触发渲染（需节流）。

---

## 10. 参考文件与定位
后端：
- `backend/openrouter.py:78-84`
- `backend/council.py:1143-1147`
- `backend/council.py:261-283`
- `backend/main.py:658-684`

前端：
- `frontend/src/App.jsx:154-209`
- `frontend/src/components/CouncilAvatars.jsx:267-272`
- `frontend/src/components/CouncilAvatars.css:120-160`
- `frontend/src/components/ChatInterface.jsx:275-294`

---

如需我在此文档继续补充“修复路线图”或“对照 spec 的逐条验收项”，告诉我即可。 
