# Thinking Stream Integration Spec (Stage1/2/3)

> Status: Draft (approved direction)
> Scope: LLM Council full pipeline (Stage1, Stage2, Stage3) thinking stream

## 目录
1. 概述
2. 用户场景与需求描述
3. 目标与非目标
4. 核心定义与术语
5. 详细技术方案
   - 5.1 事件协议与数据结构
   - 5.2 后端改造设计
   - 5.3 前端改造设计
   - 5.4 持久化策略与结构
   - 5.5 渲染节流与性能策略
6. 技术架构图与流程图
7. UI 交互与呈现规范
8. 风险与对策
9. 需要改动的代码文件与关键修改点
10. 验收标准与质量指标
11. 待确认项与边界规则

---

## 1. 概述
本规范将 "Thinking Stream" 接入现有 LLM Council 系统，覆盖 Stage1/Stage2/Stage3 全流程。核心原则是:
1) 仅展示 "标题型思考" (thinking titles)，不展示 raw reasoning。
2) 保证 Stage2 JSON 严格可解析，不被思考流污染。
3) 流式展示与最终答案互不干扰，进入 Answering 即冻结 Thinking。
4) 持久化思考标题到对话记录，但限制容量并排除 filler。

---

## 2. 用户场景与需求描述

### 2.1 用户场景
| 场景 | 用户感知 | 期望体验 |
| --- | --- | --- |
| 多模型并发思考 | 不知道谁在忙 | 看到每个模型的最新思考标题 |
| Stage2/Stage3 时间长 | 空白或误以为卡死 | 有持续标题提示系统在工作 |
| 部分模型不支持 reasoning | 体验断裂 | 即使开启 Thinking，也正常返回结果 |
| 回看历史对话 | 无法复盘过程 | 能查看思考标题历史 |

### 2.2 用户需求
1) 支持 Thinking 开关: 有能力的模型展示思考标题，无能力模型保持正常输出。
2) Thinking 覆盖 Stage1/Stage2/Stage3。
3) 前端采用混合方案: 默认全局 Console 显示最新标题，点击某人展开详情。
4) Thinking 标题需要持久化，但不存 filler，不存 raw reasoning。
5) Stage2 JSON 输出必须严格可解析，不得被 Thinking 干扰。

---

## 3. 目标与非目标

### 3.1 目标 (Must)
1) 统一 SSE 事件 type: "thinking"，包含 stage 字段。
2) Thinking 标题仅通过 tool_call 输出 (title)，保证 Stage2 JSON 不被污染。
3) 进入 Answering (content) 后冻结 Thinking，不再接受标题。
4) Thinking 标题持久化至对话记录，并设置上限。
5) 前端显示: 全局 Console + 单人折叠详情。

### 3.2 非目标 (Out of scope)
1) 不展示 raw reasoning。
2) 不引入复杂的实时协作或多端同步。
3) 不改动业务规则 (Stage1/2/3 逻辑与评分规则保持不变)。

---

## 4. 核心定义与术语
| 术语 | 说明 |
| --- | --- |
| Thinking Title | 通过 tool_call 输出的步骤标题 |
| Console | 全局最新标题显示区域 |
| Capsule | 每个模型的思考展示折叠面板 |
| Freeze | 一旦收到 Answering 内容，Thinking 停止 |
| Filler | TTFB 期间的占位文本，不持久化 |

---

## 5. 详细技术方案

### 5.1 事件协议与数据结构

#### SSE 事件
统一使用:
```json
{
  "type": "thinking",
  "stage": "stage1|stage2|stage3",
  "councilor_id": "immanuel_kant",
  "model": "openai/gpt-oss-20b:free",
  "delta": "拆解用户需求",
  "is_title": true,
  "t": 12.4
}
```

#### 规则
1) `type` 固定为 "thinking"。
2) `stage` 明确归属。
3) `delta` 只接收标题，不接收 raw reasoning。
4) `is_title` 必须为 true (禁止 reasoning 混用)。
5) `t` 为相对时间戳 (seconds since request start)。

### 5.2 后端改造设计

#### 5.2.1 OpenRouter Streaming
- 新增 streaming query 接口，支持 tool_calls 与 content delta。
- Tool call arguments 可能分片流式传输，必须缓冲拼接直到 JSON 可解析。

#### 5.2.2 Stage1/2/3 Thinking Hooks
- Stage1/2/3 均提供 on_thinking 回调。
- Thinking 事件进入 SSE queue，与 stage1_item/stage2_item 并行。

#### 5.2.3 冻结规则
- 一旦收到 content (Answering 开始)，立即冻结 Thinking。
- 冻结后，不再处理任何 tool_call title。
- Stage2 JSON 输出必须完全纯净 (不得夹带标题)。

#### 5.2.4 模型能力标注
配置新增:
```json
capabilities: {
  "thinking": true,
  "mode": "tool"
}
```
用途:
1) 能力判断 (支持则启用 thinking)。
2) 兼容不支持 reasoning/tool 的模型。

### 5.3 前端改造设计

#### 5.3.1 状态结构
建议新增 thinking store:
```js
thinkingState = {
  stage1: { councilor_id: [ {t, title} ] },
  stage2: { councilor_id: [ {t, title} ] },
  stage3: { councilor_id: [ {t, title} ] }
}
```

