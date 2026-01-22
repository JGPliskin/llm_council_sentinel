# LLM Council Sentinel

一个本地可运行的多模型协作问答系统。系统将多个 LLM 组成“委员会”，并通过三阶段流程完成多方观点输出与匿名互评，最终由主席给出综合结论。

---

## 1. 核心特性

- **Stage1 并行回答**：多 Councilor 同时输出 Markdown 回答
- **Stage2 匿名互评**：匿名化后互评排序，输出 JSON 评审结果
- **Stage3 共识综合**：主席模型输出最终结论
- **SSE 流式输出**：Thinking 与答案增量实时推送
- **固定模型分配**：对话创建时分配并固定模型（schema_version=3）

---

## 2. 工作流程

1. **Stage1**：多 Councilor 生成回答（Markdown）
2. **Stage2**：匿名互评并输出 `ranking + scores + per_candidate_comments`
3. **Stage3**：Chairman 综合输出最终结论（Markdown）

---

## 3. 安装与配置

### 3.1 依赖

- Python >= 3.10
- Node.js >= 18
- 推荐使用 `uv` 管理 Python 依赖

### 3.2 安装

后端：
```bash
uv sync
```

前端：
```bash
cd frontend
npm install
cd ..
```

### 3.3 配置 API Key

在项目根目录创建 `.env`：

```bash
OPENROUTER_API_KEY=sk-or-v1-...
NIM_API_KEYS=nvapi-...,nvapi-...  # 可配置多个 Key 轮替
```

---

## 4. 运行方式

### 4.1 本地开发

后端（8010）：
```bash
uv run python -m backend.main
```

前端（5173）：
```bash
cd frontend
npm run dev
```

打开：`http://localhost:5173`

### 4.2 Docker（Nginx 代理）

```bash
cd frontend && npm install && npm run build && cd ..
docker-compose up -d
```

访问：`http://localhost`（Nginx 转发 `/api/*` → backend:8008）

> 注意：前端 `API_BASE` 默认是 `http://localhost:8010`，Docker 场景需修改 `frontend/src/api.js` 以使用 `http://localhost/api`。

---

## 5. 模型配置

修改 `backend/config.py` 以调整 Councilor/Chairman 模型：

- `COUNCILORS`: Stage1/Stage2 评审员
- `CHAIRMAN`: Stage3 主席

---

## 6. 文档索引

- `docs/AGENTS.md` - 架构与流程
- `docs/API_REFERENCE.md` - API 参考
- `docs/DATA_SCHEMA.md` - 数据模型
- `docs/配置说明.md` - 配置参数
- `docs/UI_STYLE_GUIDE.md` - UI 样式规范
- `docs/开发文档/mobile-right-review-drawer-spec.md` - Mobile Review Drawer Implementation

---

## 7. 免责声明

本项目为实验性多模型协作系统，代码按原样提供，仅供参考与学习用途。

---

*Last updated: 2026-01-18*
