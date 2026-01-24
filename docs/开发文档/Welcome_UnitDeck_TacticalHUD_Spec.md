# Welcome + TacticalHUD/UnitDeck 复刻规格说明

> 目标：将 Welcome 页与全局 TacticalHUD 底部卡片面板重构为 demo 的 UnitDeck 样式，并在 Web 与移动端保持一致的交互逻辑与动画效果。
> 注意：本文件仅为实现规格说明，不修改代码。

## 目录
0. 适用范围与术语
1. 用户场景与需求描述
2. 设计约束与共识
3. 交互与信息流（流程图）
4. UI 布局规格（Web / Mobile）
5. UnitDeck/TacticalHUD 面板规格
6. InfoPanel 与立绘交互规则
7. 动画与动效规格（demo 复刻）
8. 资源与数据映射
9. 技术方案（组件级）
10. 代码改动清单（文件与关键点）
11. 验证清单
12. 外部输入与素材清单
13. 交互事件矩阵与状态表
14. 像素级 UI 规范（Web / Mobile）

---

## 0. 适用范围与术语

### 0.1 适用范围
- 仅涉及前端 UI 与交互表现（`frontend/`）。不调整后端逻辑。
- 仅重构 Welcome 与全局底部面板（TacticalHUD → UnitDeck）。
- 侧边栏保持现有样式与行为不变。

### 0.2 术语定义
- **UnitDeck**：demo 中底部议员卡片条样式与交互（`demo/neural-council-os/components/UnitDeck.tsx`）。
- **UnitDeckList**：建议新增的“纯展示列表组件”，只负责渲染卡片样式，不承载业务逻辑。
- **UnitDeckCard**：建议新增的“单卡片组件”，封装卡片的视觉与状态样式。
- **Bottom Panel Container**：由 Status Bar（TacticalHUD 上栏）+ UnitDeck 组成的同一块底部面板容器；代码层可继续使用 `TacticalHUD.jsx` 文件名。
- **立绘舞台**：Welcome 画面中央展示选中议员立绘的区域。
- **InfoPanel**：显示当前聚焦/选中议员的介绍信息区域。

---

## 1. 用户场景与需求描述

### 1.1 主要用户场景
- 用户在 Welcome 页选择议员（Councilors）并输入指令启动对话。
- 进入 Stage1/2/3 后，底部面板持续展示议员状态、进度、排名等信息。

### 1.2 核心需求（已确认）
| 需求 | 说明 |
| --- | --- |
| UnitDeck 复刻 demo 样式 | 底部卡片布局与动画需与 demo 一致 |
| Status Bar 放在 UnitDeck 上方 | 与 UnitDeck 组成一个整体面板 |
| 进度条横向填充 | 取代当前纵向填充 |
| UnitDeck 全局形态统一 | Bottom Panel Container 与卡片样式统一；Welcome/Stage 逻辑分层 |
| Web 立绘为多人并列 | 与 demo 行为一致 |
| InfoPanel 响应 hover | UnitDeck hover 与立绘 hover 均触发 |
| 立绘点击行为 | 点击立绘=聚焦/锁定 InfoPanel；取消通过显式按钮 |
| 移动端保留 UnitDeck 面板 | 视觉与逻辑一致，仅做尺寸与排版适配 |
| 移动端 UnitDeck 保留小头像 | M-A 方案（推荐） |
| 移动端允许取消最后一个选中 | 输入框变灰提示不可用 |
| Stage1/2/3 隐藏未参与议员 | 仅展示 resolved councilors |

---

## 2. 设计约束与共识

### 2.1 HUD 风格约束（来自 UI_STYLE_GUIDE）
- 主色仅使用 cyan（`--hud-cyan`）。
- 不引入新的紫色/多色主题。
- 背景纹理层保持启用（grid、scanline、vignette）。

### 2.2 行为约束
- 不改动后端逻辑。
- 仅重构前端 UI 表现。

### 2.3 非目标（Non-goals）
- 不改变 Sidebar 结构与视觉。
- 不新增新配色（保持 HUD cyan）。
- 不更改 API 协议与数据结构。

---

## 3. 交互与信息流（流程图）

