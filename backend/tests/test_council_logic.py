import pytest
import sys
import os
import json

# Add project root to path (one level up from backend)
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# Add backend to path (for direct imports if needed, though 'from backend' is preferred)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from council import strip_json_fences, _build_stage2_candidates

class TestCouncilLogic:
    
    def test_strip_json_fences(self):
        # Case 1: Standard markdown
        text = "```json\n{\"foo\": \"bar\"}\n```"
        assert json.loads(strip_json_fences(text)) == {"foo": "bar"}
        
        # Case 2: Plain text
        text = '{"foo": "bar"}'
        assert json.loads(strip_json_fences(text)) == {"foo": "bar"}
        
        # Case 3: With commentary
        text = "Here is the json:\n```json\n{\"a\":1}\n```\nThanks."
        assert json.loads(strip_json_fences(text)) == {"a": 1}

    def test_build_stage2_candidates(self):
        results = [
            {
                "councilor_id": "c1",
                "status": "ok",
                "answer_markdown": "Answer A"
            },
            {
                "councilor_id": "c2",
                "status": "failed",
                "answer_markdown": "Should ignore"
            }
        ]

        candidates, anon_map = _build_stage2_candidates(results)

        assert len(candidates) == 1
        assert candidates[0]["payload"]["answer_markdown"] == "Answer A"
        assert anon_map["anon_1"] == "c1"
