# Thinking 标题流 (Thinking Title Stream)
> 版本：v0.3.2 | 状态：Ready to Implement

## 目录
1. 概述
2. 用户场景与需求描述
3. 目标与非目标
4. 关键概念与术语
5. 详细技术方案
6. 状态机与流程图
7. 输出规范与示例
8. 验收标准与质量指标
9. 需要改动的代码文件与关键修改点
10. 风险与对策
11. 附录：Prompt 协议模板

---

## 1. 概述
本方案用于验证“Thinking 标题流”在模型推理等待期（TTFB ~30s）中的展示可行性。
核心目标是：让用户在等待期间看到连续的“标题/步骤”流，避免空白，同时不泄露模型内部推理。

**核心机制**：协议化 `tool_call` 主动输出标题 + Client 端 Filler 填充。

---

## 2. 用户场景与需求描述

### 2.1 典型用户场景
| 场景 | 用户感知 | 期望体验 |
| :--- | :--- | :--- |
| 模型推理 20–60s | 看到空白、误以为卡死 | 持续出现“思考标题”证明系统在工作 |
| 首个标题迟到 | 等待无反馈 | 2–4s 内出现 filler 占位 |
| 模型开始回答 | Thinking 继续刷标题 | 进入 Answering 后 Thinking 冻结 |
| 输出收尾 | 不知道过程有效性 | 输出标题统计小结，确认节奏与数量 |

### 2.2 用户需求（自然语言）
- 我只想看到“步骤标题”，不要长推理。
- 等待期间不能空白，要有 filler。
- 标题出现后，filler 应停止。
- 最终答案必须完整，不影响质量。
- CLI 原型即可，UI 要能肉眼验证体验。

---

## 3. 目标与非目标

### 3.1 目标（Must）
1. **内容型 Thinking**：通过 Tool Call 实时输出标题。
2. **只展示标题**：不显示 raw reasoning。
3. **TTFB 填充**：首个标题前输出 filler（2–4s/条，≤6 条）。
4. **流式驱动**：标题必须在 streaming 过程中出现。
5. **最终答案完整**：允许内部推理，最终输出不降质。
6. **状态冻结**：进入 Answering 后拒收任何标题。

### 3.2 非目标（Out of Scope）
- 不接入现有议会项目（Stage2/匿名化/并发等）。
- 不展示 raw reasoning。
- 不做复杂容灾（坏模型直接换）。
- 不实现多模型并发。

---

## 4. 关键概念与术语
| 术语 | 说明 |
| :--- | :--- |
| Filler | 2–4 秒一条的占位文本，用于填补首标题前的空白 |
| Title | `emit_thinking_title` 工具输出的标题 |
| Dual Channel | 同时监听 `tool_calls` 与 `content` 的兜底策略 |
| Freeze | 进入 Answering 后锁定 Thinking 面板，不再接受标题 |
| TTFB | First Token Time，首个标题到达前的等待期 |

---

## 5. 详细技术方案

### 5.1 通道设计（Dual Channel + Freeze）
- **通道 1：tool_calls**
  - `emit_thinking_title(title: string)`：输出标题。
  - `emit_final(final: string)`：输出最终答案（可选，默认不在 prompt 中要求）。
- **通道 2：content 兜底**
  - 最终答案**默认走 content**（可流式）。
  - 若模型意外调用 `emit_final`，客户端仍需兜底接住。

**冻结规则**：
- 一旦进入 Answering（收到 `emit_final` 或 `content`），Thinking 面板冻结。
- 冻结后**不再处理任何标题**（即使后续 tool_calls 仍有 title）。

### 5.2 Tool Call 参数流式拼接（关键补丁）
OpenRouter/OpenAI 的 `tool_calls[].function.arguments` 可能分片流式传输，导致半截 JSON。
**正确做法：客户端缓冲拼接，直到 JSON 可完整解析才更新 UI。**

**规则**：
- 对每个 tool_call 使用独立 buffer。
- 每次收到 arguments 增量就追加。
- 仅当 JSON 解析成功，才取出 `title` 更新 UI。
- 不允许渲染半截 JSON。

### 5.3 Filler 策略
- **启动**：请求发出即启动。
- **频率**：每 2–4 秒一条。
- **上限**：最多 3–6 条。
- **停止**：收到首条真实标题后立即停止。
- **保留**：已输出 filler 保留但标记灰色。

### 5.4 Windows 终端编码兼容
- PowerShell 默认编码可能非 UTF-8，导致 emoji 乱码。
- 要求：启动时设置 `sys.stdout.reconfigure(encoding='utf-8')`，或提示用户 `chcp 65001`。

---

## 6. 状态机与流程图

### 6.1 状态机表
| 阶段 | 触发条件 | UI 行为 | 状态机约束 |
| :--- | :--- | :--- | :--- |
| **Idle** | 脚本启动 | 等待输入 | - |
| **Waiting** | 请求发出 | **[FILLER] 启动** (每 2-4s 输出) | - |
| **Thinking** | 收到 `emit_thinking_title` | **[REAL] 显示**，停止 Filler | 必须在 Answering 前 |
| **Answering** | 收到 `content`（或 `emit_final` 兜底） | **[LOCK] 冻结 Thinking**，流式输出答案 | **此后拒收任何 Title** |
| **Finished** | 流结束 | 显示统计小结 | - |

