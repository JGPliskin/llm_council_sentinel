# Stage2 人格化 + 严格 JSON + 增量展示（综合SPEC）

本文档整合两份方案的优点，定义 Stage2 人格化、严格 JSON 输出和增量展示的统一实现规格。

---

## 0. 目标与硬约束

| 项 | 说明 |
|---|---|
| Stage2 人格化 | 每个 judge 使用各自 `judge_persona` 进行评审，避免“同模型=同评审风格” |
| Stage2 严格 JSON | 输出必须严格按 schema；拒绝额外字段；不得输出 Markdown、解释、代码块 |
| Stage2 请求形态不变 | 每个 judge **一次请求**，一次性对所有候选做 ranking（不改为逐候选多次请求） |
| 前端显示真实名字 | Stage2 排名展示时显示回答者真实角色名；评审输入仍保持匿名（`anon_*`） |
| 增量展示 | Stage1/Stage2 不等全员完成：谁先完成先展示，其余保持 loading/思考态 |
| 不落盘中间态 | 增量 SSE 仅用于 UI；对话存储仍在全部完成后一次性保存 |
| 旧会话兼容 | 历史消息若缺 `answer_summary`，前端用截断的 `answer_markdown` fallback |
| Persona 边界控制 | Persona 仅影响评审风格和理由表述，不得影响 JSON 格式和 ranking 完整性 |

---

## 1. 配置与数据源

| 配置项 | 位置 | 说明 |
|---|---|---|
| `persona_path` | `backend/config.py` | Stage1 人设（回答风格） |
| `judge_persona_path` | `backend/config.py` | Stage2 人设（评审风格） |
| `judge_system_prompt` | `backend/config.py` | Stage2 rubric/评审标准 |
| `stage_limits.stage1/stage2` | `backend/config.py` | token/timeout 限制 |

---

## 2. 输出 Schema

### 2.1 Stage2 输出（每位 judge 一次）

Stage2 只输出一个 JSON object（不得有额外文本），顶层字段只允许：

```json
{
  "ranking": ["anon_1", "anon_2", "anon_3"],
  "scores": { "anon_1": 8, "anon_2": 6 },
  "rationale": "string"
}
```

**约束**：
- 顶层 key **只允许** `ranking`, `scores`, `rationale`：出现任何其他 key => invalid（触发重试）
- `ranking`：必填，必须包含全部 `anon_id` 且每个恰好一次
- `scores`：可选；若存在，key 只能是 `anon_id`；value 必须为 1–10 的整数
- `rationale`：可选；若存在，建议限制长度（≤ 600 chars）以提升稳定性

---

## 3. Stage2 Prompt 结构（叠加机制）

messages 固定叠加顺序（JSON 硬约束最后一段最强）：

| 顺序 | role | 内容 |
|---:|---|---|
| 1 | `system` | `judge_persona`（来自 `judge_persona_path`，评审风格） |
| 2 | `system` | `judge_rubric`（来自 `judge_system_prompt`，评审标准） |
| 3 | `system` | `json_guard`（硬约束：只输出 JSON + schema + 禁止额外字段 + anon_id 完整性） |
| 4 | `user` | payload（JSON）：`question` + `candidates[]` |

**JSON 硬约束内容**：
```
HARD CONSTRAINTS:

* Output exactly one JSON object and nothing else.
* No markdown fences. No extra commentary. No emojis.
* ranking must include ALL anon_ids exactly once.
* Only allowed fields: ranking, scores, rationale.
```

---

## 4. 后端实现细节

### 4.1 修改文件：`backend/council.py`

#### 1. 更新 `_build_ranking_messages` 函数
- 新增参数：`councilor`（包含 persona 和 rubric 信息）
- 构建叠加的 system prompt（按上述顺序）
- 确保 JSON 约束始终在最后

#### 2. 更新 `_collect_single_ranking_bounded` 函数
- 传递 `councilor` 参数给 `_build_ranking_messages`
- 保持现有重试机制：JSON 错误或可重试网络错误时重试一次

#### 3. 维持匿名评审机制
- 评委仍只看到 `anon_id` 标识的候选
- 后端维护 `anon_map: { anon_id -> councilor_id }` 用于前端映射

### 4.2 修改文件：`backend/main.py`

#### 1. 实现增量流处理
- 创建 `stage1_stream_responses` 异步生成器
- 创建 `stage2_stream_rankings` 异步生成器
- 立即调度所有任务，当单个结果返回时 yield 更新

#### 2. SSE 事件类型

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

#### 3. 事件 payload 要求
- `stage1_item` 和 `stage2_item` 事件包含单个完成结果
- `stage2_complete` 事件包含完整排名和 `anon_to_name` 映射
- 所有 Stage2 事件包含 `anon_to_councilor` 和 `anon_to_name` 映射信息

