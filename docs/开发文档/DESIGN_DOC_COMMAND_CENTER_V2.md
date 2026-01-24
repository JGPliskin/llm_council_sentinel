# DESIGN_DOC_COMMAND_CENTER_V3.2 - Command Center Dock 统一布局规范

**版本**: 3.2 (Unified Dock Delivery)
**日期**: 2026-01-24
**优先级**: High
**涉及端**: Mobile (H5/App), Desktop (Web), Backend
**范围**: Welcome Screen + Dock (HUD) 统一布局与交互

---

## 目录
1. 背景与目标
2. 用户场景与痛点
3. 需求清单
4. 核心设计决策
5. 统一 Dock 布局规范
6. 交互逻辑与状态切换
7. 组件与数据结构
8. 技术方案（实现步骤）
9. 影响文件与关键修改点
10. 验收与风险
11. 开发任务清单（按工单拆分）
12. 关键交互细节与实现参数
13. 交付物与沟通节奏
14. 附录：状态切换流程图

---

## 1. 背景与目标

### 1.1 背景
当前 Welcome 页面与后续 Stage 使用了两个底部容器：
- Welcome: `InfoPanel + CommandInput` 在 Welcome 内部
- Stage: `TacticalHUD` 固定底部

这导致 **同一信息（Squad Row / 底部卡片）跨阶段换容器**，形成割裂感。

### 1.2 目标
- **统一 Dock（全阶段共享同一容器）**，消除割裂感
- 保留 HUD 的进度风格（底部卡片/小卡）
- 保留左侧/右侧面板展开与状态显示
- 移动端键盘弹起时保持输入区可见
- Web 端保持“操作区打包”的视觉逻辑

---

## 2. 用户场景与痛点

### 2.1 用户场景
| 场景 | 用户行为 | 期望表现 |
|---|---|---|
| Welcome / 移动端 | 选择议员、输入指令 | 输入区不被遮挡，操作集中在底部 Dock |
| Welcome / Web | 选择议员、观察介绍、输入指令 | 输入区与底部卡片形成整体，不割裂 |
| Stage 1/2/3 | 查看进度与状态 | 底部 Dock 仍在且一致，无跳变 |

### 2.2 痛点
- 移动端：输入框像孤岛，上下割裂
- Web 端：输入框和底部卡片分离，视觉逻辑被打断
- Squad Row 在 Welcome 与 Stage 位置不一致，割裂感明显

---

## 3. 需求清单

### 3.1 功能需求
1. Dock 统一容器：**Welcome 与 Stage 均使用同一 Dock**
2. Squad Row 保持 HUD progress 风格
3. Quick Actions 与 Input 保持连续
4. 输入框固定底部，移动端键盘弹起时可见
5. 保留左侧/右侧面板开关与 Stage 状态提示
6. Welcome 可展示 InfoPanel（议员简介）

### 3.2 交互需求
1. Welcome: Dock 全量显示（Status + Info + Squad + Quick Actions + Input）
2. Mobile 输入焦点时：隐藏 Info，保留 Quick Actions + Squad + Input
3. Stage: 隐藏 Info/Quick Actions/Input，仅保留 Status + Squad

### 3.3 非目标
- 不修改后端 API 协议（`description` 已存在）
- 不改变 Stage 内容区逻辑，仅调整底部 Dock 与间距

### 3.4 术语明确（给开发直指代码）
**Squad Row = 当前 HUD 底部卡片行（截图所示）**  
- 现状位置：`frontend/src/components/TacticalHUD.jsx` 的底部区域  
- 现状样式：`frontend/src/components/TacticalHUD.css` 内 `.agent-slice` / `.agent-slot--ready`  
- 现状数据（idle）：`selectedAgentIds + allCouncilors`（由 `App.jsx` 传入 `TacticalHUD`）  
- 现状数据（stage）：`resolvedCouncilors + agentProgress`（由 `useParliamentEngine` 驱动）  
- 视觉关键字：`READY` 状态、头像背景、带边框的卡片（HUD progress 风格）  

---

## 4. 核心设计决策

