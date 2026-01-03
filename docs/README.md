# LLM Council (LLM 委员会)

![llmcouncil](header.jpg)

这个项目的核心理念是：与其向单个 LLM 提问，不如将它们组成一个"LLM 委员会"。本项目是一个简单的本地 Web 应用，界面类似 ChatGPT，但使用 **OpenRouter** 将你的问题发送给多个 LLM，然后让它们互相评审和排名彼此的回答，最后由主席 LLM 生成最终答案。

## 工作流程

1. **阶段 1：初始观点**。用户的问题被分别发送给所有 LLM（委员会成员），收集各自的回答。各个回答以"标签页视图"显示，用户可以逐一查看。
2. **阶段 2：互评**。每个 LLM 都会收到其他 LLM 的回答。在底层，LLM 的身份被匿名化，这样 LLM 就不会在评判时偏袒某些模型。LLM 被要求根据准确性和洞察力对回答进行排名。
3. **阶段 3：最终答案**。指定的主席 LLM 综合所有模型的回答，编译成一个最终答案呈现给用户。

## 容错与回退机制（最新）

- **固定模型优先 + 软回退**：对话创建时会分配固定模型；若固定模型不健康或调用失败，会回退到候选池中更快的模型（不更新固定分配）。
- **400 错误分类**：请求错误（如 `context_length_exceeded` / `invalid_request`）不回退；模型错误或未知 400 会回退。
- **阶段截止时间**：Stage1/Stage2/Stage3 默认 180s，总时限内已完成的结果会立即流式返回。

## ⚠️ 免责声明

这个项目是一个实验性的 "Vibe Code" 项目，用于并排探索和评估多个 LLM。代码按原样提供，仅供参考。

## 安装配置

### 1. 安装依赖

本项目使用 [uv](https://docs.astral.sh/uv/) 进行 Python 依赖管理，使用 npm 管理前端依赖。

**后端：**
```bash
uv sync
```

**前端：**
```bash
cd frontend
npm install
cd ..
```

### 2. 配置 API Key

本项目使用 **OpenRouter** 作为模型服务提供商。

在项目根目录创建 `.env` 文件：

```bash
OPENROUTER_API_KEY=sk-or-v1-...
```

你可以在 [OpenRouter](https://openrouter.ai/keys) 获取你的 API key。

### 3. 配置模型（可选）

编辑 `backend/config.py` 自定义委员会成员和主席模型：

```python
# Councilor 配置（示例）
COUNCILORS = [
    {
        "id": "immanuel_kant",
        "name": "康德",
        "model": "xiaomi/mimo-v2-flash:free",  # 首选模型
        "model_candidates": [                   # 回退候选列表
            "xiaomi/mimo-v2-flash:free",
            "nvidia/nemotron-nano-9b-v2:free",
            # ...
        ],
        # ...
    },
]

# 主席配置
CHAIRMAN = {
    "id": "chairman",
    "name": "共识主席",
    "model": "xiaomi/mimo-v2-flash:free",
    # ...
}
```

更多可用的模型 ID，请查看 [OpenRouter Models 页面](https://openrouter.ai/models)。

## 运行应用

**方式 1：使用启动脚本 (推荐)**
```bash
./start.sh
```

**方式 2：手动运行**

终端 1（后端）：
```bash
uv run python -m backend.main
```

终端 2（前端）：
```bash
cd frontend
npm run dev
```

然后在浏览器中打开 `http://localhost:5173`。

## 测试与验证脚本

为了方便调试和验证环境，相关的测试脚本已整理至 `tests/` 目录：

| 脚本文件 | 描述 |
| :--- | :--- |
| `tests/check_main_import.py` | **导入检查**：验证 `backend.main` 模块是否可以被正确导入，用于排查路径或依赖问题。 |
| `tests/debug_models.py` | **模型调试**：详细测试配置文件中所有模型的连通性，并将结果输出到日志文件。 |
| `tests/test_minimal.py` | **环境测试**：最简化的 Python 环境测试脚本，用于验证解释器是否工作正常。 |
| `tests/verify_openrouter.py` | **API 验证**：简单验证 OpenRouter API Key 是否有效，尝试调用主席模型并打印响应。 |
| `tests/verify_rotation.py` | **轮换逻辑验证**：测试模型轮换（Rotation）算法，确保当首选模型不可用时能自动切换到备选模型。 |
| `tests/*.log` | 上述脚本运行产生的日志文件。 |

运行测试脚本示例：
```bash
uv run python tests/verify_openrouter.py
```

## Docker 部署（生产环境）

### 快速部署

1. **构建并启动：**
```bash
./deploy.sh
```
或者手动：
```bash
cd frontend && npm install && npm run build && cd ..
docker-compose up -d
```

2. **停止服务：**
```bash
docker-compose down
```

### 数据持久化

对话数据以 JSON 格式存储在 `./data/conversations/` 目录中。

## 技术栈

- **后端：** FastAPI, Python 3.10+, OpenRouter API
- **前端：** React + Vite, TailwindCSS
- **管理：** uv (Python), npm (Node.js)
