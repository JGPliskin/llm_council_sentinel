import pytest
import json
import asyncio
from unittest.mock import MagicMock, patch
import sys
# Mock httpx to avoid import errors with trio/python3.7
sys.modules["httpx"] = MagicMock()

async def async_return(result):
    return result

from backend.openrouter import stream_model

@patch('backend.openrouter.httpx', MagicMock()) # Double ensure patched
def test_stream_model_parsing_sync():
    """Sync wrapper for async test."""
    
    async def run_test():
        # Mock response chunks simulating a tool call
        mock_chunks = [
            # Chunk 1: Tool call start
            {
                "choices": [{
                    "delta": {
                        "tool_calls": [{
                            "index": 0,
                            "function": {
                                "name": "emit_thinking",
                                "arguments": "{\"title\": \"Analy"
                            },
                             "id": "call_123"
                        }]
                    }
                }]
            },
            # Chunk 2: Tool call continue
            {
                "choices": [{
                    "delta": {
                        "tool_calls": [{
                            "index": 0,
                            "function": {
                                "arguments": "zing Request\"}"
                            }
                        }]
                    }
                }]
            },
            {
                "choices": [{
                    "delta": {
                        "content": "Here is the answer."
                    }
                }]
            }
        ]

        # Mock AsyncClient
        mock_client = MagicMock()
        mock_response = MagicMock()
        
        # mimic aiter for streaming response
        async def chunk_generator():
            for chunk in mock_chunks:
                # aiter_lines yields strings, and SSE format usually has "data: " prefix
                yield f"data: {json.dumps(chunk)}"
                # Also yield empty line if openrouter consumes it, but aiter_lines usually splits by newline
                # So each yield is a line.

                
        mock_response.aiter_lines.return_value = chunk_generator()
        mock_response.status_code = 200
        
        # Setup async context manager for stream()
        mock_client.stream.return_value.__aenter__ = MagicMock(side_effect=lambda: async_return(mock_response))
        mock_client.stream.return_value.__aexit__ = MagicMock(side_effect=lambda *a, **k: async_return(None))

        # Setup async context manager for AsyncClient() itself
        mock_client.__aenter__ = MagicMock(side_effect=lambda: async_return(mock_client))
        mock_client.__aexit__ = MagicMock(side_effect=lambda *a, **k: async_return(None))

        thinking_payloads = []
        # Test both sync and async callbacks (backend supports both now)
        async def on_thinking(payload):
            thinking_payloads.append(payload)

        with patch('backend.openrouter.httpx.AsyncClient', return_value=mock_client), \
             patch('backend.openrouter.OPENROUTER_API_KEY', "test-key"):
            result = await stream_model(
                "test-model", 
                [{"role": "user", "content": "hi"}], 
                on_thinking=on_thinking,
                tools=[{"type": "function", "function": {"name": "emit_thinking"}}]
            )

        # Verify thinking callback was triggered
        assert thinking_payloads[0]["title"] == "Analyzing Request"
        assert result["content"] == "Here is the answer."

    asyncio.run(run_test())
