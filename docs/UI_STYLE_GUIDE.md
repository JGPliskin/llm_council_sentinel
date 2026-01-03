# UI_STYLE_GUIDE.md - LLM Council Sentinel 视觉规范

本文档描述当前前端 UI 的实际视觉规范与约束，目标是“给任何人看都没有歧义”。所有规则以 `frontend/src` 代码与 `frontend/src/index.css` 为准。

---

## 1. 设计方向

- 风格：暗色系、战术 HUD、轻量赛博风
- 关键词：对比清晰、信息密度高、状态可感知
- 主要使用 Tailwind 类与少量 CSS 变量

---

## 2. 颜色系统

### 2.1 主题变量（`frontend/src/index.css`）

```css
:root {
  --bg-primary: #09090b;     /* zinc-950 */
  --bg-secondary: #18181b;   /* zinc-900 */
  --bg-tertiary: #27272a;    /* zinc-800 */

  --text-primary: #f4f4f5;   /* zinc-100 */
  --text-secondary: #71717a; /* zinc-500 */
  --text-muted: #3f3f46;     /* zinc-700 */

  --border-default: #27272a; /* zinc-800 */
  --border-subtle: #18181b;  /* zinc-900 */

  --accent-orange: #f97316;
  --accent-blue: #3b82f6;
  --accent-purple: #a855f7;
  --accent-teal: #14b8a6;
  --accent-red: #ef4444;
  --accent-yellow: #facc15;
}
```

### 2.2 Councilor 颜色映射

来源：`frontend/src/config/councilors.js`

| Councilor ID | 颜色关键字 | CSS 变量 |
|---|---|---|
| `immanuel_kant` | orange | `--accent-orange` |
| `donald_trump` | red | `--accent-red` |
| `hideo_kojima` | blue | `--accent-blue` |
| `chairman` | purple | `--accent-purple` |

UI 中多处使用：`style={{ background: "var(--accent-orange)" }}`

---

## 3. 字体系统

### 3.1 默认字体

当前默认字体栈（`index.css`）：

```css
body {
  font-family:
    -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Oxygen",
    "Ubuntu", "Cantarell", sans-serif;
}
```

### 3.2 等宽字体

```css
code, .mono {
  font-family: "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, monospace;
}
```

---

## 4. 动画与过渡

### 4.1 常用类

- `animate-in fade-in slide-in-from-bottom-4 duration-500`
- `animate-pulse`
- `scroll-smooth`

### 4.2 Thinking → Review/Answer 过渡

**要求**：cross-fade + 轻微上移，180-240ms

**规范描述**：
- opacity: 1 → 0（thinking） / 0 → 1（review/answer）
- transform: translateY(4px) → translateY(0)
- duration: 180-240ms
- 背景适配：避免纯透明导致文字对比不足，必要时保持 `bg-zinc-950/60` 底色

---

## 5. 布局规范

| 区域 | 桌面宽度 | 说明 |
|---|---|---|
| Sidebar | 约 256px | 通过 `Sidebar.jsx` 控制 |
| DetailPanel | 400px | `md:w-[400px]` |
| 内容区 | 100% | `StageContentArea.jsx` |

移动端：Sidebar 与 DetailPanel 均为覆盖式抽屉。

---

## 6. 核心组件样式约定

### 6.1 StageContentArea

- 头部 tabs：`bg-zinc-900/80` + 边框
- 内容卡：`bg-zinc-900/40` + `border-zinc-800`
- Thinking 区块：`bg-zinc-950/60` + `border-zinc-800`

### 6.2 DetailPanel

- Panel 背景：`bg-zinc-900/90`
- Judge 卡片：`bg-zinc-950/50` + `border-zinc-800`
- 状态标识：
  - thinking：橙色 `text-orange-500`
  - done：绿色 `text-green-500`

### 6.3 TacticalHUD

- 主题随 Stage 切换
  - Stage1：橙色
  - Stage2：蓝色
  - Stage3：紫色

---

*Last updated: 2026-01-03*
