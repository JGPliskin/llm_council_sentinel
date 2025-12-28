# LLM Council Sentinel - 视觉设计规范 (Style Guide)

> 📅 文档版本: v1.0 | 更新日期: 2024-12-28
> 
> 🎯 目标: 定义 Cyberpunk 风格 UI 的视觉规范，确保前端实现一致性

---

## 目录

- [1. 设计理念](#1-设计理念)
- [2. 颜色系统](#2-颜色系统)
- [3. 字体系统](#3-字体系统)
- [4. 动画规范](#4-动画规范)
- [5. 组件样式](#5-组件样式)
- [6. 纹理与背景](#6-纹理与背景)
- [7. 间距与布局](#7-间距与布局)
- [8. 响应式断点](#8-响应式断点)
- [9. CSS 变量定义](#9-css-变量定义)

---

## 1. 设计理念

### 1.1 设计风格

**Cyberpunk Tactical HUD** - 结合科幻战术界面与现代极简主义

| 关键词 | 描述 |
|--------|------|
| **暗色主导** | 以 zinc-900/950 为基底，减少视觉疲劳 |
| **霓虹强调** | 使用 orange/blue/purple/teal 等饱和色作为重点 |
| **斜切边角** | 使用 `clip-path: polygon()` 创造战术感 |
| **网格纹理** | 点阵/网格背景增加层次感 |
| **微动画** | 脉冲、扫描线、渐入等增强交互反馈 |

### 1.2 设计原则

1. **信息层次清晰** - 主要信息用高对比色，次要信息用低对比色
2. **状态可感知** - 通过颜色、动画、图标明确表达当前状态
3. **操作可预期** - hover/active 状态有明确的视觉反馈
4. **一致性** - 相同功能使用相同的视觉语言

---

## 2. 颜色系统

### 2.1 基础色板

| 色彩名称 | Tailwind 类 | Hex | 用途 |
|----------|-------------|-----|------|
| **背景主色** | `bg-zinc-950` | `#09090b` | 页面/卡片背景 |
| **背景次色** | `bg-zinc-900` | `#18181b` | 面板/条栏背景 |
| **边框色** | `border-zinc-800` | `#27272a` | 默认边框 |
| **文字主色** | `text-zinc-100` | `#f4f4f5` | 主要文字 |
| **文字次色** | `text-zinc-500` | `#71717a` | 次要/辅助文字 |
| **禁用色** | `text-zinc-700` | `#3f3f46` | 禁用状态 |

### 2.2 强调色

| 颜色 | Tailwind 类 | Hex | 语义 |
|------|-------------|-----|------|
| **Orange** | `orange-500` | `#f97316` | Stage 1 生成中、活跃状态 |
| **Blue** | `blue-500` | `#3b82f6` | Stage 2 评审中、评审者 |
| **Purple** | `purple-500` | `#a855f7` | Stage 3 综合、Consensus |
| **Teal** | `teal-500` | `#14b8a6` | 完成状态 |
| **Red** | `red-500` | `#ef4444` | 错误、被评审目标 |
| **Yellow** | `yellow-400` | `#facc15` | 第一名/最高排名 |

### 2.3 议员专属颜色

| 议员 ID | 颜色 | Tailwind 前缀 |
|---------|------|---------------|
| `immanuel_kant` | Orange | `orange-` |
| `donald_trump` | Red | `red-` |
| `hideo_kojima` | Blue | `blue-` |
| `chairman` | Purple | `purple-` |

### 2.4 颜色使用规则

```css
/* 边框高亮 */
.agent-card--active {
  border-color: var(--agent-color-500);
  box-shadow: inset 0 0 20px rgba(var(--agent-color-rgb), 0.2);
}

/* 文字强调 */
.status-generating { color: theme('colors.orange.500'); }
.status-reviewing  { color: theme('colors.blue.500'); }
.status-consensus  { color: theme('colors.purple.500'); }
.status-complete   { color: theme('colors.teal.500'); }
```

### 2.5 Stage 颜色跟随规范

**HUD 元素会根据当前 Stage 动态变化颜色**：

| Stage | 颜色 | 应用位置 |
|-------|------|----------|
| idle | `zinc-500` | HUD 状态文字、指示灯 |
| stage1 | `orange-500` | HUD 状态文字、指示灯、顶部边框 |
| stage2 | `blue-500` | HUD 状态文字、指示灯、顶部边框 |
| stage3 | `purple-500` | HUD 状态文字、指示灯、顶部边框 |

**CSS 实现**：

```css
/* HUD 顶部边框跟随 Stage */
.tactical-hud--stage1 { border-top-color: theme('colors.orange.600'); }
.tactical-hud--stage2 { border-top-color: theme('colors.blue.600'); }
.tactical-hud--stage3 { border-top-color: theme('colors.purple.600'); }

/* 状态指示灯 */
.stage-indicator__dot--idle    { background: theme('colors.zinc.600'); }
.stage-indicator__dot--stage1  { background: theme('colors.orange.500'); animation: pulse 1s infinite; }
.stage-indicator__dot--stage2  { background: theme('colors.blue.500'); }
.stage-indicator__dot--stage3  { background: theme('colors.purple.500'); }
```

### 2.6 明确不需要的功能

> [!IMPORTANT]
> 以下功能在原 frontend_refactor 中存在，但**本次迁移中不需要实现**：

| 功能 | 原位置 | 不需要的原因 |
|------|--------|-------------|
| **ConnectionOverlay (贝塞尔曲线)** | TacticalHUD Stage 2 | 视觉复杂，投入产出比低 |
| **PeerReview.type 字段** | types.ts | 用户无需区分"批评/建议"类型 |

## 3. 字体系统

### 3.1 字体家族

| 类型 | 字体名 | 权重 | 用途 |
|------|--------|------|------|
| **无衬线** | Inter | 400, 500, 600, 700, 900 | 主要 UI 文字 |
| **衬线** | Merriweather | 300, 400, 700 | 内容区长文 |
| **等宽** | JetBrains Mono | 400, 700 | 代码、状态标签、ID |

### 3.2 字体引入

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&family=Merriweather:ital,wght@0,300;0,400;0,700;1,300;1,400&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
```

### 3.3 CSS 类

```css
body { font-family: 'Inter', sans-serif; }
.font-serif { font-family: 'Merriweather', serif; }
.font-mono { font-family: 'JetBrains Mono', monospace; }
```

### 3.4 字号规范

| 元素 | Tailwind 类 | 尺寸 |
|------|-------------|------|
| 大标题 | `text-3xl md:text-5xl` | 30px / 48px |
| 标题 | `text-xl` | 20px |
| 正文 | `text-base` | 16px |
| 小字 | `text-sm` | 14px |
| 微型标签 | `text-[10px]` / `text-xs` | 10px / 12px |

---

## 4. 动画规范

### 4.1 关键帧定义

```css
/* 淡入 */
@keyframes fadeIn { 
  from { opacity: 0; } 
  to { opacity: 1; } 
}

/* 从右滑入 */
@keyframes slideInRight { 
  from { transform: translateX(20px); opacity: 0; } 
  to { transform: translateX(0); opacity: 1; } 
}

/* 从下滑入 */
@keyframes slideInUp { 
  from { transform: translateY(20px); opacity: 0; } 
  to { transform: translateY(0); opacity: 1; } 
}

/* 脉冲光晕 */
@keyframes pulse-glow { 
  0%, 100% { box-shadow: 0 0 5px rgba(255, 107, 0, 0.2); } 
  50% { box-shadow: 0 0 20px rgba(255, 107, 0, 0.6); } 
}

/* SVG 路径绘制 */
@keyframes dash { 
  to { stroke-dashoffset: 0; } 
}

/* 扫描线 */
@keyframes scanline { 
  0% { transform: translateY(-100%); } 
  100% { transform: translateY(100%); } 
}
```

### 4.2 动画工具类

```css
.animate-in { animation-fill-mode: both; }
.fade-in { animation-name: fadeIn; }
.slide-in-from-right-4 { animation-name: slideInRight; }
.slide-in-from-bottom-4 { animation-name: slideInUp; }
.duration-500 { animation-duration: 500ms; }
.duration-700 { animation-duration: 700ms; }
```

### 4.3 使用场景

| 场景 | 动画 | 类组合 |
|------|------|--------|
| 卡片进入 | 淡入 + 上滑 | `animate-in fade-in slide-in-from-bottom-4 duration-500` |
| 面板展开 | 淡入 + 右滑 | `animate-in fade-in slide-in-from-right-4 duration-500` |
| 加载状态 | 脉冲 | `animate-pulse` |
| 扫描效果 | 扫描线 | `animate-[scanline_2s_linear_infinite]` |

---

## 5. 组件样式

### 5.1 斜切卡片 (Tactical Card)

```css
.tactical-card {
  clip-path: polygon(
    10px 0,      /* 左上角切角 */
    100% 0, 
    100% calc(100% - 10px),  /* 右下角切角 */
    calc(100% - 10px) 100%, 
    0 100%, 
    0 10px
  );
}
```

```html
<div class="relative backdrop-blur-sm overflow-hidden"
     style="clip-path: polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px)">
  <!-- 内容 -->
</div>
```

### 5.2 HUD 议员卡片 (AgentSlice)

**结构**：

```
┌───────────────────────────────┐
│ ▪ ▪                     [状态图标] │  ← 顶部端口 + 图标
├───────────────────────────────┤
│                               │
│  🧠 KANT                      │  ← Avatar + 名字
│  ████████░░░ 78%              │  ← 进度条 (Stage 1)
│  或 平均 #1.2                  │  ← 排名 (Stage 2/3)
│  DEONTOLOGIST                  │  ← 角色标签
├───────────────────────────────┤
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ │  ← 底部端口
└───────────────────────────────┘
```

**状态样式**：

| 状态 | 边框颜色 | 内发光 | 图标 |
|------|----------|--------|------|
| standby | `border-zinc-800` | 无 | 🔒 Lock |
| generating | `border-orange-500/50` | orange | ⚡ Zap (脉冲) |
| reviewer | `border-blue-500/50` | blue | 🎯 Target |
| target | `border-red-500/50` | red | 🛡️ ShieldAlert (弹跳) |
| complete | `border-teal-600/50` | 无 | 无 |

### 5.3 内容区标签页 (Tabs)

```css
/* 激活状态 */
.tab--active {
  background: theme('colors.zinc.800');
  color: white;
  border-top: 2px solid theme('colors.orange.500');
  margin-bottom: -1px;
  padding-bottom: 1rem;
}

/* 未激活状态 */
.tab--inactive {
  background: theme('colors.zinc.900')/50;
  color: theme('colors.zinc.500');
}

/* Consensus Tab 激活 */
.tab--consensus-active {
  color: theme('colors.purple.400');
  border-top-color: theme('colors.purple.500');
}
```

### 5.4 Consensus Ready Overlay

**位置**：覆盖在底部 HUD 区域上方 (非全屏)

**触发条件**：Stage 3 完成 且 `hasViewedConsensus === false`

**行为**：用户点击后**永久消失**，同时 `hasViewedConsensus` 设为 `true`

```css
.consensus-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(4px);
  z-index: 40;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.consensus-banner {
  background: theme('colors.zinc.900');
  border: 2px solid theme('colors.purple.500');
  padding: 1.5rem;
  transform: skewX(-12deg);
  box-shadow: 0 0 50px rgba(168, 85, 247, 0.5);
}

.consensus-banner__content {
  transform: skewX(12deg);  /* 反向倾斜恢复文字 */
  text-align: center;
}
```

### 5.5 Consensus Beacon (战术数据信标)

**位置**：内容区右下角悬浮按钮

**图标**：使用 `lucide-react` 的 `Scale` (天平) 图标

**行为逻辑**：

| 状态 | 触发条件 | 视觉表现 |
|------|----------|----------|
| **首次出现** | Stage 3 完成，用户尚未点击 | 紫色 + 强烈呼吸/扩散动画 |
| **已查看后** | 用户看过 Consensus 后切回其他 Tab | 紫色静止按钮，无动画 |

**CSS 实现**：

```css
/* 呼吸扩散动画 */
@keyframes beacon-ping {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  75%, 100% {
    transform: scale(2);
    opacity: 0;
  }
}

/* Beacon 按钮 */
.consensus-beacon {
  position: fixed;
  bottom: 180px;  /* 在 HUD 上方 */
  right: 24px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: theme('colors.purple.600');
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 35;
  transition: transform 0.2s, box-shadow 0.2s;
}

.consensus-beacon:hover {
  transform: scale(1.1);
  box-shadow: 0 0 30px rgba(168, 85, 247, 0.6);
}

/* 首次出现：呼吸动画 */
.consensus-beacon--pinging::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: theme('colors.purple.500');
  animation: beacon-ping 1.5s ease-out infinite;
}

/* 已查看：静止状态 */
.consensus-beacon--static {
  opacity: 0.8;
}
.consensus-beacon--static::before {
  display: none;  /* 移除呼吸动画 */
}
```

### 5.6 Welcome Screen HUD 插槽 (Squad Staging Area)

**核心概念**：底部 HUD 不仅是"运行时输出框"，而是**"插槽 (Slot)"**。

**行为逻辑**：

| 操作 | HUD 变化 |
|------|----------|
| 选中一个议员 | 对应插槽立即填充为 "READY" 卡片 |
| 取消选中 | 插槽变回空的虚线框 |

**状态样式 (新增)**：

| 状态 | 边框颜色 | 背景 | 文字 | 动画 |
|------|----------|------|------|------|
| **empty** (空插槽) | `border-dashed border-zinc-700` | 透明 | 无 | 无 |
| **ready** (就绪) | `border-zinc-600` | `bg-zinc-900/60` | "READY" | 无 |

**CSS 实现**：

```css
/* 空插槽 */
.agent-slot--empty {
  border: 2px dashed theme('colors.zinc.700');
  background: transparent;
  opacity: 0.4;
}

/* 就绪状态 */
.agent-slot--ready {
  border: 1px solid theme('colors.zinc.600');
  background: rgba(24, 24, 27, 0.6);  /* zinc-900/60 */
}

.agent-slot--ready .agent-name {
  color: theme('colors.zinc.400');
}

.agent-slot--ready .agent-status {
  color: theme('colors.zinc.600');
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

/* "READY" 或 "STANDBY" 标签 */
.agent-slot--ready::after {
  content: 'READY';
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 8px;
  color: theme('colors.zinc.600');
  letter-spacing: 0.2em;
}
```

**视觉示意**：

```
Welcome Screen 激活时的底部 HUD：

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ ┌──────────┐ │  │              │  │              │
│ │ 🧠 康德  │ │  │    ┌────┐   │  │    ┌────┐   │
│ │ READY    │ │  │    │ +  │   │  │    │ +  │   │
│ └──────────┘ │  │    └────┘   │  │    └────┘   │
│   已选中     │  │   空插槽     │  │   空插槽     │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## 6. 纹理与背景

### 6.1 点阵背景

```css
.bg-dot-pattern {
  background-image: radial-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px);
  background-size: 4px 4px;
}
```

### 6.2 网格背景

```css
.bg-grid-pattern {
  background-size: 40px 40px;
  background-image: 
    linear-gradient(to right, rgba(255, 255, 255, 0.05) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
}
```

### 6.3 斜条纹背景 (用于进度条)

```css
.bg-stripe-pattern {
  background-image: repeating-linear-gradient(
    45deg,
    rgba(0, 0, 0, 0.2),
    rgba(0, 0, 0, 0.2) 5px,
    transparent 5px,
    transparent 10px
  );
}
```

---

## 7. 间距与布局

### 7.1 间距规范

| 用途 | Tailwind 类 | 像素值 |
|------|-------------|--------|
| 组件内边距 (小) | `p-2` | 8px |
| 组件内边距 (中) | `p-4` | 16px |
| 组件内边距 (大) | `p-6 md:p-8` | 24px / 32px |
| 元素间距 (小) | `gap-1` / `gap-2` | 4px / 8px |
| 元素间距 (中) | `gap-4` | 16px |
| 区块间距 | `mb-6 md:mb-8` | 24px / 32px |

### 7.2 布局尺寸

| 区域 | 桌面端 | 移动端 |
|------|--------|--------|
| 左侧边栏 | `w-64` (256px) | 隐藏/抽屉 |
| 右侧详情面板 | `w-[400px]` | 底部抽屉 `h-[60vh]` |
| 底部 HUD | `h-40 md:h-48` | `h-40 md:h-48` |
| 内容区最大宽度 | `max-w-4xl` | 100% |

---

## 8. 响应式断点

| 断点 | 宽度 | Tailwind 前缀 |
|------|------|---------------|
| 移动端 | < 768px | (default) |
| 平板/桌面 | >= 768px | `md:` |
| 大屏 | >= 1024px | `lg:` |
| 超大屏 | >= 1280px | `xl:` |

### 8.1 响应式隐藏规则

```css
/* 移动端隐藏，桌面显示 */
.hide-mobile { display: none; }
@media (min-width: 768px) { .hide-mobile { display: block; } }

/* 桌面隐藏，移动端显示 */
.hide-desktop { display: block; }
@media (min-width: 768px) { .hide-desktop { display: none; } }
```

---

## 9. CSS 变量定义

将以下变量添加到 `frontend/src/index.css`：

```css
:root {
  /* 背景 */
  --bg-primary: #09090b;     /* zinc-950 */
  --bg-secondary: #18181b;   /* zinc-900 */
  --bg-tertiary: #27272a;    /* zinc-800 */
  
  /* 文字 */
  --text-primary: #f4f4f5;   /* zinc-100 */
  --text-secondary: #71717a; /* zinc-500 */
  --text-muted: #3f3f46;     /* zinc-700 */
  
  /* 边框 */
  --border-default: #27272a; /* zinc-800 */
  --border-subtle: #18181b;  /* zinc-900 */
  
  /* 强调色 */
  --accent-orange: #f97316;
  --accent-blue: #3b82f6;
  --accent-purple: #a855f7;
  --accent-teal: #14b8a6;
  --accent-red: #ef4444;
  --accent-yellow: #facc15;
  
  /* 动画时长 */
  --duration-fast: 150ms;
  --duration-normal: 300ms;
  --duration-slow: 500ms;
  
  /* 圆角 */
  --radius-sm: 2px;
  --radius-md: 4px;
  --radius-lg: 8px;
}
```

---

## 附录：从 frontend_refactor 迁移的关键样式文件

| 源文件 | 迁移内容 |
|--------|----------|
| `frontend_refactor/index.html` | `<style>` 内的动画定义、纹理背景 |
| `frontend_refactor/components/TacticalHUD.tsx` | AgentSlice 样式、状态颜色 |
| `frontend_refactor/components/StageContentArea.tsx` | Tab 样式、内容卡片 |
| `frontend_refactor/components/WelcomeScreen.tsx` | 欢迎界面布局 |

---

> 📄 文档结束
