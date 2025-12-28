import pytest
import sys
import os
import json

# Add project root to path (one level up from backend)
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# Add backend to path (for direct imports if needed, though 'from backend' is preferred)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from council import strip_json_fences, enforce_judge_card_constraints, parse_stage1_json

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

    def test_enforce_judge_card_constraints_padding(self):
        # Input with insufficient items
        input_card = {
            "stance": "Support",
            "core_reasons": ["Reason 1"]
        }
        
        processed = enforce_judge_card_constraints(input_card)
        
        # Should pad to at least 2
        assert len(processed["core_reasons"]) >= 2
        assert "补充要点" in processed["core_reasons"][1]

    def test_enforce_judge_card_constraints_truncation(self):
        # Input with long items
        long_str = "A" * 100
        input_card = {
            "stance": "Support",
            "core_reasons": [long_str, "Reason 2"],
            "assumptions": [long_str],
            "risks": [],
            "actionables": []
        }
        
        processed = enforce_judge_card_constraints(input_card)
        
        # Check truncation (default 50 chars in function, or logic?)
        # Current logic: `truncate_item(text, limit=50)` called in loop
        assert len(processed["core_reasons"][0]) <= 50
        assert len(processed["assumptions"][0]) <= 50
        
        # Total length check (<= 600 chars serialize)
        serialized = json.dumps(processed, ensure_ascii=False)
        assert len(serialized) <= 600

    def test_parse_stage1_json(self):
        raw = """
        {
            "answer_markdown": "Test Answer",
            "judge_card": {
                "stance": "Neutral",
                "core_reasons": ["R1", "R2"]
            }
        }
        """
        parsed = parse_stage1_json(raw)
        assert parsed["answer_markdown"] == "Test Answer"
        assert parsed["judge_card"]["stance"] == "Neutral"