### 3.1 Welcome 选择流
```
[UnitDeck hover] ---> set focusedId
[立绘 hover] ------> set focusedId

[UnitDeck click] ---> toggle selectedIds
[立绘 click] -----> focus lock (InfoPanel 固定展示该议员)
[InfoPanel button] -> LINK/UNLINK 切换选中

InfoPanel 选择优先级：
  hover(focusedId) > lastSelected > firstSelected > fallback
```

### 3.1.1 InfoPanel 决策伪代码
```
if (focusedId) return focusedId
if (lastSelected) return lastSelected
if (firstSelected) return firstSelected
return fallback (first councilor or chairman)
```

### 3.2 Stage 状态与 UnitDeck
```
Stage1/Stage2: progress 按 agentProgress -> 横向填充
Stage3: aggregateRankings -> 显示排名/标签
activeTab: 点击卡片切换
```

### 3.3 移动端显示策略（Welcome vs Stage）
```
Welcome: 显示全部议员卡（未选中 = STANDBY，无填充）
Stage1/2/3: 仅显示已参与议员（resolved councilors）
```

---

## 4. UI 布局规格（Web / Mobile）

### 4.0 断点约定
- `md = 768px`（与现有 React/Tailwind 断点保持一致）。
- `sm = 480px`（用于极小屏的紧凑策略）。

### 4.1 Web 布局（ASCII 原型）
```
+-------------------+------------------------------------------------------+
| Sidebar (原样)    |                                                      |
|                   | 立绘舞台（多人并列）                                 |
|                   | [Art][Art][Art]                                      |
|                   | InfoPanel                                            |
|                   | CommandInput + Presets                               |
|                   +------------------------------------------------------+
|                   | Bottom Panel Container                               |
|                   | [Status Bar (TacticalHUD 上栏)]                      |
|                   | [UnitDeck 卡片（demo 样式 + 动画 + 进度横填）]         |
+-------------------+------------------------------------------------------+
```

### 4.2 Mobile 布局（ASCII 原型）
```
[立绘舞台（可横滑/单列）]
[InfoPanel（紧凑）]
[CommandInput]
[Bottom Panel Container]
  [Status Bar (TacticalHUD 上栏)]
  [UnitDeck（横滑卡片，小头像）]
```

### 4.3 布局与层级规则
- Bottom Panel Container 固定在主内容底部（与当前 TacticalHUD 位置一致）。
- Status Bar 与 UnitDeck 视觉上连为一体，中间无分割背景断层。
- 立绘舞台、InfoPanel、CommandInput 在 Bottom Panel Container 之上，保持纵向布局。
- 背景纹理层（Background）仍位于最底层。

### 4.5 三层结构（容器/上栏/列表）
```
BottomPanelContainer (= TacticalHUD.jsx 组件职责)
  ├─ StatusBar（控制按钮 + Stage 指示）
  └─ UnitDeckList（卡片列表）
       └─ UnitDeckCard × N
```

### 4.4 自适配策略（必须遵守）
- **高度优先级**：Bottom Panel Container > CommandInput > InfoPanel > 立绘舞台。
- **高度不足时的缩放顺序**：
  1) 压缩立绘舞台高度（最低降到 `20vh`）。
  2) InfoPanel 描述文字 clamp 为 2 行（mobile）。
  3) CommandInput 保持可用，禁止被遮挡或移出可视区。
- **极小屏（<480px）**：
  - UnitDeck 单卡宽度 `clamp(220px, 80vw, 260px)`。
  - InfoPanel 标题缩到 `16px`，描述 `11px`，行高 `1.3`。
  - Status Bar 字号降为 `9px`。
- **横屏（landscape）**：
  - 立绘舞台固定为 `min(180px, 30vh)`。
  - InfoPanel 仅显示标题 + 1 行描述。
- **移动端软键盘打开**：
  - 立绘舞台降到 `20vh`。
  - InfoPanel 描述 clamp 为 1-2 行。
  - CommandInput 保持在 Bottom Panel Container 之上并完全可见。

---

## 5. UnitDeck/TacticalHUD 面板规格

