# NIM API 集成技术设计方案 (Status: Implemented)

> **Implementation Note (2026-01-18)**:  
> 本设计已完全落地。实际实现中包含以下关键调整：
> 1. **智能容错**：`nim.py` 实现了 `_looks_like_emit_thinking` 启发式逻辑，解决了 DeepSeek V3.1 偶尔返回 `name: null` 导致的显示延迟问题。
> 2. **Provider前缀**：系统严格遵循 `nim:` 和 `openrouter:` 前缀规范。
> 3. **总结模型**：新增了 `SUMMARY_MODEL_CANDIDATES` 用于会话标题生成。
> 4. **超时与Deadline**：`STAGE1_DEADLINE` 和 `STAGE2_DEADLINE` 最终定为 180s（而非设计初期的禁用）。


## 1. 概述 (Overview)

本项目旨在将 NVIDIA NIM API 集成到现有的 LLM Council Sentinel 后端中，作为第二大模型服务提供商。通过引入 NIM，系统将支持 OpenRouter 和 NIM 双供应商轮替，提高系统的可用性和模型多样性，重点引入 DeepSeek V3.1 等模型。

本次集成的核心原则是**业务层无感知**：通过抽象层屏蔽底层供应商差异，保持上层 `council.py` 等业务逻辑的稳定性。

## 2. 用户场景与需求 (User Scenarios & Requirements)



### 2.1 核心需求
1.  **双供应商支持**：系统需同时支持 OpenRouter 和 NVIDIA NIM。
2.  **混合轮替**：在同一个 Councilor 的候选池（`model_candidates`）中，可以混合配置 OpenRouter 模型和 NIM 模型。
3.  **显式路由为主**：主要通过配置中的 `provider` 字段区分供应商。
    **前缀路由补充**：统一使用前缀避免歧义：
    *   `nim:` 表示 NVIDIA NIM
    *   `openrouter:` 表示 OpenRouter
4.  **多 Key 管理与限流**：
    *   NIM API 有严格的 RPM 限制（每 Key 每分钟 40 次）。
    *   **策略优化**：Key 限速不应影响模型健康状态。
    *   **限制**：采用进程内（In-Process）限速方案。对于多 Worker/多实例部署，当前方案不能保证全局 RPM 精确控制（需在文档中明确告知）。
5.  **Thinking 展示策略（NIM 仅 Tool 模式）**：
    *   NIM 侧只使用 `tool calling`（`emit_thinking`）来输出思考过程。
    *   **不启用** prompt 解析或 native reasoning 的兜底模式，避免复杂度和语义不一致。
    *   Stage2 的 `emit_thinking` 必须包含 `target_anon_id`，否则前端不展示该条 thinking。

### 2.2 关键技术指标
*   **模型标识**：
    *   **推荐**：在 `GLOBAL_MODEL_POOL` 中显式配置 `"provider"` 字段。
    *   **前缀约束**：所有 OpenRouter 模型统一加 `openrouter:` 前缀，所有 NIM 模型统一加 `nim:` 前缀。
    *   **兼容**：保留 `nim:` / `openrouter:` 前缀解析，用于 Ad-hoc 场景。
*   **配置方式**：API Keys 通过环境变量 `NIM_API_KEYS`（逗号分隔）配置。新增 `NIM_RPM_PER_KEY` 配置项（默认 40）。可选 `NIM_API_BASE`（默认 `https://integrate.api.nvidia.com/v1`）。
*   **限流策略**：
    *   Key 级：Token Bucket (`NIM_RPM_PER_KEY` RPM)。
*   **Provider 级回退**：当所有 Key 耗尽时，返回特定错误码（如 `provider_rate_limited`），触发业务层快速失败或重试其他候选模型，**但不标记模型为不健康**。
*   **Tool Calling 约束**：
    *   NIM 侧只走 `tool_choice` + `tools` 的标准流程。
    *   如果 NIM 返回中缺少 `tool_calls`，系统不会尝试 prompt/native 兜底，仅展示最终回答（无 thinking）。


## 3. 技术架构 (Architecture)

引入新的中间抽象层 `llm_client.py`，负责请求路由。

### 3.1 架构数据流图

```mermaid
graph TD
    User[用户] --> Main[main.py]
    Main --> Council[council.py <br/> 业务编排]
    
    subgraph "抽象路由层 (Abstraction Layer)"
        Council -->|调用 stream_model| LLM_Client[llm_client.py <br/> 统一入口]
    end
    
    subgraph "供应商客户端 (Provider Clients)"
        LLM_Client -->|路由判断| Router{provider字段?}
        
        Router -->|provider=openrouter| OR_Client[openrouter.py]
        Router -->|provider=nim| NIM_Client[nim.py]
        Router -->|无字段| PrefixCheck{前缀 nim:/openrouter:?}
        PrefixCheck -->|nim:| NIM_Client
        PrefixCheck -->|openrouter:| OR_Client
        PrefixCheck -->|No| OR_Client[openrouter.py (Default)]
        
        subgraph "NIM 内部模块"
            NIM_Client --> KeyMgr[NIMKeyManager]
        end
    end
    
    subgraph "External APIs"
        OR_Client --> OR_API[OpenRouter API]
        NIM_Client --> NIM_API[NVIDIA NIM API]
    end

    style LLM_Client fill:#f9f,stroke:#333,stroke-width:2px
    style NIM_Client fill:#bbf,stroke:#333,stroke-width:2px
```

