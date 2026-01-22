# UI Demo Style Spec (As-Built) - Sentinel Consensus HUD

## 目录
- 1. 概述
- 2. 用户场景与需求描述
- 3. 设计与技术约束
- 4. 视觉系统与设计令牌
- 5. 背景纹理与动效策略
- 6. 交互与布局策略（桌面/移动）
- 7. 详细技术方案（按组件）
- 8. 技术架构图 / 流程图
- 9. 已修改文件与关键改动点
- 10. 非目标与排除项
- 11. 已知风险与验证清单

---

## 1. 概述
本规范文档以当前最新代码为准，记录将前端 UI 视觉完全对齐 `tests/sentinel-consensus-system` Demo 风格的实现细节。
目标是“视觉一致”，不改变逻辑、按钮、交互或动画行为。

明确排除：System Time 模块（不出现、不引入）。

---

## 2. 用户场景与需求描述
### 2.1 用户场景
1) 用户在 Welcome 页面选择议员与输入任务，进入 Stage 1/2/3 流程。
2) 用户在 Stage 1/2/3 期间浏览议员回答与思考过程，并查看右侧 Peer Reviews。
3) 用户通过底部 Tactical HUD 查看阶段与议员状态，完成共识阶段。

### 2.2 需求描述（最终确认）
- 视觉上像素级复刻 Demo 质感：霓虹青主色、深色 HUD 面板、全局网格背景、轻微发光边线。
- 保持所有原有逻辑、按钮、交互、动画不变（仅改样式）。
- System Time 模块不需要、不出现。
- 背景网格为全局固定背景（Welcome + Stage 1/2/3 全部有）。
- 右侧 Review 面板：
  - 移动端保持“上下抽屉”。
  - 桌面端改为“左右滑入/滑出”，与左侧列表一致。
- 页面颜色尽量统一为主色调（cyan）。紫色和过多颜色必须移除。
- 议员相关色彩也统一为主色调（仅保留极小提示点时允许）。
- 思考过程标题在移动端避免重叠：仅显示 `LOGIC_PROCESS`。
- 底部 HUD 卡片边框宽度一致（上下左右统一）。
- 顶部议员 Tab 边框宽度一致（上/左/右统一）。

---

## 3. 设计与技术约束
- 仅修改 `frontend/src/*` + 必要的样式/字体资源；不改业务逻辑。
- 非 UI 的 backend 修复仅限于已确认的 deepseek 调用报错修复。
- 保持原有交互：Tab 切换、抽屉开关、Stage 进度等行为不变。
- 禁止引入 System Time 组件。

---

## 4. 视觉系统与设计令牌
### 4.1 主色调
- 主色调：`--hud-cyan = #06b6d4`
- 背景：`--hud-bg = #050a14`
- 面板背景：`--hud-bg-soft = #0a0f1e`
- 文本：`--hud-text = #e0f2fe`
- 次级文本：`--hud-muted = #5b6b7a`

### 4.2 颜色统一策略
- 统一为 cyan；移除 purple/amber 等大面积主题色。
- 议员颜色统一为 cyan（避免画面色彩过多）。
- 仅保留必要的小提示点为非 cyan 的情况已删除。

### 4.3 字体
- Orbitron + Rajdhani 自托管（woff2）。
- 默认正文使用 Rajdhani；HUD 标题/标签使用 Orbitron。
- CJK fallback：系统字体（PingFang SC / Microsoft YaHei）。

字体资源落地：
- `frontend/src/assets/fonts/*.woff2`
- `frontend/src/index.css` 通过 `@import` 引入 `fonts.css`

---

## 5. 背景纹理与动效策略
### 5.1 背景层
背景始终存在于 App 根层（Welcome + Stage 1/2/3 统一）：
1) 透视网格（grid floor）
2) 平面网格（flat grid）
3) vignette
4) scanline + cyan sweep

实现位置：`frontend/src/components/ui/Background.jsx`

### 5.2 性能与降级
- `prefers-reduced-motion: reduce` 时禁用 scanline/sweep 动画。
- `will-change: transform` 提示 GPU 优化。

---

## 6. 交互与布局策略（桌面/移动）
### 6.1 右侧 Review 面板
- 移动端：保留上下抽屉。
- 桌面端：改为右侧横向滑入/滑出（与左侧列表一致）。

实现位置：`frontend/src/App.jsx`
- `md` 断点下切换 `translate-x-full` / `translate-x-0` 与 `width`。

---

## 7. 详细技术方案（按组件）

### 7.1 Sidebar（左侧任务列表）
文件：`frontend/src/components/Sidebar.jsx`
- Header 改为 Demo 风格：MISSION LOGS + DEFENSE AREA。
- Initiate Session：纯色半透明填充，移除条纹。
- 活动对话橙点：移到右上角偏上位置（更贴近右边）。
- 卡片统一 HUD 边框与暗色填充。