### 5.1 面板结构
- UnitDeck 作为 TacticalHUD 的卡片区域替代方案。
- Status Bar 保留 TacticalHUD 现有上栏，放在 UnitDeck 之上。
- 二者包裹在同一容器中，形成统一底部面板（Bottom Panel Container）。
 - TacticalHUD 组件实际承担 BottomPanelContainer 职责（文件名可不改）。

### 5.2 卡片布局与密度（复刻 demo）
参考 `demo/neural-council-os/components/UnitDeck.tsx` 的布局与间距：
- **Web**：三列栅格（`md:grid md:grid-cols-3`），gap 为 `gap-4`，卡片高度由内容决定。
- **Mobile**：横向滚动（`flex overflow-x-auto snap-x snap-mandatory`），单卡宽度 `w-[280px]`。
- **卡片内边距**：Web `p-3`，Mobile `p-2`。
- **头像**：Web `w-12 h-12`，Mobile `w-10 h-10`，左侧固定。
- **文本**：
  - 名字：`text-base md:text-lg`，全大写，强对比。
  - 角色：`text-[9px] md:text-[10px]`，弱对比。
  - 状态标签：`LINKED / STANDBY`，右侧 badge。
- **移动端密度规则**：保留小头像（约 20-24px），角色行可隐藏或缩短；Welcome 阶段显示全部卡，Stage1/2/3 隐藏未参与议员。
- **极小屏宽度**：单卡宽度改为 `clamp(220px, 80vw, 260px)`，避免横向溢出。

### 5.3 视觉状态（复刻 demo）
- 选中：卡片背景高亮、边框亮、轻微上浮、扫光动画、LINKED 呼吸。
- 未选中：低对比背景、透明度降低、无填充。
- Hover：边框轻微增强，名字/角色提亮。
- activeTab：增加细描边或微弱高亮（保持 HUD cyan）。

### 5.4 进度条规范
- 从左到右填充（替代纵向填充）。
- 颜色基于 HUD cyan（或 `getCouncilorUIConfig`，目前均为 cyan）。
- Stage1/Stage2 使用 progress 填充，Stage3 不显示填充。
- 未选中状态（Welcome）不显示填充，仅显示 STANDBY。
- 进度填充应置于卡片底层（低透明度），不得遮挡文字。

### 5.5 Stage 行为细则
- **Welcome**：显示全部议员卡；未选中为 STANDBY。
- **Stage1/2/3**：仅显示参与议员（resolved councilors）。
- **Stage2 被跳过**：卡片右上角显示 `SKIPPED`（沿用现有逻辑）。
- **Stage3**：显示排名 badge（`#1/#2` 或均值 rank）。

### 5.6 Status Bar 规格（沿用 TacticalHUD 上栏）
- 位置：Bottom Panel Container 内顶部。
- 高度：Web 40px，Mobile 36px（建议）。
- 内边距：`px-6 py-2`（Web），`px-4 py-1.5`（Mobile）。
- 字体：`text-[10px]`、`font-mono`、`tracking-[0.2em]`。
- 按钮区（左侧）：Sidebar 开关 / DetailPanel 开关 / Reset（保持现有图标尺寸 14px）。
- 状态区（中间）：Stage 指示 + 文案（保持现有状态文案）。
- 右侧资源信息（CPU/MEM）：Web 显示，Mobile 隐藏。
 - Welcome 阶段也显示 Status Bar（与 Stage 保持一致的底部面板结构）。

### 5.7 Bottom Panel Container 规格
- 宽度：100%。
- 位置：主内容底部固定（与当前 TacticalHUD 位置一致）。
- 背景：`var(--hud-bg-soft)`；顶部边框 `1px solid var(--hud-cyan-soft)`。
- 内部分层：Status Bar 在上，UnitDeck 在下。
- 移动端安全区：底部增加 `padding-bottom: env(safe-area-inset-bottom)`。
- 移动端高度建议：`min-height: 140px`（含 Status Bar + UnitDeck）。

---

## 6. InfoPanel 与立绘交互规则

### 6.1 InfoPanel 触发源
- UnitDeck hover -> 显示该议员信息
- 立绘 hover -> 显示该议员信息

### 6.2 优先级规则
```
hover(focusedId) > lastSelected > firstSelected > fallback
```