#### 5.3.2 渲染逻辑
- Console: 展示每个 councilor 最新一条标题 (跨 stage 或按 stage filter)。
- Capsule: 点击头像展开，显示该 councilor 各 stage 历史 (最近 N 条)。
- 不显示 filler (仅运行时状态可用)。

#### 5.3.3 展示节流
- Display throttling: 每 200ms 批量更新 UI。
- Buffer 保留完整日志，但写入上限限制。

### 5.4 持久化策略与结构

#### 5.4.1 持久化范围
1) 仅保存 Thinking 标题。
2) 不保存 filler。
3) 不保存 raw reasoning。

#### 5.4.2 上限策略
- 单模型单 stage: 最大 50 条标题。
- 单条对话总标题: 最大 200 条。
- 超出时丢弃最旧。

#### 5.4.3 持久化结构 (存入 message.metadata)
```json
"thinking": {
  "stage1": {
    "immanuel_kant": [
      {"t": 2.1, "title": "拆解用户需求"},
      {"t": 6.5, "title": "校验边界条件"}
    ]
  },
  "stage2": { "donald_trump": [ ... ] },
  "stage3": { "chairman": [ ... ] }
}
```

### 5.5 渲染节流与性能策略
- UI 渲染频率固定 200ms。
- Buffer 内部保留完整日志，不 drop middle。
- 当超过上限: 删除最旧。

---

## 6. 技术架构图与流程图

### 6.1 数据流 (ASCII)
```ascii
User -> Frontend -> /message/stream (SSE)
                  |
                  +-- thinking (stage1/2/3, tool_call title only)
                  +-- stage1_item
                  +-- stage2_item
                  +-- stage3_complete
                  +-- complete
```

### 6.2 Thinking 状态流转
```ascii
Idle -> Waiting -> Thinking -> Answering -> Finished
                (tool_call titles)   (content starts -> freeze)
```

### 6.3 前端展示结构
```ascii
┌─ Thinking Console ─────────────────────────────┐
│ 最新: 康德 · 拆解用户需求                       │
└────────────────────────────────────────────────┘
[Avatar Capsule] 康德 ▸ 点击展开历史
```

---

## 7. UI 交互与呈现规范

### 7.1 Console
- 默认显示每个 councilor 最新标题。
- 不显示 filler。
- 如需 stage filter, 需隐藏在 "more" 中，默认不打扰。

### 7.2 Capsule
- 头像点击展开。
- 展示该 councilor 各 stage 标题 (最近 N 条)。
- 标题规则: 6-18 字, 动词 + 对象, 无标点。

---

## 8. 风险与对策
| 风险 | 影响 | 对策 |
| --- | --- | --- |
| Stage2 JSON 被污染 | 解析失败 | tool_call 标题 + content 即冻结 |
| 模型不支持 tool_call | 无标题 | 能力标注 + fallback |
| 日志过大 | 存储膨胀 | 上限控制 + 不存 filler |
| 高频渲染 | UI 卡顿 | Display throttling |

---

## 9. 需要改动的代码文件与关键修改点

> 本文仅列出关键修改点，不提供实现代码。

### 后端
| 文件 | 修改点 | 关键逻辑 |
| --- | --- | --- |
| `backend/openrouter.py` | 新增 streaming query | SSE chunk 解析 + tool_call args 缓冲 |
| `backend/council.py` | Stage1/2/3 thinking 回调 | on_thinking + freeze 规则 |
| `backend/main.py` | SSE 添加 thinking 事件 | 统一 type="thinking", 带 stage |
| `backend/storage.py` | 持久化 thinking | 保存 metadata.thinking |
| `backend/config.py` | capabilities 配置 | capabilities: {thinking, mode} |

### 前端
| 文件 | 修改点 | 关键逻辑 |
| --- | --- | --- |
| `frontend/src/api.js` | SSE 新事件 | 解析 type="thinking" |
| `frontend/src/components/ChatInterface.jsx` | thinking state | 统一缓存 + throttling |
| `frontend/src/components/Stage1.jsx` | Capsule 展示 | 展开显示 thinking 历史 |
| `frontend/src/components/CouncilAvatars.jsx` | 点击展开 | 点击头像触发展开 |
| `frontend/src/index.css` | Console 样式 | 全局 Console 样式 |

### 文档
| 文件 | 修改点 |
| --- | --- |
| `docs/配置说明.md` | 新增 capabilities 配置说明 |

---

## 10. 验收标准与质量指标
1) Stage1/2/3 均可看到 thinking 标题流。
2) Stage2 JSON 必须稳定可解析，无污染。
3) Thinking 标题持久化，且刷新后仍可查看。
4) 超过上限后最旧记录被清理。
5) UI 在 6 模型并发下不卡顿。

---

## 11. 待确认项与边界规则
1) 是否需要 stage filter 默认显示或隐藏。
2) 是否在历史回放中区分 stage1/2/3。
3) 标题频率是否需要硬性限制 (3-10s)。
4) 是否需要 "thinking 开关" 默认记忆上次选择。