---

## 5. 前端实现细节

### 5.1 修改文件：`frontend/src/components/ChatInterface.jsx`

#### 1. 处理增量 SSE 事件
- 监听 `stage1_item` 和 `stage2_item` 事件
- 实时更新 Stage1 和 Stage2 组件的响应数据
- 保持未完成结果的 loading 状态

#### 2. 修复“Council Members”显示问题
- 构建 `councilors` prop 时使用稳定的议员 ID
- 优先数据源：`msg.meta.resolved_councilor_ids` → 会话级活跃议员列表 → msg.stage1 结果 ID
- 确保 `CouncilAvatars` 组件始终有访问角色名的权限

### 5.2 修改文件：`frontend/src/components/Stage2.jsx`

#### 1. 真实名字显示逻辑
- 优先使用 `anon_to_name` 映射显示排名标签
- 备选方案：`anon_to_councilor` + `councilorLookup[id].name`
- 最后 fallback：`anon_id`（应极少出现）

#### 2. 增量更新处理
- 接收部分排名数据并立即显示
- 保持未完成评审的 loading 状态
- 避免重复渲染或数据覆盖

### 5.3 Emoji 头像实现
- 在 `DEFAULT_COUNCILORS` 数组中添加 `avatar` 字段
- 在标签页和排名中显示 Emoji + 角色名

| 议员ID | 姓名 | Emoji头像 |
|--------|------|-----------|
| immanuel_kant | 康德 | 🎓 |
| donald_trump | 特朗普 | 🗽 |
| hideo_kojima | 小岛秀夫 | 🎮 |

---

## 6. 实时进度显示

在每个 Stage 容器的 CardHeader 下方显示进度条：

```
┌─────────────────────────────────────────┐
│ Stage 2: 评审阶段                       │
│ 每个评审员将对回答进行评分和排序         │
│ ┌─────────────────────────────────────┐ │
│ │ 进度：█████████████░░░░░░░ 70%     │ │
│ │ 康德 🎓 完成 | 特朗普 🗽 80% | 小岛 🎮 50% │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

**实现要点**：
- 使用 React 状态管理进度数据
- 监听 SSE 事件更新进度
- 使用 CSS 动画实现进度条平滑过渡
- 显示每个议员的完成状态

---

## 7. 验证计划

### 7.1 自动化测试
- 无现有自动化测试，将在后续版本考虑添加

### 7.2 手动验证

| 测试项 | 测试内容 | 预期结果 |
|---|---|---|
| Stage2 人格化 | 同一模型的不同议员评审风格应明显不同 | 评审理由和风格差异显著 |
| 严格 JSON 输出 | 检查所有 Stage2 输出 | 100% 符合 JSON schema 要求 |
| 前端真实名字显示 | 检查 Stage2 排名 | 显示真实角色名而非匿名标签 |
| 增量展示 | 观察 Stage1 和 Stage2 | 先完成的议员/评委立即显示，其余保持 loading |
| Council Members 显示修复 | 检查消息视图 | 显示角色名而非模型 ID |
| 进度条显示 | 观察评审过程 | 进度条实时反映完成情况 |
| 重试机制 | 模拟 JSON 错误 | 系统自动重试一次 |
| 历史会话兼容 | 查看旧会话 | 正确显示，无报错 |

---

## 8. 兼容性与非目标

### 8.1 兼容性
- 历史会话若缺少 `answer_summary`，前端使用截断的 `answer_markdown` 作为 fallback
- 旧前端仍可只依赖 `stage1_complete/stage2_complete` 事件（新增事件不破坏兼容性）

### 8.2 非目标（v1 不做）
- 不实现 anon_id 随机洗牌
- 不实现评委自我评审排除
- 不改变 Stage2 一次请求的机制
- 不做中途落盘（仅 UI 实时更新）
- 不优化 token 使用（正确性和用户体验优先）

---

## 9. 风险与缓解措施

| 风险点 | 影响 | 缓解措施 |
|--------|------|----------|
| Persona 影响 JSON 格式 | 系统无法解析评审结果 | JSON 约束始终置于 prompt 最后；实现重试机制 |
| Persona 过度影响评审 | 评审结果偏离客观标准 | 评审标准置于 persona 之后；保持匿名评审机制 |
| 增量更新性能问题 | 频繁更新导致 UI 卡顿 | 使用 React.memo 优化组件；限制更新频率 |
| 网络延迟导致的不一致 | UI 显示与实际状态不符 | 实现状态同步机制；提供加载状态反馈 |

---

## 10. 未来扩展

- Emoji 头像可无缝替换为图片 URL
- 进度条可扩展为更详细的任务状态展示
- 可考虑添加自动化测试覆盖增量流场景
- 可优化 token 使用，减少成本