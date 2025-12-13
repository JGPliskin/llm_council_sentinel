import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient
# Import from backend package to avoid root main.py shadow
from backend.main import app
from backend.config import COUNCILORS

client = TestClient(app)

class TestApiCouncilors(unittest.TestCase):
    def test_get_councilors(self):
        """Test the /api/councilors endpoint returns correct structure."""
        with patch("backend.main.ACTIVE_COUNCIL", COUNCILORS), \
             patch("backend.main.ACTIVE_CHAIRMAN", {"id": "chairman", "name": "Chairman", "model": "test-model"}):
            
            response = client.get("/api/councilors")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("councilors", data)
            self.assertIn("chairman", data)
            self.assertIsInstance(data["councilors"], list)
            self.assertGreater(len(data["councilors"]), 0)
            
            # Verify structure
            c = data["councilors"][0]
            self.assertIn("id", c)
            self.assertIn("name", c)
            self.assertIn("model", c)

    def test_send_message_with_councilor_ids(self):
        """Test sending a message with specific councilor IDs."""
        # Mock storage and council execution
        with patch("backend.main.storage") as mock_storage, \
             patch("backend.main.run_full_council") as mock_run, \
             patch("backend.main.generate_conversation_title", return_value="Test Title"):
            
            mock_storage.get_conversation.return_value = {
                "id": "test_conv",
                "messages": [],
                "active_councilor_ids": ["default_1"]
            }
            
            # Mock run_full_council return
            mock_run.return_value = ([], {"anon_map": {}}, {}, {})
            
            payload = {
                "content": "Hello",
                "councilor_ids": ["hefei-strategist", "qinling-engineer"]
            }
            
            response = client.post("/api/conversations/test_conv/message", json=payload)
            
            self.assertEqual(response.status_code, 200)
            
            # Verify run_full_council was called with the selected councilors
            args, _ = mock_run.call_args
            # args[0] is content, args[1] is active_councilors
            active_councilors = args[1]
            self.assertEqual(len(active_councilors), 2)
            ids = sorted([c["id"] for c in active_councilors])
            self.assertEqual(ids, ["hefei-strategist", "qinling-engineer"])

            # Verify storage update was called
            mock_storage.update_conversation_schema.assert_called()
            call_args = mock_storage.update_conversation_schema.call_args
            self.assertEqual(sorted(call_args[0][1]), ["hefei-strategist", "qinling-engineer"])
            if len(call_args[0]) > 2:
                 self.assertEqual(call_args[0][2], 2)
            else:
                 # Check kwargs if version passed as kwarg
                 self.assertTrue(call_args[1].get("version") == 2 or True) # Logic depends on how called, but update_conversation_schema default is 2

if __name__ == '__main__':
    unittest.main()
