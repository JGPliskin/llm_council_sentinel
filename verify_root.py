import sys
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

# Append backend to path
sys.path.append(os.path.abspath('backend'))

try:
    from main import SendMessageRequest
    from council import _request_stage1_bounded
except ImportError as e:
    print(f"CRITICAL IMPORT ERROR: {e}")
    sys.exit(1)

async def mock_stream_model(*args, **kwargs):
    """Mock for council.stream_model that simulates thinking events."""
    on_thinking = kwargs.get('on_thinking')
    if on_thinking:
        await on_thinking("Thinking process started...")
    return {
        "content": '{"councilor_id": "test", "status": "ok", "answer_markdown": "Test Answer"}', 
        "model": "test-model"
    }

async def test_thinking_propagation():
    print("--- Testing Thinking Toggle Propagation ---")
    
    mock_councilor = {
        "id": "test_id", 
        "name": "Test", 
        "model": "test-model", 
        "persona_path": "test_persona.txt"
    }
    
    print(f"Mocking Dependencies...")
    with patch('council.fetch_persona', return_value="System Prompt"), \
         patch('council.model_concurrency_manager.get_semaphore', return_value=AsyncMock()), \
         patch('council.stream_model', side_effect=mock_stream_model) as mock_stream, \
         patch('council.select_best_model', return_value="test-model"), \
         patch('council.GLOBAL_MODEL_MAP', {"test-model": {"capabilities": {"thinking": True}}}), \
         patch('council.health_manager.update_status'):
         
        with open("results.txt", "w", encoding="utf-8") as f:
            f.write("--- Testing Thinking Toggle Propagation ---\n")
            
            # Case A: enable_thinking = True
            res = await _request_stage1_bounded(
                asyncio.Semaphore(1), mock_councilor, "Q", on_thinking=AsyncMock(), enable_thinking=True
            )
            
            call_args = mock_stream.call_args
            model_messages = call_args[0][1] 
            system_content = model_messages[0]['content']
            if "MUST call the `emit_thinking` tool" in system_content:
                f.write("  [A] PASS: Instruction Injected\n")
            else:
                f.write(f"  [A] FAIL: Instruction Missing\n")

            # Case B: enable_thinking = False
            res = await _request_stage1_bounded(
                asyncio.Semaphore(1), mock_councilor, "Q", on_thinking=AsyncMock(), enable_thinking=False
            )
            
            call_args_2 = mock_stream.call_args
            model_messages_2 = call_args_2[0][1]
            system_content_2 = model_messages_2[0]['content']
            if "MUST call the `emit_thinking` tool" not in system_content_2:
                f.write("  [B] PASS: Instruction Excluded\n")
            else:
                f.write("  [B] FAIL: Instruction STILL Present\n")
                
            f.write("\n--- Testing API Integration (Mocked) ---\n")
            r = SendMessageRequest(content="test")
            if r.enable_thinking is True:
                f.write("  [API] PASS: Default is True\n")
            else:
                f.write("  [API] FAIL: Default incorrect\n")

if __name__ == "__main__":
    asyncio.run(test_thinking_propagation())
