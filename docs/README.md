# LLM Council Sentinel

LLM Council Sentinel 是一个可本地运行的多模型协作问答系统。系统将多个 LLM 组织成“议员（Councilor）+ 主席（Chairman）”结构，并通过三阶段流程输出最终结论。

## 0. 术语（Terminology）

| 术语 | 含义 | 来源/实现 |
| --- | --- | --- |
| Councilor（议员） | 参与 Stage1 与 Stage2 的模型实例 | `backend/config.py` -> `COUNCILORS` |
| Chairman（主席） | 负责 Stage3 综合总结的模型实例 | `backend/config.py` -> `CHAIRMAN` |
| Stage1 | 多 Councilor 并行生成候选答案（Markdown） | `backend/council.py` -> `stage1_collect_responses` |
| Stage2 | 匿名互评：输出排序与评语（JSON） | `backend/council.py` -> `stage2_collect_rankings` |
| Stage3 | 主席综合总结（Markdown） | `backend/council.py` -> `stage3_synthesize_final` |
| Thinking | 通过 `emit_thinking` 工具输出“公开可见的思考步骤” | `backend/council.py` + SSE `thinking` |
| Conversation | 持久化对话 JSON 文件 | `data/conversations/*.json` |
| Model Assignment | 固定模型分配（schema_version=3） | `backend/model_assigner.py` |

## 1. 流程概览（ASCII）

```
User Input
   |
   v
Stage1: Councilor 并行回答 (Markdown)
   |
   v
Stage2: 匿名互评 (ranking/scores/comments)
   |
   v
Stage3: Chairman 综合结论 (Markdown)
```

## 2. 快速开始（本地开发）

### 2.1 依赖
- Python >= 3.10
- Node.js >= 18
- `uv`（推荐）或 `pip/venv`

### 2.2 后端
```bash
uv sync
uv run python -m backend.main
```
默认端口：`http://localhost:8010`

### 2.3 前端
```bash
cd frontend
npm install
npm run dev
```
默认端口：`http://localhost:5173`

### 2.4 验证
```bash
curl http://localhost:8010/health
curl http://localhost:8010/api/councilors
```

### 2.5 Docker + Nginx
```bash
cd frontend
npm install
npm run build
cd ..
docker-compose up -d
```
访问：`http://localhost`

注意：前端 `API_BASE` 固定为 `http://localhost:8010`（见 `frontend/src/api.js`）。如走 Nginx 代理，应改为 `http://localhost/api` 或设置兼容反向代理。

## 3. 目录结构

| 目录/文件 | 用途 |
| --- | --- |
| `backend/` | FastAPI 后端、LLM 编排、健康检查与持久化 |
| `frontend/` | React 前端、HUD UI 与 SSE 客户端 |
| `data/` | 对话持久化目录（默认 `data/conversations`） |
| `docs/` | 项目文档（本目录） |
| `nginx.conf` | Docker/Nginx 反向代理配置 |
| `docker-compose.yml` | 容器编排 |

## 4. 关键配置

- 环境变量：`.env`（见 `docs/配置说明.md`）
- 模型池与角色：`backend/config.py`
- 头像资源：`frontend/public/avatars/`（路径写入 `backend/config.py` 的 `avatar` 字段）
- Persona 文件：`backend/personas/`

## 5. 文档索引

- `docs/Architecture.md`：系统架构
- `docs/API_REFERENCE.md`：API 与 SSE 协议
- `docs/DATA_SCHEMA.md`：数据结构与存储
- `docs/配置说明.md`：配置项说明
- `docs/AGENTS.md`：核心流程与约束（技术版）
- `docs/UI_STYLE_GUIDE.md`：前端 HUD 视觉规范

## 6. 运行约束与已知行为

- 消息长度上限：`1000` 字符（前后端一致）。
- 速率限制：`/message` 与 `/message/stream` 均为 `5/min`（按 IP）。
- 管理员 Token：后端当前为 debug 模式，`verify_admin` 直接放行（见 `backend/main.py`）。
- Thinking 持久化：仅流式 `/message/stream` 会写入 `metadata.thinking`。
- Stage2 跳过条件：有效候选答案 `< 2`。

---

Last updated: 2026-01-23

