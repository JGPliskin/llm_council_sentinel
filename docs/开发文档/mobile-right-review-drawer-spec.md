# 移动端右侧 Review 抽屉规范

## 目录
- 背景与目标
- 用户场景与需求描述
- 交互与布局规则
- 抽屉高度策略
- 内容展示与滚动策略
- 技术方案与数据流
- 流程图与结构图
- 需要改动的代码文件与关键修改
- 风险与对策
- 验收标准

## 背景与目标
移动端保持左侧对话列表侧边栏不变，仅将右侧 Review 面板改为底部抽屉。抽屉高度采用固定档位，并允许内部滚动，避免内容截断。桌面端保持原有右侧面板。

## 用户场景与需求描述
| 阶段 (Stage) | 初始状态 | 打开后内容 | 高度行为 | 特殊控件 |
| --- | --- | --- | --- | --- |
| Stage 1 | 默认关闭 | 显示用户输入的问题 | 固定 1 档 (30vh) | 无全屏按钮 |
| Stage 2 | 默认关闭 | 显示 Judge 思考与评审 | 动态 1/2/3 档 | 无全屏按钮 |
| Stage 3 | 默认关闭 | 展示所有 Peer Reviews | 固定 3 档 (60vh) | 显示全屏按钮 |

说明：移动端右侧抽屉与左侧对话列表互斥，任一打开都会关闭另一方。

## 交互与布局规则
| 规则 | 说明 |
| --- | --- |
| 触发方式 | 点击左下角“打开面板”按钮 |
| 关闭方式 | 抽屉头部关闭按钮 + 点击遮罩 |
| 互斥 | 打开抽屉时自动关闭左侧对话列表，反之亦然 |
| 遮罩 | 覆盖主内容，抽屉位于遮罩之上 |
| HUD 层级 | HUD 位于抽屉下方，抽屉头部固定提供关闭/全屏 |
| 拖拽 | 仅显示视觉拖拽条，不支持手势关闭 |

## 抽屉高度策略
采用固定档位高度，视觉上“约等于 3 张卡片高度”。

| 档位 | 高度 | 用途 |
| --- | --- | --- |
| 1 档 | 30vh | Stage 1 / Stage 2 (1 张卡片) |
| 2 档 | 45vh | Stage 2 (2 张卡片) |
| 3 档 | 60vh | Stage 2 (>=3 张卡片) / Stage 3 默认 |
| 全屏 | 90vh | Stage 3 手动切换 |

Stage 2 规则：
- 高度只增不减，避免频繁跳动。
- Stage 2 结束或抽屉关闭时，重置为 1 档。
- Stage 2 skipped 场景固定 1 档。

## 内容展示与滚动策略
| Stage | 内容 | 滚动策略 |
| --- | --- | --- |
| Stage 1 | 用户输入的问题 | 内容区可滚动 |
| Stage 2 | Judge 思考卡片与评审 | 内容区可滚动，不截断 |
| Stage 3 | Review 列表 | 内容区可滚动，不截断 |

## 技术方案与数据流
### 数据与状态
| 状态/数据 | 归属 | 用途 |
| --- | --- | --- |
| isPanelOpen | App | 右侧抽屉开合 |
| isSidebarOpen | App | 左侧对话列表开合 |
| panelHeightTier | App | 抽屉高度档位 (1/2/3/Full) |
| isPanelFullscreen | App | 是否全屏 (Stage 3) |
| currentPrompt | engine.conversation.messages[0] | Stage 1 显示用户问题 |

### 互斥逻辑 (App)
```javascript
const openRightPanel = () => {
  setIsPanelOpen(true);
  if (window.innerWidth < 768) setIsSidebarOpen(false);
};

const openLeftSidebar = () => {
  setIsSidebarOpen(true);
  if (window.innerWidth < 768) setIsPanelOpen(false);
};
```

### 动态高度计算
动态高度逻辑放在 DetailPanel 或提成共享函数，避免 App 与实际 UI 不一致。

Stage 2 高度计算规则：
1) 统计可见 JudgeCard 数量。
2) clamp 到 1-3 档。
3) debounce 300ms 以减抖。
4) 只增不减，关闭或 Stage2 结束时重置。

Stage 2 skipped：
- 抽屉显示 “SKIPPED” 信息时固定 1 档。

## 流程图与结构图
### 抽屉开合流程
```
[点击按钮]
      |
      v
[抽屉上滑 + 遮罩出现]
      |
      +--> [点击遮罩或关闭按钮] -> [抽屉关闭]
```

### 互斥流程
```
[打开右侧抽屉] -> [关闭左侧对话列表]
[打开左侧对话列表] -> [关闭右侧抽屉]
```

### 移动端结构示意
```
Z-30 主内容区
Z-40 遮罩层
Z-50 底部抽屉
```

## 需要改动的代码文件与关键修改
| 文件 | 目的 | 关键修改 |
| --- | --- | --- |
| `frontend/src/App.jsx` | 移动端抽屉容器与互斥逻辑 | mobile 使用 bottom sheet；互斥开合；管理全屏与档位 |
| `frontend/src/components/DetailPanel.jsx` | Stage1 内容展示 + 高度计算 | 增加 Stage1 prompt 展示；提供可见卡片数计算 |
| `frontend/src/hooks/useParliamentEngine.js` | Stage1 prompt 数据来源 | 确保 conversation.messages[0] 可用 |
| `frontend/src/components/ui/sheet.jsx` | 抽屉动画 | 复用 bottom sheet 样式与遮罩 |

## 风险与对策
| 风险 | 影响 | 对策 |
| --- | --- | --- |
| Stage 2 高度频繁跳动 | 视觉疲劳 | debounce 300ms + 高度只增不减 |
| 内容过长 | 内容被裁切 | 内容区滚动，不截断 |
| 遮罩挡住按钮 | 无法关闭 | 抽屉头部固定关闭按钮 |

## 验收标准
1) 移动端右侧面板改为底部抽屉，桌面端保持右侧面板。
2) 抽屉仅手动打开，不自动弹出。
3) Stage 1 显示用户问题，固定 1 档高度。
4) Stage 2 动态 1/2/3 档，高度只增不减，Stage2 结束或关闭后重置。
5) Stage 2 skipped 时显示 SKIPPED 信息且高度为 1 档。
6) Stage 3 默认 3 档高度，并支持全屏切换。
7) 抽屉内容区滚动，不截断。
8) 移动端左右互斥：打开一方自动关闭另一方。