### 6.3 立绘点击行为
- Web/Mobile：点击立绘 = 聚焦/锁定 InfoPanel（不触发取消）
- 取消选中统一通过 InfoPanel 按钮完成

### 6.4 取消按钮（Web/Mobile）
- 位置：InfoPanel 右侧（对当前 focused/lastSelected 生效）。
- 行为：已选中显示 `UNLINK`，未选中显示 `LINK`。
- 允许取消最后一个选中，输入框置灰提示。

---

## 7. 动画与动效规格（demo 复刻）

### 7.1 UnitDeck 卡片动画
| 动效 | 说明 |
| --- | --- |
| LINKED 呼吸 | 选中标签轻微呼吸（opacity / glow） |
| 卡片上浮 | 选中卡片略微上移 |
| Shimmer 扫光 | 选中卡片表面渐变扫过 |
| 连接线 | 选中卡片顶部竖线 |

### 7.2 立绘舞台动画
| 动效 | 说明 |
| --- | --- |
| 多立绘入场 | 依次淡入（demo hologramFadeIn） |
| 扫描线 | 立绘容器内 scanline 运动 |

### 7.3 动效时长建议（对齐 demo）
- 卡片 hover/选中过渡：`300ms`。
- LINKED 呼吸：`2s` 循环。
- 扫光（shimmer）：`2.5s` 循环，横向移动。
- 立绘入场：`0.5s`，每张延迟 `0.1s` 叠加。

### 7.4 降动效规则
- 遵守 `prefers-reduced-motion`：关闭 scanline 与 shimmer 动画。

---

## 8. 资源与数据映射

### 8.0 demo 参考路径（项目内）
- demo 根目录：`demo/neural-council-os/`（位于项目根目录 `E:\project\llm_council_sentinel` 下）
- `demo/neural-council-os/App.tsx`（整体布局与面板结构）
- `demo/neural-council-os/components/UnitDeck.tsx`（卡片结构与动画）
- `demo/neural-council-os/components/ChatInterface.tsx`（立绘舞台与扫描线效果）
- `demo/neural-council-os/components/UnitInfoPanel.tsx`（InfoPanel 视觉参考）
- `demo/neural-council-os/components/CommandInput.tsx`（输入区风格参考）
- `demo/neural-council-os/constants.ts`（demo 临时人物图与文案）
- `demo/neural-council-os/index.html`（基础样式与 scanline）

### 8.1 demo 临时资源（来源）
来自 `demo/neural-council-os/constants.ts`：
- Kant avatar/standing
  - https://images.unsplash.com/photo-1506794778202-cad84cf45f1d
- Trump avatar/standing
  - https://images.unsplash.com/photo-1560250097-0b93528c311a
- Kojima avatar/standing
  - https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d

### 8.2 前端本地资源方案
- 将 3 张 demo 图片下载并替换到：`frontend/public/avatars/`
- 若区分 avatar 与 standing：
  - 建议建立 `frontend/public/avatars/standing/` 子目录
  - 命名示例：`kant_standing.png`, `trump_standing.png`, `kojima_standing.png`

### 8.3 数据映射建议
- 在 `frontend/src/config/councilors.js` 增加前端映射字段：
  - `avatar`（现有）
  - `standing`（新增，仅前端用）

### 8.4 状态数据来源
- `TacticalHUD` 现有 props：
  - `agentProgress`（Stage1/2 进度）
  - `aggregateRankings`（Stage3 排名）
  - `resolvedCouncilors`（参与议员）
  - `activeTab` 与 `onTabSelect`（点击切换）
- `WelcomeScreen` 现有 props：
  - `selectedIds`（选中议员）
  - `onToggleId`（切换选中）

---

## 9. 技术方案（组件级）

### 9.1 Welcome 结构重组
- `WelcomeScreen.jsx`
  - 移除大立绘卡作为选择入口
  - 加入立绘舞台区域（只展示选中议员）
  - InfoPanel + CommandInput 仍保留
  - UnitDeck 面板放置底部
  - 立绘点击仅负责“聚焦”，不直接取消选中

