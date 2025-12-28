# UI 重构开发任务交接

## 🎯 任务目标

将 `frontend_refactor/` 的 Cyberpunk UI 设计移植到 `frontend/` 主项目，对接真实后端 API。

---

## 📚 核心参考文档

请仔细阅读以下两份文档，它们包含了所有需要遵循的规范：

| 文档 | 路径 | 内容 |
|------|------|------|
| **技术规格** | `docs/UI_REFACTOR_SPEC.md` | 数据映射、组件架构、后端改动、代码示例 |
| **视觉规范** | `docs/UI_STYLE_GUIDE.md` | 颜色、字体、动画、组件样式 |

---

## ✅ 已确认的技术决策 (无需再讨论)

1. **AgentId**：使用 `string` + 前端映射表 (见 SPEC 4.6节)
2. **Stage1 标题**：从 Markdown H1 提取，无则不显示
3. **Stage2 评价**：后端改 Prompt 输出 `per_candidate_comments` 结构
4. **HUD 分数显示**：显示 "平均 #X.X" (数值越低越好)
5. **Thinking 持久化**：不保留，历史对话不显示 thinking

---

## 📋 开发优先级建议

### Phase 1: 基础迁移
- [ ] 迁移 CSS 样式 (动画 keyframes、纹理背景) 到 `index.css`
- [ ] 创建 `src/config/councilors.js` 议员 UI 配置
- [ ] 实现 `useParliamentEngine` Hook (参考 SPEC 9.1节)

### Phase 2: 组件开发
- [ ] 新建 `TacticalHUD.jsx` (参考 SPEC 9.3节 + Style Guide 5.2节)
- [ ] 新建 `WelcomeScreen.jsx` (含 HUD 插槽逻辑，见 Style Guide 5.6节)
- [ ] 新建 `DetailPanel.jsx` (参考 SPEC 9.2节)

### Phase 3: 集成与特效
- [ ] 实现 Consensus Beacon (参考 Style Guide 5.5节)
- [ ] 集成 SSE 流式处理

### Phase 4: 后端配合
- [ ] 修改 `backend/council.py` Stage 2 Prompt (参考 SPEC 7.1-7.4节)

---

## ⚠️ 特别注意事项

1. **HUD 插槽机制** (Style Guide 5.6节)
   - Welcome Screen 时，选中议员要立即在 HUD 显示 "READY" 卡片
   - 取消选中时变回虚线空插槽

2. **Consensus Beacon** (Style Guide 5.5节)
   - 图标：使用 `lucide-react` 的 `Scale` (天平)
   - 首次出现：紫色 + 呼吸扩散动画
   - 看过后切回其他 Tab：保留按钮但移除动画

3. **Consensus Ready Overlay** (Style Guide 5.4节)
   - 覆盖在 HUD 区域上方，**不是全屏**
   - 点击后永久消失

4. **Stage 颜色跟随** (Style Guide 2.5节)
   - HUD 顶部边框颜色跟随 Stage 变化
   - Stage 1 Orange → Stage 2 Blue → Stage 3 Purple

5. **排名显示格式**
   - 使用 "平均 #1.2" 而非 "9.2分"
   - 数值越低表示排名越靠前

---

## ❌ 明确不需要实现的功能

| 功能 | 原位置 | 不需要的原因 |
|------|--------|-------------|
| **ConnectionOverlay (贝塞尔曲线)** | TacticalHUD Stage 2 | 视觉复杂，投入产出比低 |
| **PeerReview.type 字段** | types.ts | 用户无需区分"批评/建议"类型 |

---

## 🔍 代码参考

- **旧项目 API 调用**：`frontend/src/api.js`
- **旧项目 SSE 处理**：`frontend/src/App.jsx` (第 200-350 行)
- **新 UI 组件参考**：`frontend_refactor/components/`
- **新 UI Mock 数据结构**：`frontend_refactor/mockData.ts`

---

如有任何歧义，以 `UI_REFACTOR_SPEC.md` 为准。