### 3.2 模块职责
*   **`llm_client.py` (新增)**: 
    *   系统的统一 LLM 调用入口。
    *   负责路由分发：**严格优先级**：`config.provider` > `prefixed model_id` > Default (OpenRouter)。
    *   负责去掉 `nim:` / `openrouter:` 前缀后再调用对应客户端。
    *   统一规范不同客户端的返回格式。
*   **`nim.py` (新增)**:
    *   封装 NVIDIA NIM API 的调用逻辑。
    *   内置 `NIMKeyManager` 处理多 Key 轮替和限流。
    *   **仅处理 tool_calls 形式的 thinking**，不启用 native/prompt 解析分支。
*   **`openrouter.py` (现有)**:
    *   保持现状，负责 OpenRouter API 调用。

## 4. 详细技术方案 (Detailed Design)

### 4.1 模型标识与配置

**Model ID 规范**：
系统将优先使用 `GLOBAL_MODEL_POOL` 中的 `provider` 字段进行路由。
*   OpenRouter 模型：`"provider": "openrouter"` (默认)
*   NIM 模型：`"provider": "nim"`

**Model ID 兼容性**：
为了保持既有习惯和方便测试，`llm_client` 也会检查 `model_id` 字符串：
*   如果缺少配置但以 `nim:` 开头 -> 视为 NIM 模型。
*   如果缺少配置但以 `openrouter:` 开头 -> 视为 OpenRouter 模型。

**配置文件 (`config.py`)**:
*   新增 `NIM_API_KEYS` 读取逻辑。
*   更新 `GLOBAL_MODEL_POOL`，添加 NIM 模型定义（显式指定 provider）。

**NIM 模型配置示例**:
```python
{
    "id": "nim:deepseek-ai/deepseek-v3.1",  # 明确前缀避免歧义
    "name": "DeepSeek V3.1 (NIM)",
    "provider": "nim",                  # 核心路由字段
    "capabilities": {
        "thinking": True,
        "mode": "tool"                  # NIM 仅走 tool calling
    },
    "concurrency_limit": 3,
    "category": "reasoning",
}
```
*(注：所有模型 ID 均需带前缀，例如 `nim:deepseek-ai/deepseek-v3.1` 或 `openrouter:deepseek-ai/deepseek-v3.1`)* 

### 4.2 Key 管理与限流 (`nim.py`)

实现 `NIMKeyManager` 类：

1.  **Key Pool**: 维护所有配置的 Key 及其状态（Bucket）。
2.  **Token Bucket**: 每个 Key 独立维护一个令牌桶。
    *   `capacity`: NIM_RPM_PER_KEY (或配置值)
    *   `refill_rate`: NIM_RPM_PER_KEY / 60.0 (每秒恢复令牌数)
3.  **Key 选择策略 (`acquire_key`)**:
    *   过滤掉处于临时冷却（因 429/401）的 Key。
    *   过滤掉令牌不足的 Key。
    *   **选择剩余令牌最多**的 Key（负载均衡）。
    *   若无可用 Key，**快速失败**，返回 `provider_rate_limited` 错误码。

**并发控制**:
*   沿用现有的 Per-Model 信号量控制（`council.py` 内的 `ModelConcurrencyManager`），不再引入全局 NIM Semaphore，避免死锁风险和逻辑冲突。

**Rate Limit 保护**:
*   当 `nim.py` 返回 `provider_rate_limited` 时，上层业务逻辑应重试其他候选模型（如有），**但不触发 HealthManager 的模型冷却**。
*   这样即使所有 Key 耗尽，模型本身仍被视为 "Healthy" (但在当前请求中不可用)，避免影响后续请求的选择（如果 Key 恢复）。

**provider_rate_limited 行为矩阵**：

| 场景 | 处理策略 | 是否更新 Health |
|---|---|---|
| 单个 Key 429 | 同模型内轮换其他 Key | 否 |
| 全部 Key 耗尽 | 返回 `provider_rate_limited` | 否 |
| 收到 `provider_rate_limited` | 回退到其他候选模型 | 否 |

### 4.3 统一输出格式

为了让 `council.py` 无缝处理，`nim.py` 的 `stream_model` 必须输出与 `openrouter.py` 一致的结构字典：

```python
{
    "content": "...",           # 累积的最终回答
    "thinking_content": "...",  # 可选：由 tool_calls 组装的思考摘要（非必需）
    "provider": "nim",          # "nim" / "openrouter"
    "model": "...",             # 实际响应模型
    "ttft_ms": 1234,            # 首 Token 延迟
    "error": False,             # 是否出错
    "error_code": None,         # 例如 "provider_rate_limited"
    # ...
}
```