### 9.2 TacticalHUD 改造
- `TacticalHUD.jsx`
  - 保留 Status Bar 与控制按钮
  - 替换卡片列表为 UnitDeckList（纯展示组件）
  - progress 填充方向改为横向
  - activeTab 切换逻辑保持
  - 仅负责 stage 场景的 UnitDeck 渲染（与 Welcome 独立实例）
  - Welcome 阶段亦渲染 Status Bar（同样的 Bottom Panel Container 结构）

### 9.3 InfoPanel 行为调整
- `InfoPanel.jsx`
  - 监听 UnitDeck hover 与立绘 hover
  - 使用优先级规则避免抖动
  - 增加 LINK/UNLINK 按钮（Web/Mobile 通用）

### 9.4 移动端适配
- Status Bar 压缩为单行
- 立绘舞台高度受限
- UnitDeck 保持横滑

### 9.5 实施顺序建议
1) 重构 `TacticalHUD` 卡片结构为 UnitDeck 样式（先保证 stage 功能可用）。  
2) 重构 Welcome 立绘舞台与 UnitDeck 选择逻辑。  
3) 接入 demo 临时素材并校验动效。  
4) 补齐移动端交互与 InfoPanel 按钮。  
5) 加入空状态文案与引导样式（无选中时）。  

---

## 10. 代码改动清单（文件与关键点）

### 10.1 需要改动的文件
| 文件路径 | 修改点 |
| --- | --- |
| `frontend/src/components/TacticalHUD.jsx` | 结构重排，Status Bar + UnitDeck 同容器；卡片改为 demo 样式 |
| `frontend/src/components/TacticalHUD.css` | 新增 demo 动画（breathing, shimmer, hover, progress 横向填充） |
| `frontend/src/components/WelcomeScreen.jsx` | 布局重构：立绘舞台 + InfoPanel + Input + UnitDeck |
| `frontend/src/components/welcome/CouncilorCard.jsx` | 由“选择卡”改为“立绘显示组件” |
| `frontend/src/components/welcome/InfoPanel.jsx` | hover 优先级逻辑 |
| `frontend/src/components/welcome/CommandInput.jsx` | 视觉微调匹配 demo |
| `frontend/src/config/councilors.js` | 增加 standing/头像映射 |
| `frontend/public/avatars/*` | 替换为 demo 图 |
| `frontend/src/components/UnitDeckList.jsx` | （建议新增）纯展示列表组件，复用卡片样式 |
| `frontend/src/components/UnitDeckCard.jsx` | （建议新增）单卡片视觉组件 |

### 10.2 不应修改的文件
- `frontend/src/components/Sidebar.jsx`（保持原样）
- `frontend/src/components/ui/Background.jsx`（保持 HUD 背景层）

### 10.3 关键逻辑修改
- `progress`：纵向 -> 横向填充
- `hover`：UnitDeck 与立绘统一驱动 InfoPanel
- `click`：立绘点击仅“聚焦/锁定”，取消由按钮触发
- `mobile`：允许取消最后一个选中，输入置灰

---

## 11. 验证清单
- Web：Status Bar 与 UnitDeck 合并为统一面板
- Web：UnitDeck 动画与 demo 一致
- Web：立绘 hover / UnitDeck hover 都能驱动 InfoPanel
- Web：立绘点击聚焦 InfoPanel（非取消）
- Mobile：保留 UnitDeck + Status Bar
- Mobile：UnitDeck 保留小头像
- 所有 Stage：进度条横向填充
- Mobile：允许取消最后一个选中，输入置灰
- Stage1/2/3：只显示参与议员卡
- Mobile：软键盘弹出时 Input 可见且不被遮挡
- Mobile：横屏与极小屏布局无遮挡、无重叠
- Welcome：无选中时显示空状态提示
- Welcome：Status Bar 可见且与 Stage 一致

---

## 12. 外部输入与素材清单
- 立绘使用的最终素材（demo 图仅为临时占位）。
  - 需要提供：每位议员的 standing 立绘图（建议 3:5 比例，至少 600px 高）。
  - 需要提供：头像图（建议 200px 正方形）。

