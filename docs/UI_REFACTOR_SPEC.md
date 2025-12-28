# LLM Council Sentinel - UI 重构技术规格文档

> 📅 文档版本: v1.0 | 更新日期: 2024-12-28
> 
> 🎯 目标: 将 `frontend_refactor/` 的 Cyberpunk 风格 UI 设计移植到 `frontend/` 主项目，对接真实后端 API

---

## 目录

- [1. 项目背景](#1-项目背景)
- [2. 用户场景与需求描述](#2-用户场景与需求描述)
- [3. 技术决策清单](#3-技术决策清单)
- [4. 数据结构映射表](#4-数据结构映射表)
- [5. 技术架构设计](#5-技术架构设计)
- [6. 组件迁移方案](#6-组件迁移方案)
- [7. 后端改动方案](#7-后端改动方案)
- [8. 代码文件改动清单](#8-代码文件改动清单)
- [9. 关键代码修改示例](#9-关键代码修改示例)
- [10. 验证测试计划](#10-验证测试计划)
- [11. 视觉设计规范](#11-视觉设计规范)
- [附录 A: 术语表](#附录-a-术语表)
- [附录 B: 参考文件](#附录-b-参考文件)

---

## 1. 项目背景

### 1.1 现状

| 目录 | 描述 | 数据来源 | 状态 |
|------|------|----------|------|
| `frontend/` | 旧项目，功能完整，UI 朴素 | 真实后端 API (SSE 流式) | ✅ 可运行 |
| `frontend_refactor/` | 新 UI，Cyberpunk 风格，视觉出色 | Mock 静态数据 | ⚠️ 仅演示 |

### 1.2 目标

将 `frontend_refactor/` 的视觉设计合并到 `frontend/`，实现：

1. **保留真实 API 调用能力** (SSE 流式、健康检测等)
2. **采用新 UI 的视觉风格** (Cyberpunk HUD、三段式布局)
3. **简化交互模式** (单轮对话、无追问)

### 1.3 非目标 (Out of Scope)

- 后端核心逻辑改动 (仅改 Stage 2 Prompt 输出格式)
- 新增业务功能
- 性能优化

---

## 2. 用户场景与需求描述

### 2.1 核心用户流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           用户流程图                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [首次访问] ──▶ [空对话列表] ──▶ [点击新建] ──▶ [WelcomeScreen]              │
│                                                                              │
│  [WelcomeScreen]                                                             │
│    ├── 选择议员 (点击 Avatar 切换选中)                                       │
│    ├── 输入 Prompt                                                           │
│    └── 点击 Launch ──▶ 创建对话 + 发送消息                                   │
│                                                                              │
│  [Stage 1] ──▶ [Stage 2] ──▶ [Stage 3] ──▶ [Consensus Ready Overlay]        │
│                                                                              │
│  [点击 Overlay] ──▶ [显示最终答案] ──▶ 对话结束 (只读)                        │
│                                                                              │
│  [点击历史对话] ──▶ [即时显示完整结果] (Stage 1/2/3 静态渲染)                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 界面布局

#### 桌面端 (>=768px)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [左侧边栏]         │ [中央内容区]                    │ [右侧详情面板]        │
│ TacticalSidebar    │ StageContentArea               │ UnifiedDetailPanel   │
│ w-64               │ flex-1                         │ w-[400px]            │
├─────────────────────────────────────────────────────────────────────────────┤
│                            [底部 HUD]                                        │
│                         TacticalHUD (h-[120px])                              │
│                         显示议员卡片、进度/排名                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 移动端 (<768px)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Header Bar]  [Menu Icon]                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                    [中央内容区]                                               │
│                    StageContentArea                                          │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│              [底部 HUD] TacticalHUD (缩小版)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│              [底部抽屉] UnifiedDetailPanel (h-[60vh])                        │
│              (可拖动收起/展开)                                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 各阶段界面状态

#### Stage 1: 并行生成

| 区域 | 显示内容 |
|------|----------|
| 中央内容区 | Tab 切换各议员回答 (Markdown)，底部显示 Judge Card |
| 右侧面板 | 当前选中议员的 Thinking 过程 (实时流) |
| 底部 HUD | 3 个议员卡片，各自显示进度条 (0~100%) |

#### Stage 2: 互评

| 区域 | 显示内容 |
|------|----------|
| 中央内容区 | Tab 切换各议员 (显示 Stage 1 回答，不变) |
| 右侧面板 | 对当前选中议员的评价列表 (来自其他议员) |
| 底部 HUD | 评审完成前：显示卡片；完成后：显示排名 + 平均排名 (#X.X) |

#### Stage 3: 综合

| 区域 | 显示内容 |
|------|----------|
| 中央内容区 | Tab 切换各议员 + Consensus Tab (主席最终答案) |
| 右侧面板 | 点击议员 Tab：显示对该议员的评价；点击 Consensus Tab：显示主席 Thinking |
| 底部 HUD | 排名 + 平均排名 |

#### Stage 3 完成

| 区域 | 显示内容 |
|------|----------|
| 全屏 Overlay | "Consensus Ready" 提示，点击后隐藏 |
| 底部 HUD | 排名 + 平均排名 (持续显示) |

### 2.4 历史对话查看

| 操作 | 行为 |
|------|------|
| 点击侧边栏历史对话 | 静态渲染完整 Stage 1/2/3 数据，无动画 |
| 修改议员 | ❌ 不支持，历史对话只读 |
| 继续追问 | ❌ 不支持，每轮对话独立 |

---

## 3. 技术决策清单

| # | 议题 | 决策 | 说明 |
|---|------|------|------|
| 1 | Agent ID 策略 | 前端维护映射 | 后端返回 `immanuel_kant`，前端映射到 UI 配置 |
| 2 | AgentResponse.content | Markdown | 保留 `react-markdown` 渲染 |
| 3 | 前端配置字段 | 只保留 `color` | 去掉 `role`，不需要额外展示字段 |
| 4 | Thinking 状态 | 简化两态 | `processing` / `complete`，不保留 `pending` |
| 5 | 进度条算法 | A+B 混合 | Stage1: 定时器平滑+完成跳变；Stage2/3: 比例 |
| 6 | Stage 2 跳过 | 复用旧逻辑 | 当有效回答 < 2 时自动跳过 |
| 7 | 匿名映射 | 显示真名 | 不再显示 `anon_X`，直接显示议员名 |
| 8 | Thinking 持久化 | 不持久化 | 只在当前 Session 显示，刷新后丢失 |
| 9 | 健康状态 UI | 显示+禁用 | 不健康议员灰显，不可选择 |
| 10 | 议员列表来源 | 后端 API | 完全依赖 `/api/councilors` 返回 |
| 11 | 对话历史 | 完整管理 | 列表、新建、删除 |
| 12 | 多轮对话 | 不支持 | 一轮 Q&A 后对话结束 |
| 13 | 议员选择时机 | WelcomeScreen | 新对话时选择，历史只读 |
| 14 | WelcomeScreen | 新对话显示 | `stage === 'idle'` 时显示 |
| 15 | 历史对话渲染 | 静态全量 | 即开即看，无动画重播 |
| 16 | 数据流架构 | Hook 改造 | 改造 `useParliamentEngine` 接入真实 SSE |
| 17 | 项目结构 | 原地改造 | 在 `frontend/` 中逐步替换组件 |
| 18 | shadcn/ui | 保留 | 继续使用 Card, Tabs 等组件 |
| 19 | Markdown | 保留 | 继续使用 `react-markdown` |
| 20 | i18n | 保留 | 继续使用 `react-i18next` |
| 21 | Judge Card | 保留 | 放在 Stage 1 回答底部 |
| 22 | Aggregate Rankings | 底部 HUD | 显示平均排名 (#X.X 格式，数值越低越好) |
| 23 | Scores | 底部 HUD | 显示在 HUD 议员卡片上 |
| 24 | Thinking History | 不保留 | Stage 2 覆盖 Stage 1 内容 |
| 25 | Stage 2 评价拆分 | 后端改 Prompt | 结构化输出 `per_candidate_comments` |
| 26 | HUD ConnectionOverlay | 不需要 | 去掉贝塞尔曲线连线 |
| 27 | Mobile 适配 | 保留新设计 | 底部抽屉 60vh |

---

## 4. 数据结构映射表

### 4.1 Agent/Councilor 身份

| 新 UI (Mock) | 旧 API (真实) | 映射方式 |
|--------------|---------------|----------|
| `AgentId = 'kant'` | `councilor.id = 'immanuel_kant'` | 前端配置映射 |
| `AgentProfile.name = 'KANT'` | `councilor.name = '康德'` | 使用后端返回 |
| `AgentProfile.color = 'orange'` | ❌ 无 | 前端配置补充 |
| `AgentProfile.avatar = '🧠'` | `councilor.avatar = '🧠'` | 使用后端返回 |

### 4.2 Stage 1 回答

| 新 UI (Mock) | 旧 API (真实) | 处理方式 |
|--------------|---------------|----------|
| `AgentResponse.title` | ❌ 无 | 去掉或从 Markdown H1 提取 |
| `AgentResponse.content: string[]` | `answer_markdown: string` | 直接渲染 Markdown |
| 无 | `judge_card: { stance, core_reasons }` | 保留显示 |
| 无 | `status: 'ok' / 'failed'` | 用于状态判断 |

### 4.3 Stage 2 评审

| 新 UI (Mock) | 旧 API (真实) | 处理方式 |
|--------------|---------------|----------|
| `PeerReview.from` | `judge_councilor_id` | 对应 |
| `PeerReview.to` | ❌ 无 (需拆分) | 后端改 Prompt 输出 |
| `PeerReview.comment` | `per_candidate_comments[anon_X]` | 后端新增字段 |
| 无 | `ranking: ['anon_1', 'anon_2', ...]` | 用于排序 |
| 无 | `scores: { anon_1: 9.2, ... }` | 用于 HUD 显示 |

### 4.4 Stage 3 最终答案

| 新 UI (Mock) | 旧 API (真实) | 处理方式 |
|--------------|---------------|----------|
| `MOCK_ANSWERS.chair.title` | ❌ 无 | 去掉 |
| `MOCK_ANSWERS.chair.content[]` | `stage3.response` | 直接渲染 Markdown |

### 4.5 Thinking 日志

| 新 UI (Mock) | 旧 API (真实) | 处理方式 |
|--------------|---------------|----------|
| `LogStep.id` | 无 | 前端生成唯一 ID |
| `LogStep.agentId` | `councilor_id` 或 `model` | 优先使用 `councilor_id` |
| `LogStep.text` | `delta` | 对应 |
| `LogStep.time` (string) | `t` (number) | 转换: `${t.toFixed(1)}s` |
| `LogStep.status` | 无 | 前端维护状态机 |

### 4.6 前端 UI 配置文件结构

```typescript
// src/config/councilors.ts

/**
 * 议员 UI 配置映射表
 * Key: 后端返回的 councilor.id
 * Value: 前端专用的 UI 属性
 */
export const COUNCILOR_UI_CONFIG: Record<string, {
  color: string;  // HUD 卡片高亮颜色，值为 Tailwind 色系名
}> = {
  "immanuel_kant": { color: "orange" },
  "donald_trump": { color: "red" },
  "hideo_kojima": { color: "blue" },
  "chairman": { color: "purple" },
};

/**
 * 获取议员 UI 配置
 * @param id 议员 ID
 * @returns UI 配置，若无则返回默认值
 */
export function getCouncilorUIConfig(id: string) {
  return COUNCILOR_UI_CONFIG[id] || { color: "gray" };
}
```

---

## 5. 技术架构设计

### 5.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            前端架构概览                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                           App.tsx                                   │    │
│  │  - 路由管理 (react-router-dom)                                       │    │
│  │  - 对话列表状态                                                       │    │
│  │  - URL 参数处理                                                       │    │
│  └──────────────────────────┬──────────────────────────────────────────┘    │
│                             │                                                │
│                             ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    useParliamentEngine Hook                         │    │
│  │  - SSE 流式订阅                                                       │    │
│  │  - 状态机管理 (idle → stage1 → stage2 → stage3)                       │    │
│  │  - 进度计算                                                           │    │
│  │  - Thinking 日志收集                                                   │    │
│  └──────────────────────────┬──────────────────────────────────────────┘    │
│                             │                                                │
│         ┌───────────────────┼───────────────────────────┐                   │
│         │                   │                           │                   │
│         ▼                   ▼                           ▼                   │
│  ┌─────────────┐    ┌─────────────────┐    ┌──────────────────────┐         │
│  │ Tactical    │    │ StageContent    │    │ UnifiedDetail        │         │
│  │ Sidebar     │    │ Area            │    │ Panel                │         │
│  │ (对话列表)   │    │ (主内容)         │    │ (详情面板)            │         │
│  └─────────────┘    └─────────────────┘    └──────────────────────┘         │
│                             │                                                │
│                             ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                       TacticalHUD                                   │    │
│  │  - AgentSlice 卡片 (进度/排名)                                        │    │
│  │  - Stage 指示器                                                       │    │
│  │  - Consensus Overlay                                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 状态流转图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         useParliamentEngine 状态机                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    ┌────────┐                                                                │
│    │  idle  │ ◀──────────────────────────────────────────────┐              │
│    └───┬────┘                                                 │              │
│        │ startSession(prompt)                                 │              │
│        │ 创建对话 + 发送消息                                    │              │
│        ▼                                                      │              │
│    ┌────────┐                                                 │              │
│    │ stage1 │                                                 │              │
│    └───┬────┘                                                 │              │
│        │ 所有 stage1_item 完成                                 │              │
│        │ (或收到 stage1_complete)                              │              │
│        ▼                                                      │              │
│    ┌────────┐                                                 │              │
│    │ stage2 │◀── 可能跳过 (N<2)                                │              │
│    └───┬────┘                                                 │              │
│        │ 收到 stage2_complete                                  │              │
│        ▼                                                      │              │
│    ┌────────┐                                                 │              │
│    │ stage3 │                                                 │              │
│    └───┬────┘                                                 │ reset()      │
│        │ 收到 stage3_complete                                  │              │
│        ▼                                                      │              │
│    ┌────────────┐                                             │              │
│    │ consensus  │──────────────────────────────────────────────┘              │
│    │ Unlocked   │                                                            │
│    └────────────┘                                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 SSE 事件处理流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SSE 事件处理流程                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  后端 SSE 流                                                                  │
│       │                                                                      │
│       ├── meta                 → 更新 resolvedCouncilors, 初始化占位符        │
│       ├── stage1_start         → stage = 'stage1', loading.stage1 = true    │
│       ├── stage1_item          → 更新对应议员的回答                           │
│       ├── thinking             → 更新 thinkingSteps (追加日志)               │
│       ├── stage1_complete      → 填充最终数据, loading.stage1 = false        │
│       │                                                                      │
│       ├── stage2_start         → stage = 'stage2', 初始化评审占位符           │
│       │   └── (skipped=true)   → 跳过 Stage 2, 直接等待 stage3               │
│       ├── stage2_item          → 更新对应评审结果                             │
│       ├── stage2_complete      → 填充最终数据, 计算 Aggregate Rankings        │
│       │                                                                      │
│       ├── stage3_start         → stage = 'stage3', loading.stage3 = true    │
│       ├── stage3_complete      → 填充最终答案, consensusUnlocked = true      │
│       │                                                                      │
│       └── complete             → 流结束, isLoading = false                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.4 侧边详情面板内容逻辑

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   UnifiedDetailPanel 内容决策逻辑                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  function getDetailPanelContent(stage, activeTab):                          │
│                                                                              │
│    if activeTab === 'final' (Consensus Tab):                                │
│      return Stage3 主席 Thinking 日志                                        │
│                                                                              │
│    if stage === 'stage1':                                                   │
│      return 当前议员 (activeTab) 的 Thinking 日志                            │
│                                                                              │
│    if stage === 'stage2' OR stage === 'stage3':                             │
│      return 对当前议员的评价列表 (来自其他所有 Judge)                          │
│             每条评价包含:                                                     │
│             - 评审者 Avatar + 名字                                           │
│             - 对该议员的评语 (per_candidate_comments[anon_X])                 │
│             - 评分 (scores[anon_X])                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.5 底部 HUD 状态逻辑

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TacticalHUD 显示状态                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Stage 1:                                                                    │
│    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                     │
│    │ 🧠 KANT      │  │ 🧱 TRUMP     │  │ 🎮 KOJIMA    │                     │
│    │ ████████░░░  │  │ ██████░░░░░  │  │ ██████████░  │                     │
│    │ 78%          │  │ 56%          │  │ 92%          │                     │
│    └──────────────┘  └──────────────┘  └──────────────┘                     │
│                                                                              │
│  Stage 2 (评审未完成):                                                        │
│    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                     │
│    │ 🧠 KANT      │  │ 🧱 TRUMP     │  │ 🎮 KOJIMA    │                     │
│    │ [等待评审]   │  │ [等待评审]   │  │ [等待评审]   │                     │
│    └──────────────┘  └──────────────┘  └──────────────┘                     │
│                                                                              │
│  Stage 2 完成 / Stage 3:                                                     │
│    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                     │
│    │ 🥇 康德      │  │ 🥈 小岛      │  │ 🥉 特朗普    │ ← 按排名排序         │
│    │ 平均 #1.2    │  │ 平均 #2.0    │  │ 平均 #2.8    │                     │
│    └──────────────┘  └──────────────┘  └──────────────┘                     │
│                                                                              │
│  Stage 3 完成:                                                               │
│    ┌─────────────────────────────────────────────────────────────────┐      │
│    │                    CONSENSUS READY OVERLAY                      │      │
│    │                     (点击后隐藏，HUD 继续显示排名)                │      │
│    └─────────────────────────────────────────────────────────────────┘      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. 组件迁移方案

### 6.1 组件映射表

| 新 UI 组件 | 迁移到 | 处理方式 |
|-----------|--------|----------|
| `index.tsx` (App) | `frontend/src/App.jsx` | 合并布局逻辑 |
| `WelcomeScreen.tsx` | `frontend/src/components/WelcomeScreen.jsx` | 新建 |
| `StageContentArea.tsx` | 替换 `ChatInterface.jsx` 中的消息渲染 | 重构 |
| `TacticalHUD.tsx` | `frontend/src/components/TacticalHUD.jsx` | 新建 |
| `TacticalSidebar` (in index) | 合并到 `Sidebar.jsx` | 样式迁移 |
| `UnifiedDetailPanel` (in index) | `frontend/src/components/DetailPanel.jsx` | 新建 |
| `useParliamentEngine.ts` | `frontend/src/hooks/useParliamentEngine.js` | 重写 |

### 6.2 保留的旧组件

| 组件 | 保留原因 | 需要修改 |
|------|----------|----------|
| `api.js` | 真实 API 调用逻辑 | 无 |
| `i18n.js` | 国际化配置 | 无 |
| `CouncilAvatars.jsx` | 议员头像 + 选择逻辑 | 样式调整 |
| `Stage1.jsx` | 保留 Judge Card 渲染 | 样式调整 |
| `Stage2.jsx` | 保留 Scores/Ranking 渲染 | 样式调整 |
| `Stage3.jsx` | Chairman 答案渲染 | 样式调整 |
| `Sidebar.jsx` | 对话列表管理 | 样式迁移 |

### 6.3 删除的旧组件

| 组件 | 删除原因 |
|------|----------|
| `ThinkingConsole.jsx` | 被 DetailPanel 替代 |
| `ThinkingHistory.jsx` | 不再保留 |
| `ModelBeads.jsx` | 被 HUD 替代 |

---

## 7. 后端改动方案

### 7.1 Stage 2 Prompt 修改

**目标**：让 LLM 输出结构化的 `per_candidate_comments`，而不是一整段 `rationale`。

**修改文件**：`backend/council.py` - `_build_ranking_messages` 函数

**当前 Prompt 要求的 JSON 输出格式**：
```json
{
  "ranking": ["anon_1", "anon_2", "anon_3"],
  "rationale": "整段评价文字..."
}
```

**修改后的 JSON 输出格式**：
```json
{
  "ranking": ["anon_1", "anon_2", "anon_3"],
  "per_candidate_comments": {
    "anon_1": "对 anon_1 的具体评价，1-2 句话",
    "anon_2": "对 anon_2 的具体评价，1-2 句话",
    "anon_3": "对 anon_3 的具体评价，1-2 句话"
  },
  "summary": "可选的总结性评价"
}
```

### 7.2 Prompt 修改示例

```python
# backend/council.py

# 在 _build_ranking_messages 中修改 JSON Guard 部分

JSON_GUARD_PROMPT = """
你必须输出严格的 JSON 格式，结构如下：

{
  "ranking": ["anon_X", "anon_Y", ...],  // 按质量从高到低排序
  "per_candidate_comments": {
    "anon_X": "1-2 句话的具体评价",
    "anon_Y": "1-2 句话的具体评价"
    // ... 为每个候选人提供简短评价
  },
  "summary": "可选：整体总结"
}

规则：
1. ranking 数组必须包含所有候选人 ID
2. per_candidate_comments 必须为每个候选人提供独立评价
3. 每条评价不超过 50 字
4. 不要输出任何 JSON 以外的内容
"""
```

### 7.3 解析逻辑修改

```python
# backend/council.py - _parse_ranking_response

def _parse_ranking_response(response_text: str, expected_anon_ids: List[str]):
    # ... 现有解析逻辑 ...
    
    # 新增：提取 per_candidate_comments
    per_candidate_comments = parsed.get("per_candidate_comments", {})
    
    # 验证：确保所有候选人都有评价
    for anon_id in expected_anon_ids:
        if anon_id not in per_candidate_comments:
            per_candidate_comments[anon_id] = ""  # 兜底空字符串
    
    return {
        "ranking": ranking,
        "scores": scores,  # 如果有
        "per_candidate_comments": per_candidate_comments,
        "summary": parsed.get("summary", ""),
        # ... 其他字段
    }
```

### 7.4 SSE 事件格式更新

**stage2_item 事件新增字段**：

```json
{
  "type": "stage2_item",
  "data": {
    "judge_councilor_id": "immanuel_kant",
    "model": "openai/gpt-oss-20b:free",
    "ranking": ["anon_1", "anon_2", "anon_3"],
    "per_candidate_comments": {
      "anon_1": "展现了严谨的系统思维...",
      "anon_2": "对抗性方法缺乏可持续性考量...",
      "anon_3": "创意方案引入了不必要的复杂度..."
    },
    "status": "completed"
  }
}
```

---

## 8. 代码文件改动清单

### 8.1 前端文件 (frontend/src/)

| 文件 | 操作 | 改动说明 |
|------|------|----------|
| `App.jsx` | 修改 | 引入新布局，集成 HUD、DetailPanel |
| `App.css` | 修改 | 添加 Cyberpunk 主题变量 |
| `index.css` | 修改 | 全局样式调整 |
| **components/** | | |
| `WelcomeScreen.jsx` | **新建** | 从 frontend_refactor 移植 |
| `TacticalHUD.jsx` | **新建** | 从 frontend_refactor 移植 + 改造 |
| `DetailPanel.jsx` | **新建** | 从 frontend_refactor 移植 + 改造 |
| `StageContentArea.jsx` | **新建** | 从 frontend_refactor 移植 + 改造 |
| `ChatInterface.jsx` | 修改 | 大幅重构，拆分职责 |
| `Sidebar.jsx` | 修改 | 样式迁移为 Cyberpunk 风格 |
| `Stage1.jsx` | 修改 | 保留 Judge Card，样式调整 |
| `Stage2.jsx` | 修改 | 适配新字段 per_candidate_comments |
| `Stage3.jsx` | 修改 | 样式调整 |
| `CouncilAvatars.jsx` | 修改 | 样式调整 |
| `ThinkingConsole.jsx` | **删除** | 被 DetailPanel 替代 |
| `ThinkingHistory.jsx` | **删除** | 不再保留 |
| `ModelBeads.jsx` | **删除** | 被 HUD 替代 |
| **hooks/** | | |
| `useParliamentEngine.js` | **新建** | 真实 SSE 版本的状态机 |
| **config/** | | |
| `councilors.js` | **新建** | UI 配置映射 |

### 8.2 后端文件 (backend/)

| 文件 | 操作 | 改动说明 |
|------|------|----------|
| `council.py` | 修改 | Stage 2 Prompt + 解析逻辑 |
| `main.py` | 无 | 无需改动 |

### 8.3 样式文件

| 文件 | 操作 | 改动说明 |
|------|------|----------|
| `frontend/src/index.css` | 修改 | 添加 Cyberpunk 主题 CSS 变量 |
| `frontend/src/App.css` | 修改 | 布局相关样式 |
| `frontend/src/components/TacticalHUD.css` | **新建** | HUD 专用样式 |

---

## 9. 关键代码修改示例

### 9.1 useParliamentEngine Hook (核心)

```javascript
// frontend/src/hooks/useParliamentEngine.js

import { useState, useCallback, useRef, useEffect } from 'react';
import { api } from '@/api';

/**
 * Parliament Engine Hook
 * 管理三阶段流程的状态机
 */
export function useParliamentEngine() {
  // === 核心状态 ===
  const [stage, setStage] = useState('idle'); // 'idle' | 'stage1' | 'stage2' | 'stage3'
  const [isLoading, setIsLoading] = useState(false);
  
  // === 数据状态 ===
  const [conversation, setConversation] = useState(null);
  const [resolvedCouncilors, setResolvedCouncilors] = useState([]);
  const [stage1Results, setStage1Results] = useState([]);
  const [stage2Results, setStage2Results] = useState(null);
  const [stage3Result, setStage3Result] = useState(null);
  
  // === 进度状态 ===
  const [agentProgress, setAgentProgress] = useState({}); // { [councilor_id]: 0~100 }
  const [stageProgress, setStageProgress] = useState(0);  // 0~100
  
  // === Thinking 日志 ===
  const [thinkingSteps, setThinkingSteps] = useState([]);  // Stage 1 日志
  const [evaluationComments, setEvaluationComments] = useState({}); // Stage 2 评价映射
  const [synthesisSteps, setSynthesisSteps] = useState([]); // Stage 3 日志
  
  // === UI 状态 ===
  const [activeTab, setActiveTab] = useState(null);
  const [consensusUnlocked, setConsensusUnlocked] = useState(false);
  const [hasViewedConsensus, setHasViewedConsensus] = useState(false);
  const [aggregateRankings, setAggregateRankings] = useState([]);
  
  // === 定时器引用 (用于进度平滑) ===
  const progressTimers = useRef({});
  
  /**
   * 启动新会话
   * @param {string} prompt 用户输入
   * @param {string[]} councilorIds 选中的议员 ID
   */
  const startSession = useCallback(async (prompt, councilorIds) => {
    // 1. 创建对话
    const newConv = await api.createConversation();
    setConversation(newConv);
    
    // 2. 重置状态
    setStage('stage1');
    setIsLoading(true);
    setConsensusUnlocked(false);
    setHasViewedConsensus(false);
    setThinkingSteps([]);
    setEvaluationComments({});
    setSynthesisSteps([]);
    setAgentProgress({});
    setStageProgress(0);
    
    // 3. 发送消息并订阅 SSE
    await api.sendMessageStream(
      newConv.id,
      prompt,
      handleSSEEvent,
      councilorIds,
      true // enableThinking
    );
  }, []);
  
  /**
   * SSE 事件处理器
   */
  const handleSSEEvent = useCallback((eventType, event) => {
    switch (eventType) {
      case 'meta':
        handleMeta(event);
        break;
      case 'stage1_start':
        handleStage1Start();
        break;
      case 'stage1_item':
        handleStage1Item(event.data);
        break;
      case 'thinking':
        handleThinking(event);
        break;
      case 'stage1_complete':
        handleStage1Complete(event.data);
        break;
      case 'stage2_start':
        handleStage2Start(event);
        break;
      case 'stage2_item':
        handleStage2Item(event.data);
        break;
      case 'stage2_complete':
        handleStage2Complete(event.data);
        break;
      case 'stage3_start':
        handleStage3Start();
        break;
      case 'stage3_complete':
        handleStage3Complete(event.data);
        break;
      case 'complete':
        setIsLoading(false);
        break;
      case 'error':
        console.error('SSE Error:', event.message);
        setIsLoading(false);
        break;
    }
  }, []);
  
  // === 事件处理函数 ===
  
  const handleMeta = (event) => {
    setResolvedCouncilors(event.resolved_councilors || []);
    // 初始化进度
    const initialProgress = {};
    (event.resolved_councilors || []).forEach(c => {
      initialProgress[c.id] = 0;
      // 启动进度定时器 (平滑效果)
      startProgressTimer(c.id);
    });
    setAgentProgress(initialProgress);
    // 设置默认 Tab
    if (event.resolved_councilors?.length > 0) {
      setActiveTab(event.resolved_councilors[0].id);
    }
  };
  
  const startProgressTimer = (id) => {
    // 清除已有定时器
    if (progressTimers.current[id]) {
      clearInterval(progressTimers.current[id]);
    }
    // 启动新定时器，每 100ms 增长 2%，最多到 90%
    progressTimers.current[id] = setInterval(() => {
      setAgentProgress(prev => {
        const current = prev[id] || 0;
        if (current >= 90) {
          clearInterval(progressTimers.current[id]);
          return prev;
        }
        return { ...prev, [id]: current + 2 };
      });
    }, 100);
  };
  
  const handleStage1Item = (item) => {
    // 停止该议员的进度定时器
    if (progressTimers.current[item.councilor_id]) {
      clearInterval(progressTimers.current[item.councilor_id]);
    }
    // 设置进度为 100%
    setAgentProgress(prev => ({ ...prev, [item.councilor_id]: 100 }));
    // 更新结果
    setStage1Results(prev => {
      const index = prev.findIndex(r => r.councilor_id === item.councilor_id);
      if (index >= 0) {
        const copy = [...prev];
        copy[index] = item;
        return copy;
      }
      return [...prev, item];
    });
  };
  
  const handleThinking = (event) => {
    const step = {
      id: Date.now() + Math.random(),
      agentId: event.councilor_id,
      text: event.delta,
      time: `${event.t.toFixed(1)}s`,
      status: 'complete'
    };
    
    if (event.stage === 'stage1') {
      setThinkingSteps(prev => [...prev, step]);
    } else if (event.stage === 'stage3') {
      setSynthesisSteps(prev => [...prev, step]);
    }
  };
  
  const handleStage2Start = (event) => {
    setStage('stage2');
    // 清空 Stage 1 的 Thinking (被 Stage 2 覆盖)
    setThinkingSteps([]);
    
    if (event.skipped) {
      // Stage 2 被跳过，直接等待 Stage 3
    }
  };
  
  const handleStage2Item = (item) => {
    // 提取 per_candidate_comments 并映射到真实议员 ID
    const anonMap = conversation?.metadata?.anon_to_councilor || {};
    const comments = item.per_candidate_comments || {};
    
    // 将评价存储到对应的被评议员
    Object.entries(comments).forEach(([anonId, comment]) => {
      const targetId = anonMap[anonId];
      if (targetId) {
        setEvaluationComments(prev => {
          const existing = prev[targetId] || [];
          return {
            ...prev,
            [targetId]: [...existing, {
              fromId: item.judge_councilor_id,
              comment,
              score: item.scores?.[anonId]
            }]
          };
        });
      }
    });
    
    setStage2Results(prev => prev ? [...prev, item] : [item]);
  };
  
  const handleStage2Complete = (data) => {
    // 计算 Aggregate Rankings
    if (data.reviews && data.reviews.length > 0) {
      const rankings = calculateAggregateRankings(data.reviews, data.anon_map);
      setAggregateRankings(rankings);
    }
  };
  
  const handleStage3Start = () => {
    setStage('stage3');
  };
  
  const handleStage3Complete = (data) => {
    setStage3Result(data);
    setConsensusUnlocked(true);
  };
  
  /**
   * 计算汇总排名
   */
  const calculateAggregateRankings = (reviews, anonMap) => {
    // ... 排名计算逻辑 ...
    return [];
  };
  
  /**
   * 查看共识 (点击 Overlay)
   */
  const viewConsensus = useCallback(() => {
    setActiveTab('final');
    setHasViewedConsensus(true);
  }, []);
  
  /**
   * 重置状态
   */
  const reset = useCallback(() => {
    setStage('idle');
    setConversation(null);
    setResolvedCouncilors([]);
    setStage1Results([]);
    setStage2Results(null);
    setStage3Result(null);
    setAgentProgress({});
    setStageProgress(0);
    setThinkingSteps([]);
    setEvaluationComments({});
    setSynthesisSteps([]);
    setConsensusUnlocked(false);
    setHasViewedConsensus(false);
    setAggregateRankings([]);
    // 清理定时器
    Object.values(progressTimers.current).forEach(clearInterval);
    progressTimers.current = {};
  }, []);
  
  // === 清理 ===
  useEffect(() => {
    return () => {
      Object.values(progressTimers.current).forEach(clearInterval);
    };
  }, []);
  
  return {
    // 状态
    stage,
    isLoading,
    conversation,
    resolvedCouncilors,
    stage1Results,
    stage2Results,
    stage3Result,
    agentProgress,
    stageProgress,
    thinkingSteps,
    evaluationComments,
    synthesisSteps,
    activeTab,
    consensusUnlocked,
    hasViewedConsensus,
    aggregateRankings,
    
    // 操作
    setActiveTab,
    startSession,
    viewConsensus,
    reset,
  };
}
```

### 9.2 DetailPanel 内容选择逻辑

```javascript
// frontend/src/components/DetailPanel.jsx

/**
 * 获取当前应展示的详情内容
 */
function getDetailContent(stage, activeTab, thinkingSteps, evaluationComments, synthesisSteps) {
  // Consensus Tab → 显示主席思考过程
  if (activeTab === 'final') {
    return {
      type: 'thinking',
      title: 'Chairman Synthesis',
      data: synthesisSteps,
    };
  }
  
  // Stage 1 → 显示当前议员的思考过程
  if (stage === 'stage1') {
    const agentSteps = thinkingSteps.filter(s => s.agentId === activeTab);
    return {
      type: 'thinking',
      title: 'Thinking Process',
      data: agentSteps,
    };
  }
  
  // Stage 2 或 Stage 3 → 显示对当前议员的评价
  if (stage === 'stage2' || stage === 'stage3') {
    const comments = evaluationComments[activeTab] || [];
    return {
      type: 'evaluation',
      title: 'Peer Reviews',
      data: comments,
    };
  }
  
  return { type: 'empty', title: '', data: [] };
}
```

### 9.3 TacticalHUD 渲染逻辑

```jsx
// frontend/src/components/TacticalHUD.jsx

function TacticalHUD({
  stage,
  agentProgress,
  aggregateRankings,
  resolvedCouncilors,
  consensusUnlocked,
  hasViewedConsensus,
  onConsensusClick,
}) {
  // 排序议员：Stage 2 完成后按排名排序
  const sortedAgents = useMemo(() => {
    if (aggregateRankings.length > 0) {
      // 按排名排序
      return [...aggregateRankings].sort((a, b) => a.rank - b.rank);
    }
    // 默认顺序
    return resolvedCouncilors.map(c => ({
      councilor_id: c.id,
      name: c.name,
      avatar: c.avatar,
    }));
  }, [aggregateRankings, resolvedCouncilors]);
  
  // 渲染单个 Agent 卡片
  const renderAgentSlice = (agent, index) => {
    const hasRanking = aggregateRankings.length > 0;
    const progress = agentProgress[agent.councilor_id] || 0;
    const uiConfig = getCouncilorUIConfig(agent.councilor_id);
    
    return (
      <div 
        key={agent.councilor_id}
        className={`agent-slice border-${uiConfig.color}-500`}
      >
        {/* 排名徽章 */}
        {hasRanking && (
          <div className="rank-badge">
            {index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉'}
          </div>
        )}
        
        {/* Avatar + 名字 */}
        <div className="agent-avatar">{agent.avatar}</div>
        <div className="agent-name">{agent.name}</div>
        
        {/* 进度条 或 分数 */}
        {!hasRanking ? (
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ width: `${progress}%` }}
            />
          </div>
        ) : (
          <div className="score">{agent.average_rank?.toFixed(1)}分</div>
        )}
      </div>
    );
  };
  
  return (
    <div className="tactical-hud">
      {/* Stage 指示器 */}
      <div className="stage-indicator">
        STAGE [{stage === 'stage1' ? '01' : stage === 'stage2' ? '02' : '03'} / 03] 
        // {stage === 'stage3' && consensusUnlocked ? 'CONSENSUS' : stage.toUpperCase()}
      </div>
      
      {/* Agent 卡片列表 */}
      <div className="agent-slots">
        {sortedAgents.map((agent, index) => renderAgentSlice(agent, index))}
      </div>
      
      {/* Consensus Ready Overlay */}
      {consensusUnlocked && !hasViewedConsensus && (
        <div className="consensus-overlay" onClick={onConsensusClick}>
          <div className="overlay-content">
            <Sparkles className="icon" />
            <span>CONSENSUS READY</span>
            <span className="hint">TAP TO REVEAL</span>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## 10. 验证测试计划

### 10.1 功能测试用例

| 测试场景 | 预期行为 | 验证方法 |
|----------|----------|----------|
| 新建对话 | 显示 WelcomeScreen，可选议员 | 手动测试 |
| 发送消息 | 进入 Stage 1，显示进度条 | 观察 HUD |
| Stage 1 完成 | 自动进入 Stage 2 | 观察 Stage 指示器 |
| Stage 2 跳过 (N<2) | 显示跳过原因，直接进入 Stage 3 | 构造只有 1 个成功回答的场景 |
| Stage 2 评审完成 | HUD 切换为排名+分数模式 | 观察 HUD |
| Stage 3 完成 | 显示 Consensus Overlay | 观察 Overlay |
| 点击 Overlay | 跳转到 Consensus Tab，Overlay 消失 | 点击测试 |
| 查看历史对话 | 静态渲染完整结果，无动画 | 点击侧边栏历史项 |
| 侧边栏详情 Stage 1 | 显示当前议员 Thinking | 切换 Tab 观察 |
| 侧边栏详情 Stage 2 | 显示对当前议员的评价 | 切换 Tab 观察 |
| 不健康议员 | 灰显，不可选择 | 模拟后端返回 healthy=false |

### 10.2 兼容性测试

| 环境 | 验证项 |
|------|--------|
| Chrome (Desktop) | 布局、动画、SSE 流 |
| Firefox (Desktop) | 布局、动画、SSE 流 |
| Safari (MacOS) | 布局、动画、SSE 流 |
| Chrome (Android) | 移动端布局、底部抽屉 |
| Safari (iOS) | 移动端布局、底部抽屉 |

### 10.3 后端测试

| 测试场景 | 验证方法 |
|----------|----------|
| per_candidate_comments 字段 | 检查 stage2_item 事件是否包含该字段 |
| 评价内容正确拆分 | 检查每个 anon_X 是否有独立评价 |
| 向后兼容 | 确保旧版前端不报错 (字段可选) |

---

## 附录 A: 术语表

| 术语 | 定义 |
|------|------|
| Councilor | 议员，参与讨论的 AI 角色 |
| Chairman | 主席，负责综合最终答案 |
| Stage 1 | 并行生成阶段，各议员独立回答 |
| Stage 2 | 互评阶段，议员互相评审排名 |
| Stage 3 | 综合阶段，主席生成最终答案 |
| Judge Card | Stage 1 回答的结构化摘要 (stance + core_reasons) |
| Aggregate Rankings | 汇总排名，根据所有 Judge 的评分计算 |
| HUD | Heads-Up Display，底部状态栏 |
| anon_X | 匿名 ID，用于 Stage 2 评审 |
| per_candidate_comments | 每个候选人的独立评价 |

## 附录 B: 参考文件

| 文件路径 | 说明 |
|----------|------|
| `frontend_refactor/index.tsx` | 新 UI 主入口 |
| `frontend_refactor/types.ts` | 新 UI 类型定义 |
| `frontend_refactor/mockData.ts` | Mock 数据结构参考 |
| `frontend_refactor/hooks/useParliamentEngine.ts` | 新 UI 状态机 (Mock 版) |
| `frontend_refactor/docs/architect.md` | 新 UI 架构文档 |
| `frontend/src/api.js` | 真实 API 调用逻辑 |
| `frontend/src/App.jsx` | 旧项目主入口 |
| `backend/council.py` | 后端三阶段逻辑 |
| `backend/config.py` | 议员配置 |

---

> 📄 文档结束
> 
> 如有疑问，请联系项目负责人