### 4.1 统一 Dock
- **Dock 为全局唯一底部容器**
- Welcome/Stage 只切换 Dock 内部行的显示与否
- Squad Row 不跨容器迁移

### 4.2 Dock 内部顺序（最终确认）
**自上而下**：
1. Status / Panel toggles / Stage info
2. Info Panel
3. Squad Row (HUD progress style)
4. Quick Actions
5. Input (bottom anchored)

Quick Actions 与 Input 相邻，保持“命令区”连续性。

---

## 5. 统一 Dock 布局规范

### 5.1 Mobile 布局
```
+--------------------------------------+
| Header                               |
|                                      |
| [Carousel Area - scroll snap]        |
|                                      |
+======================================+
| Dock 固定底部 (同一容器)              |
| Status / Panel toggles / Stage info  |
| Info Panel                            |
| Squad Row (HUD progress style)        |
| Quick Actions                         |
| Input Bar (bottom anchored)           |
+--------------------------------------+
```

- Dock: `position: fixed; bottom: 0; left: 0; right: 0`
- Dock 使用半透明背景 + blur + 顶部边框
- `padding-bottom: env(safe-area-inset-bottom)` 适配 iPhone

### 5.2 Web 布局
```
+-----------------------------------------------------------------------+
| Header                                                                |
|                                                                       |
| [Hangar Area / Grid]                                                  |
| [Info text below focused card]                                        |
|                                                                       |
| +===================================================================+ |
| | Dock / Command Deck (统一容器)                                     | |
| | Status / Panel toggles / Stage info                                | |
| | Info Panel                                                         | |
| | Squad Row (HUD progress style)                                     | |
| | Quick Actions                                                      | |
| | Input Bar                                                          | |
| +===================================================================+ |
+-----------------------------------------------------------------------+
```

- Web 端 Dock 使用带边框容器（类似 HUD 面板）
- 输入区与底部卡片在同一视觉块中

---

## 6. 交互逻辑与状态切换

### 6.1 状态表
| 状态 | Info | Squad Row | Quick Actions | Input |
|---|---|---|---|---|
| Welcome | 显示 | 显示 | 显示 | 显示 |
| Mobile 输入焦点 | 隐藏 | 显示 | 显示 | 显示 |
| Stage 1/2/3 | 隐藏 | 显示 | 隐藏 | 隐藏 |

### 6.2 键盘交互（移动端）
流程：
```
Input Focus → 隐藏 Info → Dock 高度减少 → 输入始终可见
Input Blur  → 恢复 Info
```

### 6.3 Stage 切换
流程：
```
Welcome → Stage1
  Dock 内部行变更：隐藏 Info/QuickActions/Input
  Dock 容器不变，Squad Row 保持位置
```

---

## 7. 组件与数据结构

### 7.1 组件拆分建议
| 组件 | 作用 | 数据来源 |
|---|---|---|
| `CommandDock` (或扩展 `TacticalHUD`) | 统一底部容器 | 全局 stage 状态 |
| `DockStatusRow` | 左/右面板开关 + Stage 状态 | `App.jsx` + `engine.stage` |
| `InfoPanel` | 议员简介 | `focusedId` / `selectedIds` |
| `SquadRow` | HUD progress 风格小卡片 | Welcome: `selectedAgentIds` / Stage: `resolvedCouncilors + agentProgress` |
| `QuickActionRow` | Chips 快捷指令 | 固定文案 |
| `InputBar` | 输入框与 Engage | `inputValue` |

### 7.2 Squad Row 现状位置与代码标记
> 用于让开发者精准定位 “截图中底部卡片行” 的实现位置。\n
| 项目 | 代码位置 | 说明 |
|---|---|---|
| 渲染函数 | `frontend/src/components/TacticalHUD.jsx` | `renderAgentSlice()` 渲染单张卡片 |
| 列表容器 | `frontend/src/components/TacticalHUD.jsx` | `<div className="flex gap-4 ...">` 渲染整行卡片 |
| 样式文件 | `frontend/src/components/TacticalHUD.css` | `.agent-slice` / `.agent-slot--ready` / `.agent-avatar-bg` |
| Idle 数据入口 | `frontend/src/App.jsx` | `selectedAgentIds` / `allCouncilors` 传入 `TacticalHUD` |
| Stage 数据入口 | `frontend/src/App.jsx` | `resolvedCouncilors` / `agentProgress` 传入 `TacticalHUD` |