### 7.2 StageContentArea（中心内容区）
文件：`frontend/src/components/StageContentArea.jsx`
- 顶部 Tabs：边框宽度统一为 1px。
- Consensus Tab 颜色改为主色 cyan。
- Proposal 标题及分割线统一为主色 cyan。
- 思考过程标题：无论 stage 都仅显示 `LOGIC_PROCESS`。
- Final/Consensus 相关模块统一为 cyan（删除紫色）。
- 取消局部覆盖网格（保证全局 Background 可见）。
- 底部 padding 调整，移除额外留白。 

### 7.3 DetailPanel（右侧 Peer Reviews）
文件：`frontend/src/components/DetailPanel.jsx`
- 视觉改为 HUD 卡片风格：cyan 边框、暗背景。
- 评审卡片标题栏与文本颜色统一为 cyan 系列。
- 与主色调统一，减少多色视觉冲突。

### 7.4 TacticalHUD（底部状态条）
文件：`frontend/src/components/TacticalHUD.jsx`, `frontend/src/components/TacticalHUD.css`
- 卡片边框统一为 1px，上下左右一致。
- Stage 颜色不再使用紫色，统一为 cyan。
- Consensus overlay 改为 cyan（图 2 紫色部分替换）。
- 保留原有动画，不改变逻辑。

### 7.5 WelcomeScreen（初始页面）
文件：`frontend/src/components/WelcomeScreen.jsx`
- 全面改为 cyan HUD 风格；背景网格常驻。
- 选择议员按钮/输入框/预设卡片全部统一颜色体系。

### 7.6 背景组件
文件：`frontend/src/components/ui/Background.jsx`
- 增加平面 grid 层，确保背景可见。
- 维持透视 grid + vignette + scanline + sweep。

---

## 8. 技术架构图 / 流程图
```
[User Action]
    |
    v
[Existing Logic (unchanged)]
    |
    v
[Visual Layer Updates]
    |
    v
[HUD UI Rendered]

Desktop:
 Sidebar <-> StageContentArea <-> DetailPanel (right slide)

Mobile:
 Sidebar overlay + DetailPanel bottom sheet
```

---

## 9. 已修改文件与关键改动点

| 文件 | 关键改动 | 说明 |
|---|---|---|
| frontend/src/components/Sidebar.jsx | HUD Header、按钮纯色、活动点位置 | 左侧任务列表完全 HUD 化 |
| frontend/src/components/StageContentArea.jsx | Tabs 边框一致、Proposal 主色、LOGIC_PROCESS 简化 | 中心内容视觉统一 |
| frontend/src/components/DetailPanel.jsx | Peer Reviews 统一主色 | 右侧栏 HUD 化 |
| frontend/src/components/TacticalHUD.jsx | Consensus overlay 主色替换 | 底部 HUD 视觉统一 |
| frontend/src/components/TacticalHUD.css | 边框宽度统一 | 底部卡片一致 |
| frontend/src/components/ConsensusBeacon.css | Beacon 主色替换 | 紫色清除 |
| frontend/src/components/WelcomeScreen.jsx | Welcome 页面 HUD 风格 | 一致性 |
| frontend/src/components/ui/Background.jsx | 全局网格背景 | Stage 1-3 也显示 |
| frontend/src/config/councilors.js | 议员颜色统一 | 减少色彩 |
| frontend/src/index.css | HUD tokens + util classes | 统一样式系统 |
| frontend/tailwind.config.js | fontFamily 扩展 | Orbitron + Rajdhani |
| backend/openrouter.py | None 拼接保护 | 修复 deepseek 报错 |

---

## 10. 非目标与排除项
- 不引入 System Time。
- 不修改任何逻辑、按钮、动画触发机制。
- 不修改业务流程或数据流。

---

## 11. 已知风险与验证清单
### 11.1 风险
- 过度统一颜色可能降低阶段辨识度（已明确要求）。
- 大面积背景 grid 对可读性影响（可通过 opacity 调整）。

### 11.2 验证清单
- [ ] Welcome/Stage1/Stage2/Stage3 背景 grid 是否均可见。
- [ ] 右侧 Review 面板桌面端是否为左右滑入/滑出。
- [ ] 右侧 Review 面板移动端是否为上下抽屉。
- [ ] Proposal 区域颜色是否为主色 cyan。
- [ ] 任何紫色元素是否被完全移除。
- [ ] 底部 HUD 卡片边框是否上下左右一致。
- [ ] 议员思考过程标题是否仅显示 LOGIC_PROCESS。
- [ ] deepseek 报错是否消失（openrouter None 拼接修复）。
