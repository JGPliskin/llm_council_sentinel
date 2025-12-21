# Thinking Title Stream Implementation Plan

## Goal Description
为支持 Reasoning 能力的模型（如 DeepSeek-R1）添加“流式思考过程”展示。
通过 Tool Call 实时输出思考步骤，在前端以“浮动状态指示器”呈现，提升用户等待期间的体验。
同时兼容不支持该功能的模型，并允许用户通过开关控制。

## User Review Required
> [!IMPORTANT]
> **Configuration Change**: 将在 `backend/config.py` 中为 `GLOBAL_MODEL_POOL` 添加 `features: ["thinking"]` 标记，用于自动识别是否启用思考工具。默认将 "category": "reasoning" 的模型标记为支持。

> [!NOTE]
> **Persistence Strategy**: 用户的前端开关状态将保存在浏览器的 `localStorage` 中，后端不存储相关设置。

## Proposed Changes

### Backend Configuration
#### [MODIFY] [config.py](file:///f:/OneDrive/PY/ZYZ/project/llm_council_sentinel/backend/config.py)
- 更新 `GLOBAL_MODEL_POOL`，为 reasoning 类模型添加 `features=["thinking"]` 属性。
- (Optionally) 在 `COUNCILORS` 中允许覆盖此配置。

### Backend Core
#### [MODIFY] [openrouter.py](file:///f:/OneDrive/PY/ZYZ/project/llm_council_sentinel/backend/openrouter.py)
- 重构 `query_model` 支持 `stream=True` 参数。
- 实现 `query_model_stream` generator，能同时 yield `ThinkingEvent` (Tool calls) 和积攒 `Content` (Final Answer)。
- 处理 JSON 分片缓冲 (Buffering) 逻辑，确保 `emit_thinking_title` 的 arguments 被完整解析后再 yield。

#### [MODIFY] [council.py](file:///f:/OneDrive/PY/ZYZ/project/llm_council_sentinel/backend/council.py)
- `_request_stage1_bounded`: 注入 `emit_thinking_title` tool definition（如果模型支持且开关开启）。
- `stage1_collect_responses`: 
    - 改用 `asyncio.as_completed` 或 `Queue` 模式。
    - 接收来自 `query_model_stream` 的实时事件，并通过 callback (`on_result`) 转发给 `main.py`。
    - 保持最终返回值为完整 JSON，不破坏后续 Stage 2 逻辑。

#### [MODIFY] [main.py](file:///f:/OneDrive/PY/ZYZ/project/llm_council_sentinel/backend/main.py)
- `event_generator`: 
    - 定义新的 SSE 事件类型: `stage1_thinking`。
    - 监听 Stage 1 的实时流，并广播给前端。
- API Endpoint: 接收前端传来的 `enable_thinking` 开关参数。

### Frontend
#### [MODIFY] [api.js](file:///f:/OneDrive/PY/ZYZ/project/llm_council_sentinel/frontend/src/api.js)
- 更新 `sendMessageStream` 支持处理 `stage1_thinking` 事件。
- 在请求 Body 中携带 `enableThinking` 参数。

#### [MODIFY] [App.jsx](file:///f:/OneDrive/PY/ZYZ/project/llm_council_sentinel/frontend/src/App.jsx)
- 添加 "Thinking Process" Toggle Button (保存至 localStorage)。
- 传递 `showThinking` 状态给 `ChatInterface`。

#### [MODIFY] [Stage1.jsx](file:///f:/OneDrive/PY/ZYZ/project/llm_council_sentinel/frontend/src/components/Stage1.jsx) (Assume exists, or similar)
- 实现 **Floating Indicator** (浮动指示器)。
- 逻辑：接收到 `stage1_thinking` 事件 -> 更新对应 Councilor 的状态 -> 显示 "Thinking: [Title]" -> 收到 `stage1_item` (Answer) 后 -> 冻结/隐藏。

## Verification Plan

### Automated Tests
- **Script**: `tests/test_thinking_stream.py` (New)
    - 模拟 `query_model_stream` 返回分片的 JSON Tool Calls。
    - 验证 Buffer 逻辑能否正确拼合完整 Tile。
    - 验证 Content 能够被完整累积。

### Manual Verification
1. **Config Test**: 
    - 确保只有配置了 "features: ['thinking']" 的模型（如 DeepSeek）才会触发 Tool Call。
2. **UI Test**:
    - 开启 Toggle -> 发送消息 -> 观察头像上方是否出现浮动 Title -> 观察是否每 3-5 秒更新。
    - 关闭 Toggle -> 发送消息 -> 确认无浮动 Title，且回答正常显示。
3. **Resilience**:
    - 模拟网络卡顿（延迟 SSE），验证 Filler 是否出现（如果实现了前端 Filler）。
