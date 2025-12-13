import unittest
import os
import json
import shutil
import tempfile
from unittest.mock import patch

# Add backend to path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

import storage

class TestStorageMigration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.patcher = patch("storage.DATA_DIR", self.temp_dir)
        self.patcher.start()
        # Storage expects 'conversations' subdir or handles it?
        # Typically storage.py appends 'conversations'. Ensure it exists if code assumes it.
        # Looking at storage.py, ensure_data_dir only creates DATA_DIR.
        # But get_conversation_path likely uses DATA_DIR/conversations/id.json.
        # Let's ensure 'conversations' exists in temp dir.
        os.makedirs(os.path.join(self.temp_dir, "conversations"), exist_ok=True)

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.temp_dir)

    def test_create_conversation_v2(self):
        """Test creating a conversation uses schema version 2."""
        conv = storage.create_conversation("test_v2", active_councilor_ids=["c1", "c2"])
        self.assertEqual(conv["schema_version"], 2)
        self.assertEqual(conv["active_councilor_ids"], ["c1", "c2"])
        
        # Verify file
        # storage.py writes to DATA_DIR/{id}.json (no subdir unless DATA_DIR has it)
        path = os.path.join(self.temp_dir, "test_v2.json")
        with open(path, 'r') as f:
            data = json.load(f)
            self.assertEqual(data["schema_version"], 2)

    def test_update_conversation_schema(self):
        """Test updating schema version."""
        # Create v1 style conversation manually
        path = os.path.join(self.temp_dir, "legacy.json")
        v1_data = {
            "id": "legacy",
            "active_models": ["model1"],
            "messages": []
        }
        with open(path, 'w') as f:
            json.dump(v1_data, f)
            
        # Update
        storage.update_conversation_schema("legacy", ["c1"], version=2)
        
        with open(path, 'r') as f:
            data = json.load(f)
            self.assertEqual(data["schema_version"], 2)
            self.assertEqual(data["active_councilor_ids"], ["c1"])
            self.assertIn("active_models", data)

if __name__ == '__main__':
    unittest.main()
