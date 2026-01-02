# Thinking Title Stream PoC

This script demonstrates the "Thinking Title Stream" UI pattern. It uses a protocol where the LLM emits "thinking titles" via tool calls during the inference process, providing a visual narration of its thoughts without exposing raw reasoning text.

## Features
*   **Narrated Thinking**: Real-time updates of "steps" the model is taking.
*   **Filler Mechanism**: "Looking up..." / "Thinking..." placeholders fill the gap before the first token (TTFB).
*   **Dual Channel Fallback**: Robustly handles cases where the model forgets to use tools and streams text directly.
*   **Rich UI**: Beautiful terminal output using `rich`.

## Prerequisites

1.  **Python 3.8+**
2.  **Dependencies**:
    ```bash
    pip install openai rich python-dotenv
    ```
3.  **OpenRouter API Key**:
    *   Create a `.env` file in the project root:
        ```env
        OPENROUTER_API_KEY=sk-or-your-key-here
        ```

## Usage

### 1. Robust Run (Recommended)
Use the isolated environment created for this project (bypasses global Anaconda issues):
```powershell
.\.venv\Scripts\python.exe thinking_stream_test.py --model "xiaomi/mimo-v2-flash:free"
```

### 2. Standard Run
If you have your global environment set up correctly:
```bash
python thinking_stream_test.py --model "xiaomi/mimo-v2-flash:free"
```

### Using Specific Models (Verified)

**Xiaomi Mimo V2 Flash** (Fast, Free)
```bash
python thinking_stream_test.py --model "xiaomi/mimo-v2-flash:free"
```

**TNG R1T Chimera** (Reasoning capable)
```bash
python thinking_stream_test.py --model "tngtech/tng-r1t-chimera:free" --question "Solve the strawberry problem: how many r's in strawberry?"
```

## Debugging

If you encounter issues or want to see raw logs:
```bash
python thinking_stream_test.py --debug
```

## How It Works (Status Machine)
1.  **Waiting**: Shows threaded "Filler" messages.
2.  **Thinking**: Listens for `emit_thinking_title` tool calls. Updates the list.
3.  **Answering**: Detects `emit_final` OR standard text content. Freezes the thinking panel and streams the answer.