### 12.1 临时素材映射（demo 占位）
| Councilor ID | Avatar 文件 | Standing 文件 | demo 来源 |
| --- | --- | --- | --- |
| `immanuel_kant` | `frontend/public/avatars/kant.png` | `frontend/public/avatars/standing/kant_standing.png` | `photo-1506794778202-cad84cf45f1d` |
| `donald_trump` | `frontend/public/avatars/trump.png` | `frontend/public/avatars/standing/trump_standing.png` | `photo-1560250097-0b93528c311a` |
| `hideo_kojima` | `frontend/public/avatars/kojima.png` | `frontend/public/avatars/standing/kojima_standing.png` | `photo-1507003211169-0a1dd7228f2d` |
| `chairman` | 维持现有 `frontend/public/avatars/chairman.png` | 暂不提供 standing | — |

### 12.2 命名规则（正式素材）
- Avatar：`{councilor_id}.png`
- Standing：`{councilor_id}_standing.png`
- 若只提供一张图，可暂时同图复用（avatar 与 standing 指向同一文件）。

---

## 13. 交互事件矩阵与状态表

### 13.1 Web 交互矩阵
| 目标 | Hover | Click |
| --- | --- | --- |
| UnitDeck 卡片 | 更新 focusedId → InfoPanel 显示该议员 | toggle 选中；若在 stage 则切换 activeTab |
| 立绘 | 更新 focusedId → InfoPanel 显示该议员 | 聚焦锁定 InfoPanel |
| InfoPanel 右侧按钮 | — | LINK/UNLINK 切换 |
| CommandInput | focus 显示高亮 | Enter 触发 Engage |
| Status Bar 按钮 | — | Sidebar/Detail/Reset（沿用现有） |

### 13.2 Mobile 交互矩阵
| 目标 | Tap | Long Press |
| --- | --- | --- |
| UnitDeck 卡片 | toggle 选中；更新 InfoPanel | 无 |
| 立绘 | 更新 InfoPanel（聚焦锁定） | 无 |
| InfoPanel 右侧按钮 | LINK/UNLINK 切换 | 无 |
| CommandInput | focus + 软键盘 | 无 |
| Status Bar 按钮 | Sidebar/Detail/Reset | 无 |

### 13.3 状态表（Welcome）
| 状态 | UnitDeck 卡片 | InfoPanel | CommandInput | 立绘舞台 |
| --- | --- | --- | --- | --- |
| 无选中 | 全部 STANDBY，无填充 | 空态提示 | disabled（置灰） | 空态提示 |
| 有选中 | 选中 LINKED，未选中 STANDBY | 显示 focused/lastSelected | enabled | 显示选中立绘 |

### 13.4 状态表（Stage1/2/3）
| 状态 | UnitDeck 卡片 | InfoPanel | CommandInput | 立绘舞台 |
| --- | --- | --- | --- | --- |
| Stage1/2 | 参与议员显示进度横填 | 可 hover 查看 | 由现有逻辑控制 | 不涉及 |
| Stage3 | 显示排名 badge | 可 hover 查看 | 由现有逻辑控制 | 不涉及 |

---

## 14. 像素级 UI 规范（Web / Mobile）

> 说明：以下为目标范围值，允许在实现阶段按视觉与拥挤度微调（建议 ±2px~±4px）。

### 14.1 立绘舞台
- Web：舞台容器高度为主内容区的 `70%~85%`，立绘 aspect 比例 3:5。
- Mobile：`height: clamp(180px, 28vh, 280px)`，键盘弹起时降到 `20vh`。
- 立绘底部渐隐：mask 70% → 100% 渐隐。

### 14.2 InfoPanel
- 宽度：`max-w-4xl`（约 960px），左右内边距 Web 24px / Mobile 16px。
- 标题：Web 22–26px，Mobile 16–18px；字间距 `0.1em`。
- 描述：Web 14–16px，Mobile 11–12px；行高 1.3–1.5。
- 左侧指示点：8px 方形或圆点。
- 右侧按钮（移动端）：最小点击区 40x28px。
- Mobile 描述行数：默认 2 行，键盘弹起时 1 行。

### 14.3 CommandInput
- 输入高度：48px（Web/Mobile 一致）。
- 按钮高度：38–40px，左右内边距 14–16px。
- Placeholder：保持现有英文文案；禁用时置灰。
- Mobile：Input 与 Bottom Panel Container 之间至少保留 12px 间距。

