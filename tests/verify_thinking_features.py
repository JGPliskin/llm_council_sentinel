import sys
import os
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock, patch

# Add backend to path
# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from main import app, SendMessageRequest, send_message_stream
from council import _request_stage1_bounded, stage1_collect_responses

async def mock_stream_model(*args, **kwargs):
    """Mock for council.stream_model that simulates thinking events."""
    on_thinking = kwargs.get('on_thinking')
    if on_thinking:
        # Simulate thinking output
        await on_thinking("Thinking process started...")
        await on_thinking("Analyzing request...")
    
    return {
        "content": '{"councilor_id": "test", "status": "ok", "answer_markdown": "Test Answer"}', 
        "model": "test-model"
    }

async def test_thinking_propagation():
    print("--- Testing Thinking Toggle Propagation ---")
    
    # 1. Test _request_stage1_bounded prompt injection
    print("\n[1] Testing _request_stage1_bounded prompt injection...")
    
    mock_councilor = {
        "id": "test_id", 
        "name": "Test", 
        "model": "test-model", 
        "persona_path": "test_persona.txt"
    }
    
    # Mock dependencies
    with patch('council.fetch_persona', return_value="System Prompt"), \
         patch('council.model_concurrency_manager.get_semaphore', return_value=AsyncMock()), \
         patch('council.stream_model', side_effect=mock_stream_model) as mock_stream, \
         patch('council.GLOBAL_MODEL_MAP', {"test-model": {"capabilities": {"thinking": True}}}), \
         patch('council.health_manager.update_status'):

        # Case A: enable_thinking = True
        print("  Running with enable_thinking=True...")
        semaphore = asyncio.Semaphore(1)
        await _request_stage1_bounded(
            semaphore, 
            mock_councilor, 
            "Test Query", 
            on_thinking=AsyncMock(), 
            enable_thinking=True
        )
        
        # Verify prompt contained instruction
        call_args = mock_stream.call_args
        model_messages = call_args[0][1] # arg 1 is messages
        system_content = model_messages[0]['content']
        
        if "MUST call the `emit_thinking` tool" in system_content:
            print("  ✅ PASS: Prompt contained thinking instruction.")
        else:
            print("  ❌ FAIL: Prompt missing thinking instruction.")
            print(f"  Prompt snippet: {system_content[-100:]}")

        # Case B: enable_thinking = False
        print("  Running with enable_thinking=False...")
        await _request_stage1_bounded(
            semaphore, 
            mock_councilor, 
            "Test Query", 
            on_thinking=AsyncMock(), 
            enable_thinking=False
        )
        
        call_args_2 = mock_stream.call_args
        model_messages_2 = call_args_2[0][1]
        system_content_2 = model_messages_2[0]['content']
        
        if "MUST call the `emit_thinking` tool" not in system_content_2:
            print("  ✅ PASS: Prompt correctly excluded thinking instruction.")
        else:
            print("  ❌ FAIL: Prompt contained unexpected thinking instruction.")

async def test_api_integration():
    print("\n\n--- Testing API Integration (Mocked) ---")
    # This is harder to test fully without setting up the full app context with storage
    # But we can check the request model
    
    from main import SendMessageRequest
    r = SendMessageRequest(content="test")
    print(f"  Default enable_thinking: {r.enable_thinking}")
    if r.enable_thinking is True:
        print("  ✅ PASS: Default is True")
    else:
        print("  ❌ FAIL: Default incorrect")
        
    r2 = SendMessageRequest(content="test", enable_thinking=False)
    print(f"  Explicit enable_thinking=False: {r2.enable_thinking}")
    if r2.enable_thinking is False:
        print("  ✅ PASS: Explicit False respected")
    else:
         print("  ❌ FAIL: Explicit False ignored")

if __name__ == "__main__":
    asyncio.run(test_thinking_propagation())
    asyncio.run(test_api_integration())