### 7.2 组件架构图（建议结构）
```
App.jsx
  ├─ WelcomeScreen (Hangar / Carousel / Focus)
  │    └─ onFocusChange / onActiveInfoChange
  ├─ StageContentArea
  └─ CommandDock (固定底部)
       ├─ DockStatusRow (Stage + Panel toggles)
       ├─ InfoPanel (Welcome only)
       ├─ SquadRow (HUD progress style)
       ├─ QuickActionRow (Welcome only)
       └─ InputBar (Welcome only)
```

### 7.3 数据流简图
```
[WelcomeScreen]
  - focusedId / inputValue
  - selectedAgentIds
      |
      v
[Dock]
  - StatusRow (stage + toggles)
  - InfoPanel (focusedId)
  - SquadRow (selectedAgentIds / agentProgress)
  - QuickActionRow
  - InputBar
```

---

## 8. 技术方案（实现步骤）

1. **拆分 QuickActionRow**
   - 从 `CommandInput` 中拆出 Quick Actions
   - 使 Input 和 Quick Actions 可分别控制显示

2. **统一 Dock 容器**
   - 扩展 `TacticalHUD` 作为 `CommandDock`
   - 增加 `dockMode: idle | stage` 控制行显示

3. **Welcome 使用 Dock**
   - 将 `InfoPanel + QuickActions + Input` 移入 Dock
   - Welcome 内只保留 Hangar 展示区

4. **Stage 使用 Dock**
   - Dock 仅显示 Status + Squad Row
   - Squad Row 继续使用 HUD progress style

5. **布局对齐**
   - StageContentArea 底部 padding 根据 Dock 高度调整
   - Dock 高度变化时避免遮挡

---

## 9. 影响文件与关键修改点

> 仅列关键文件和修改点，具体实现由开发完成。

### 前端
| 文件 | 修改点 | 关键说明 |
|---|---|---|
| `frontend/src/components/WelcomeScreen.jsx` | 移除原底部控制区，改为使用统一 Dock | Welcome 不再自带输入区容器 |
| `frontend/src/components/TacticalHUD.jsx` | 扩展为统一 Dock（增加 idle 渲染行） | 保留左/右面板控制与 Stage 状态 |
| `frontend/src/components/TacticalHUD.css` | Dock 样式与间距调整 | 固定底部、blur、safe-area |
| `frontend/src/components/welcome/CommandInput.jsx` | 拆分 Input 与 QuickActions | QuickActions 提供独立组件 |
| `frontend/src/components/welcome/InfoPanel.jsx` | 位置调整 | 作为 Dock 子组件 |
| `frontend/src/App.jsx` | 传递 Dock 相关 props | stage/selectedIds/agentProgress |
| `frontend/src/components/StageContentArea.jsx` | 底部 padding 与 Dock 高度协调 | 避免遮挡 |

### 关键代码修改（开发对照）
| 目标 | 关键改动建议 | 备注 |
|---|---|---|
| Dock 显示规则 | `const isIdle = stage === 'idle'`，`const showInfo = isIdle && !(isMobile && isInputFocused)` | 只在 Welcome 显示 Info |
| Quick Actions + Input | 拆分 `QuickActionRow` 与 `InputBar`，并保持相邻 | 保持命令区连续性 |
| Squad Row 数据源 | Idle: `selectedAgentIds`；Stage: `resolvedCouncilors + agentProgress` | **Squad Row = TacticalHUD 底部卡片行** |
| Dock 高度占位 | Dock 通过 `ResizeObserver` 写入 `--dock-height` | StageContentArea `padding-bottom: var(--dock-height)` |
| Focus 状态 | Input 的 `onFocus/onBlur` 仅在 mobile 时改变 `isInputFocused` | 避免桌面端 UI 抖动 |

### 后端
| 文件 | 修改点 | 关键说明 |
|---|---|---|
| `backend/config.py` | `description` 字段（已存在） | InfoPanel 依赖此字段 |

