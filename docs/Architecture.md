# Architecture.md - LLM Council Sentinel 系统架构总览

本文档描述系统的组件边界、数据流与部署拓扑。内容以当前代码实现为准（后端 `backend/`，前端 `frontend/`）。

---

## 1. 系统概览

LLM Council Sentinel 是一个三阶段协作系统：
- Stage1：多议员并行回答
- Stage2：匿名互评
- Stage3：主席综合结论

关键特性：
- SSE 流式推送（Thinking + Answer Delta）
- 固定模型分配（schema_version=3）
- 运行期健康检查与自动路由

---

## 2. 高层拓扑（ASCII）

```
+-----------------------+
|  User Browser         |
|  React UI + SSE Client |
+-----------+-----------+
            |
            | REST / SSE
            v
+-----------+-----------+
| FastAPI Backend        |
| - main.py (API, SSE)   |
| - council.py (3 stages)|
+-----------+-----------+
            |
            | LLM Requests
            v
+-----------+-----------+
| LLM Providers          |
| OpenRouter / NIM       |
+-----------+-----------+
            |
            v
+-----------------------+
| JSON Storage          |
| data/conversations/*  |
+-----------------------+
```

---

## 3. 后端组件职责

| 模块 | 主要职责 | 关键文件 |
| --- | --- | --- |
| API 接入 | 路由、校验、限流、SSE | `backend/main.py` |
| 三阶段编排 | Stage1/2/3 执行与聚合 | `backend/council.py` |
| 模型分配 | 固定分配与可复现策略 | `backend/model_assigner.py` |
| LLM 客户端 | OpenRouter/NIM 统一调用 | `backend/llm_client.py` |
| Provider 适配 | OpenRouter / NIM 请求细节 | `backend/openrouter.py`, `backend/nim.py` |
| 健康检查 | 模型健康与熔断管理 | `backend/health.py`, `backend/validation.py` |
| 持久化 | JSON 文件存储 | `backend/storage.py` |
| 运行统计 | TTFT/生成耗时 EMA | `backend/runtime_stats.py` |
| 并发跟踪 | 队列/并发计数用于 ETA | `backend/concurrency_tracker.py` |

---

## 4. 前端组件职责

| 模块 | 主要职责 | 关键文件 |
| --- | --- | --- |
| 应用入口 | 页面布局与状态注入 | `frontend/src/App.jsx` |
| SSE 状态机 | Stage1/2/3 状态维护 | `frontend/src/hooks/useParliamentEngine.js` |
| Welcome UI | 议员选择与启动 | `frontend/src/components/WelcomeScreen.jsx` |
| 内容区 | Stage1/3 展示 | `frontend/src/components/StageContentArea.jsx` |
| 右侧细节 | Stage2 Reviews / Stage3 Thinking | `frontend/src/components/DetailPanel.jsx` |
| 底部 HUD | 进度/状态卡片 | `frontend/src/components/TacticalHUD.jsx` |
| 主题样式 | HUD 设计变量与工具类 | `frontend/src/index.css` |

---

## 5. 数据流（Stage 流程）

### 5.1 Stage1
输入：用户问题 + 议员列表（Councilors）
输出：`stage1[]`（每个议员一条结果）

### 5.2 Stage2
输入：Stage1 有效答案（status=ok）
输出：匿名排序 `ranking` + `scores` + `per_candidate_comments`

### 5.3 Stage3
输入：Stage1 + Stage2 结果
输出：主席综合结论

---

## 6. SSE 事件序列（概要）

```
meta
 -> stage1_start
 -> eta_update / thinking / stage1_answer_delta / stage1_item / stage1_complete
 -> stage2_start
 -> eta_update / thinking / stage2_item / stage2_complete
 -> stage3_start
 -> thinking / stage3_answer_delta / stage3_complete
 -> title_complete
 -> complete
```

详细事件字段请见 `docs/API_REFERENCE.md`。

---

## 7. 部署拓扑

### 7.1 本地开发
- 后端：`http://localhost:8010`
- 前端：`http://localhost:5173`

### 7.2 Docker + Nginx
- 后端容器：`8008`
- Nginx 代理：`80`
- API 访问：`http://localhost/api/*`

---

Last updated: 2026-01-23