### 6.2 流程图（ASCII）
```ascii
┌──────────┐      start request      ┌─────────────────────────┐
│   CLI    ├────────────────────────►│ OpenRouter Streaming API │
└──┬───────┘                          └─────────┬───────────────┘
   │ start filler timer                        │
   │                                           │ tool_call: emit_thinking_title (arguments stream)
   │◄──────────────────────────────────────────┘
   │ buffer arguments -> JSON OK -> add [REAL]
   │
   │                                content (primary) / emit_final (fallback)
   │◄──────────────────────────────────────────┐
   │ lock thinking -> stream final output
   │
   └───────────────────────── done ────────────┘
```

---

## 7. 输出规范与示例

### 7.1 Thinking 面板（Rich CLI 视觉）
```text
╭─ Thinking Process ──────────────────────────────────────────╮
│ ⠋ [FILLER] 正在分析上下文...                               │
│ ✔ [REAL]   拆解用户需求                                     │
│ ✔ [REAL]   对比可选路径                                     │
│ ✔ [REAL]   组织输出结构                                     │
╰─────────────────────────────────────────────────────────────╯
== Final Answer ==
...streaming final output...
over

[Stats] Titles: 4, Avg Gap: 6.2s
```

### 7.2 标题规则
- 单行，无标点。
- 6–18 字（中文），动词 + 对象。
- 不重复、不刷屏（3–10 秒/条）。

---

## 8. 验收标准与质量指标

### 8.1 功能验收（必须满足）
1. **TTFB 填充**：请求发出后 2–4s 出现 filler。
2. **真实标题**：至少出现 3 条真实标题。
3. **纯标题**：Thinking 面板无长推理文本。
4. **冻结规则**：进入 Answering 后无新增标题。
5. **最终答案完整**：Markdown/JSON 不缺失。

### 8.2 质量指标（建议）
| 指标 | 目标 |
| :--- | :--- |
| 标题重复率 | < 10% |
| 平均标题间隔 | 3–10 秒 |
| 标题长度 | 6–18 字 |

### 8.3 标题实时率评估表（肉眼验收）
| 维度 | 观察点 | 合格标准 | 备注 |
| :--- | :--- | :--- | :--- |
| 首条标题 TTFB | 请求后多久出现 title | ≤10s（若无则靠 filler） | 体验优先 |
| 标题数量 | 全程 title 数量 | ≥3 条 | 思考时间短可放宽 |
| 标题频率 | title 间隔 | 3–10 秒 | <3s 视为刷屏 |
| 断流情况 | 中途 title 消失 | 允许 1 次短停 | 断流过长需换模型 |
| 回答阶段冻结 | content 出现后仍有 title | 不允许 | 违规则判失败 |
| 最终答案 | content 完整输出 | 无断裂、无重复 | 结束标记为 "over" |

---

## 9. 需要改动的代码文件与关键修改点

> 本文仅描述修改范围和关键逻辑，不提供具体代码。

| 文件 | 修改点 | 关键逻辑 |
| :--- | :--- | :--- |
| `backend/openrouter.py` | 新增 streaming 客户端 | 支持 `stream=True` 的 SSE 解析；输出 tool_calls 与 content delta |
| `thinking_stream_test.py` (新脚本) | CLI 原型 | Rich UI + 状态机 + filler + 统计 |
| `docs/THINKING_TITLE_STREAM.md` | 文档更新 | 明确 tool_call 参数流式拼接规则 |

**关键修改点（逻辑级）**
1. **Tool Call 参数累积**：对 `tool_calls[].function.arguments` 做 buffer 聚合，JSON parse 成功后才更新 UI。
2. **双通道监听**：同一 chunk 可能含 tool_calls 与 content，需同时处理。
3. **冻结规则**：进入 Answering 后拒收新的 title。
4. **Windows 编码处理**：确保 emoji 不乱码。

---

## 10. 风险与对策
| 风险 | 影响 | 对策 |
| :--- | :--- | :--- |
| 模型不调用工具 | Thinking 区只有 filler | prompt 强约束；模型不可用则更换 |
| tool_call 参数分片 | UI 乱码或半截 | 追加 buffer，JSON parse 成功才更新 |
| 标题过密 | 影响阅读/耗 tokens | prompt 频率约束 3–10 秒 |
| 输出乱码 | Windows 终端无法显示 emoji | 强制 UTF-8 或提示 `chcp 65001` |

---

## 11. 附录：Prompt 协议模板
```markdown
你是一个专家 AI。在回答问题前，你必须进行深入思考，但思考过程对用户不可见。
你需要通过调用工具 emit_thinking_title(title="...") 向用户汇报思考进度。

规则：
1. 思考过程要通过多次调用 emit_thinking_title 展现（至少 1 次）。
2. 标题要简练（6–18字），像步骤名（如“分析数据”、“校验约束”），无标点。
3. 不要把推理过程写在 content 里，最终答案直接输出在 content 中，不要调用 emit_final。
4. 标题频率控制为每 3–10 秒一条，避免刷屏。
5. 回答完毕必须输出 "over" 作为结束标记。
```