---

## 10. 验收与风险

### 10.1 验收清单
- Welcome / Mobile：输入框始终可见
- Welcome / Web：输入区与 Squad Row 在同一容器
- Stage 1/2/3：Dock 保持一致，Squad Row 不迁移
- 左侧/右侧面板按钮与状态行功能保留

### 10.2 风险与规避
| 风险 | 影响 | 规避方案 |
|---|---|---|
| Dock 高度变化导致遮挡 | Stage 内容被遮住 | StageContentArea 使用 Dock 高度变量控制 padding |
| 小屏键盘占据空间 | Dock 过高 | 输入焦点时隐藏 Info Panel |

---

## 11. 开发任务清单（按工单拆分）

| 任务 | 优先级 | 涉及文件 | 说明 | 验收要点 |
|---|---|---|---|---|
| 拆分 QuickActionRow | P0 | `frontend/src/components/welcome/CommandInput.jsx` | 抽出独立组件 | Chips 功能保持不变 |
| 构建 CommandDock | P0 | `frontend/src/components/TacticalHUD.jsx` | 新增 idle 行渲染 | Dock 全阶段一致 |
| Welcome 结构改造 | P0 | `frontend/src/components/WelcomeScreen.jsx` | 移除底部控制区 | Dock 替代原输入区 |
| Stage 与 Dock 对齐 | P0 | `frontend/src/components/StageContentArea.jsx` | padding 适配 Dock 高度 | Stage 内容不遮挡 |
| Mobile focus 逻辑 | P1 | `InputBar` 组件 | focus 时隐藏 Info | 键盘弹出不遮挡输入 |
| Squad Row 数据映射 | P1 | `TacticalHUD.jsx` | idle/stage 数据切换 | 进度风格一致 |
| CSS 统一 | P1 | `TacticalHUD.css` | Dock 背景 + safe-area | iPhone safe area 正确 |
| 回归验证 | P1 | 手工测试 | Mobile / Web / Stage | 无割裂无遮挡 |

---

## 12. 关键交互细节与实现参数

### 12.1 断点与设备判定
- Mobile 判定：`< 768px`（Tailwind `md`）
- Web 判定：`>= 768px`

### 12.2 Dock 行显示逻辑（伪代码）
```
isIdle = stage === 'idle'
isMobile = window.innerWidth < 768

showInfo = isIdle && !(isMobile && isInputFocused)
showQuick = isIdle
showInput = isIdle
showSquad = true
```

### 12.3 Squad Row 展示风格
- **必须保持 HUD progress style**（沿用 `agent-slice` 视觉样式）
- Idle：显示 `selectedAgentIds` 的 READY 状态
- Stage：显示 `agentProgress` 的进度/完成状态
- 说明：Squad Row 即 **截图中底部卡片行**，对应 `TacticalHUD.jsx` 内的 agent-slice 列表

### 12.4 Quick Actions 行为
- 点击 Quick Action：应先写入 Input，再触发 Engage（保持现有行为）
- Stage 不显示 Quick Actions

### 12.5 Dock 高度与内容区间距
- Dock 通过 `ResizeObserver` 写入 `--dock-height`
- StageContentArea 使用 `padding-bottom: var(--dock-height)`
- 目标：Dock 高度变化时内容不会被覆盖

---

## 13. 交付物与沟通节奏

### 13.1 交付物
- 统一 Dock 的前端实现（UI 与交互）
- Welcome/Stage 兼容的底部状态栏
- 更新后的布局与交互文档（本文件）

### 13.2 沟通节奏
- 设计确认后直接进入开发
- 每完成 1 个 P0 任务即进行 UI 对照验收
- 最终整体验收覆盖 Mobile + Web + Stage

---

## 14. 附录：状态切换流程图
```
Welcome (idle)
  Dock: Status + Info + Squad + Quick + Input
    |
    | Input focus (mobile)
    v
Idle Focus
  Dock: Status + Squad + Quick + Input
    |
    | Start Session
    v
Stage 1/2/3
  Dock: Status + Squad
```