**NIM 请求参数约束**:
*   `tools` 固定为 `emit_thinking` 定义。
*   `tool_choice` 设置为 `auto`（由模型决定触发时机）。

**Stream 处理逻辑**:
*   监听 `chunk.choices[0].delta.tool_calls` -> 解析 `emit_thinking` 参数并触发 `on_thinking` 回调。
*   若 `tool_calls` 为空或不可解析，**不启用任何 prompt/native 兜底**（保持 tool-only 简化策略）。
*   监听 `chunk.choices[0].delta.content` -> 累积到 `content` 并触发 `on_content` 回调。

**Stage2 `target_anon_id` 处理**:
*   Stage2 system prompt 强制要求每次 `emit_thinking` 都带 `target_anon_id`（如 `anon_1`）。
*   后端对 `title/detail` 做轻量正则兜底（匹配 `anon_\\d+`），用于补齐缺失字段。
*   若仍缺失 `target_anon_id`，该 thinking 事件直接丢弃，避免错误映射到评审对象。

3.  **错误处理对齐**:
    *   在 `nim.py` 中，所有的异常和错误状态码需映射为与 `openrouter.py` 一致的结构。
    *   特殊的 `provider_rate_limited` 错误需通过 `error_code` 字段传递，在 `council.py` 中被识别为 "Retryable" 或 "Failover" 信号，而不触发 Health 降级。

### 4.4 健康检测与路由改造

1.  **路由改造**:
    *   修改 `validation.py` 中的 `check_model_health_probe`，将直接调用 `openrouter.query_model` 改为调用 `llm_client.query_model`。
    *   修改 `council.py`，将直接导入 `openrouter` 改为导入 `llm_client`。

2.  **健康策略**:
    *   **Runtime Feedback**: 依赖实际请求的反馈。
    *   **探测对齐**: 当前实现默认沿用现有“全量刷新”策略（包含 NIM 模型），**不跳过 NIM 主动探测**。
    *   **启动强制刷新**: 服务启动时执行一次 `refresh_council_health()` 全量探测，**不受时间窗口限制**；后续仍按定时窗口执行周期性刷新。
    *   **HealthManager**：移除对 429 的特殊短冷却处理，保持其只关注 "模型是否可用" 而非 "配额是否足够"。

## 5. 初始双供应商模型列表

以下模型将作为首批支持加入 `GLOBAL_MODEL_POOL`：
_(注：为避免供应商歧义，NIM 模型统一使用 `nim:` 前缀，OpenRouter 模型统一使用 `openrouter:` 前缀)_

**NIM (nim:)**
1.  `nim:deepseek-ai/deepseek-v3.1`
2.  `nim:deepseek-ai/deepseek-v3.1-terminus`
3.  `nim:openai/gpt-oss-120b`
4.  `nim:z-ai/glm4.7`

**OpenRouter (openrouter:)**
*   沿用现有 OpenRouter 模型清单，仅统一添加 `openrouter:` 前缀（不在本文重复列出）。

**Chairman 模型策略**：与上述 NIM 模型列表保持一致，不再单独引入 `minimaxai/minimax-m2.1`。

## 6. 改动文件清单 (Impact Analysis)

| 文件路径 | 类型 | 描述 |
|---|---|---|
| `backend/llm_client.py` | **NEW** | 路由抽象层，统一 stream_model/query_model 入口 |
| `backend/nim.py` | **NEW** | NIM 客户端实现，包含 KeyManager 和 API 调用逻辑 |
| `backend/config.py` | **MOD** | 新增 NIM_API_KEYS 配置，更新 GLOBAL_MODEL_POOL |
| `backend/council.py` | **MOD** | 替换 openrouter 导入为 llm_client |
| `backend/validation.py` | **MOD** | 替换 openrouter 导入为 llm_client，适配 probing |
| `backend/model_assigner.py` | **No Change** | 逻辑通用，无需修改（仅需确保 config 正确） |
| `backend/openrouter.py` | **Refactor** | (可选) 可能需要微调导出接口以保持一致性 |

## 7. 实施计划 (Implementation Roadmap)

1.  **Phase 1: 基础设施 (Infrastructure)**
    *   创建 `llm_client.py`。
    *   创建 `nim.py` 骨架及 KeyManager 基础逻辑。
    *   更新 `config.py`。
2.  **Phase 2: 客户端实现 (Client Logic)**
    *   完善 `nim.py` 的流式调用，实现 `tool_calls` 解析与 `emit_thinking` 透传。
    *   实现 Token Bucket 限流与 Key 轮替。
3.  **Phase 3: 集成与替换 (Integration)**
    *   替换 `validation.py` 和 `council.py` 中的调用。
    *   测试各 Provider 路由正确性。
4.  **Phase 4: 验证 (Verification)**
    *   验证 DeepSeek R1 的 Thinking 显示。
    *   验证 RPM 限流保护机制。
    *   验证 OpenRouter 与 NIM 的混合轮替。
