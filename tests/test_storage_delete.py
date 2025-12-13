
import unittest
import os
import sys
import shutil
import tempfile
from unittest.mock import patch, MagicMock

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import storage
from storage import delete_conversation, bulk_delete_conversations, validate_conversation_id

class TestStorageDelete(unittest.TestCase):
    def setUp(self):
        # Create a temp directory for data
        self.test_dir = tempfile.mkdtemp()
        self.patcher = patch('storage.DATA_DIR', self.test_dir)
        self.patcher.start()
        storage.ensure_data_dir()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.test_dir)

    def create_dummy_conversation(self, cid):
        path = os.path.join(self.test_dir, f"{cid}.json")
        with open(path, 'w') as f:
            f.write('{}')
        return path

    def test_validate_conversation_id(self):
        self.assertTrue(validate_conversation_id("valid-id_123"))
        self.assertFalse(validate_conversation_id("invalid id")) # Space
        self.assertFalse(validate_conversation_id("../path")) # Traversal
        self.assertFalse(validate_conversation_id("")) # Empty
        self.assertFalse(validate_conversation_id("a" * 100)) # Too long

    def test_delete_conversation_success(self):
        cid = "test_del_1"
        path = self.create_dummy_conversation(cid)
        self.assertTrue(os.path.exists(path))
        
        result = delete_conversation(cid)
        self.assertTrue(result)
        self.assertFalse(os.path.exists(path))

    def test_delete_conversation_idempotent(self):
        cid = "test_del_nonexist"
        # Should return True even if file doesn't exist
        result = delete_conversation(cid)
        self.assertTrue(result)

    def test_delete_conversation_invalid(self):
        cid = "bad/id"
        result = delete_conversation(cid)
        self.assertFalse(result)

    def test_bulk_delete_mixed(self):
        # existing
        cid1 = "id1"
        self.create_dummy_conversation(cid1)
        # non-existing
        cid2 = "id2"
        # invalid
        cid3 = "bad id"
        
        result = bulk_delete_conversations([cid1, cid2, cid3])
        
        self.assertIn("id1", result["deletedIds"]) # Deleted
        self.assertIn("id2", result["deletedIds"]) # "Success" (idempotent)
        
        failed = result["failed"]
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]["id"], "bad id")
        self.assertEqual(failed[0]["reason"], "invalid_id")
        
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, f"{cid1}.json")))

    @patch('os.remove')
    def test_bulk_delete_os_error(self, mock_remove):
        cid = "locked_id"
        self.create_dummy_conversation(cid)
        
        # Simulate PermissionError (a subclass of OSError)
        mock_remove.side_effect = PermissionError("Access denied")
        
        result = bulk_delete_conversations([cid])
        
        self.assertEqual(len(result["deletedIds"]), 0)
        self.assertEqual(len(result["failed"]), 1)
        self.assertEqual(result["failed"][0]["id"], cid)
        # Check if reason maps correctly (PermissionError -> EACCES implied or handled)
        # In typical python, PermissionError has errno.EACCES
        self.assertIn(result["failed"][0]["reason"], ["permission_denied", "os_error"])

if __name__ == '__main__':
    unittest.main()