### 14.4 UnitDeck 卡片
- Web：卡片最小高度 68–76px；左右间距 16–24px。
- Mobile：卡片高度 56–64px；单卡宽度 260–300px（默认 280px）；`snap-center`。
- 头像：Web 44–48px；Mobile 36–40px；左侧固定。
- LINKED/ STANDBY 标签：字号 9–10px；内边距 2–4px。
- Mobile 极小屏：单卡宽度 `clamp(220px, 80vw, 260px)`。

### 14.5 Status Bar
- Web 高度 38–42px，Mobile 高度 34–36px。
- 图标尺寸 14px；左右间距 10–12px。
- Stage 指示点 7–8px；文字 9–10px monospace。

### 14.6 Bottom Panel Container
- Top border：1px（`var(--hud-cyan-soft)`）。
- 背景：`var(--hud-bg-soft)`。
- 移动端底部安全区：`padding-bottom: env(safe-area-inset-bottom)`。

### 14.7 文本截断与溢出规则
- UnitDeck 名字：单行截断，避免换行挤压。
- 角色行：移动端可隐藏或缩短为 1 行。
- InfoPanel 描述：Web 不截断，Mobile 按行数限制。

### 14.8 视口单位规范
- 移动端使用 `100dvh` 处理地址栏变化，避免底部面板被遮挡。
- 立绘舞台高度使用 `vh` 与 `clamp` 组合，避免极端尺寸失衡。

### 14.9 空状态规范（Welcome）
- 触发：无选中议员（selectedIds 为空）。
- 立绘舞台显示空态文案：
  - 标题：`NO UNIT SELECTED`
  - 副文案：`Select a councilor to begin`
- InfoPanel 显示同样的空态或简化版本。
- CommandInput 置灰并提示不可用。

---

## 15. 组件 Props 接口定义（建议）

### 15.1 UnitDeckCard Props（建议）
| 名称 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `data` | `UnitDeckCardViewModel` | 是 | 视图模型 |
| `onClick` | `(id: string) => void` | 否 | 点击回调 |
| `onHover` | `(id: string | null) => void` | 否 | hover 回调 |

### 15.2 UnitDeckList Props（建议）
| 名称 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `items` | `UnitDeckCardViewModel[]` | 是 | 预计算后的卡片数据 |
| `onItemClick` | `(id: string) => void` | 否 | 点击卡片 |
| `onItemHover` | `(id: string | null) => void` | 否 | hover 卡片 |
| `showProgress` | `boolean` | 否 | 是否显示横向进度 |
| `showRank` | `boolean` | 否 | 是否显示排名 badge |

### 15.3 UnitDeckCardViewModel（建议）
| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `string` | councilor id |
| `name` | `string` | 显示名 |
| `role` | `string` | 角色 |
| `avatar` | `string` | 头像 |
| `state` | `'linked' | 'standby' | 'skipped'` | 状态 |
| `progress` | `number` | 进度（0-100） |
| `rank` | `number` | 排名 |
| `isActiveTab` | `boolean` | activeTab 标记 |

### 15.4 类型关系（建议）
```
// ViewModel 用于数据传递（由上层计算）
// Props = ViewModel + 事件回调
type UnitDeckCardProps = {
  data: UnitDeckCardViewModel;
  onClick?: (id: string) => void;
  onHover?: (id: string | null) => void;
};
```

---

## 16. Welcome 与 Stage 的 UnitDeck 实例说明

| 场景 | 渲染位置 | 数据来源 | 行为 |
| --- | --- | --- | --- |
| Welcome | `WelcomeScreen.jsx` 底部 | `allCouncilors` + `selectedIds` | 选择/取消选中 |
| Stage1/2/3 | `TacticalHUD.jsx` 内 | `resolvedCouncilors` + `agentProgress` + `aggregateRankings` | 进度/排名/Tab 切换 |

> 结论：**同组件，不同实例**。Welcome 与 Stage 分别渲染各自的 UnitDeckList，避免复杂条件耦合。

---

最后更新：2026-01-24
