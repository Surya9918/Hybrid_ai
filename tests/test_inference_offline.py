"""
AURA Companion - Test Suite for Inference, Offline Enforcement & Privacy
Verifies:
1. Local model execution without cloud credentials.
2. Hard network block in offline mode (Rule 9).
3. Truthful telemetry without fabricated NPU claims (Rule 14).
4. Sensitive clipboard history exclusion (API keys, JWT, passwords).
5. Memory wipe nuclear delete controls.
"""

import unittest
from src.aura_runtime.inference.router import ModelRouter, InferenceBackend
from src.aura_runtime.security.clipboard_filter import ClipboardPrivacyFilter
from src.aura_runtime.storage.db import DatabaseManager
from src.aura_runtime.memory.memory_store import MemoryStore
from src.aura_runtime.tasks.task_manager import TaskManager


class TestInferenceAndPrivacy(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager(":memory:")
        self.memory_store = MemoryStore(self.db)
        self.task_mgr = TaskManager(self.db)

    def tearDown(self):
        self.db.close()

    def test_local_inference_offline_enforcement(self):
        router = ModelRouter(offline_mode=True, hardware_has_npu=False)
        # Normal local request succeeds offline
        text, telemetry = router.generate_response("Hello AURA", allow_cloud=False)
        self.assertIn("AURA local response", text)
        self.assertEqual(telemetry.backend_used, InferenceBackend.CPU_LOCAL)
        self.assertFalse(telemetry.is_npu_accelerated)

        # Attempting cloud in offline mode raises PermissionError
        with self.assertRaises(PermissionError):
            router.generate_response("Process cloud query", allow_cloud=True)

    def test_truthful_npu_reporting(self):
        # On standard sandbox without verified NPU
        router_cpu = ModelRouter(offline_mode=True, hardware_has_npu=False)
        _, telemetry_cpu = router_cpu.generate_response("Test prompt")
        self.assertFalse(telemetry_cpu.is_npu_accelerated)
        self.assertEqual(telemetry_cpu.backend_used, InferenceBackend.CPU_LOCAL)

        # On target device with verified physical Snapdragon Hexagon NPU
        router_npu = ModelRouter(offline_mode=True, hardware_has_npu=True)
        _, telemetry_npu = router_npu.generate_response("Test prompt")
        self.assertTrue(telemetry_npu.is_npu_accelerated)
        self.assertEqual(telemetry_npu.backend_used, InferenceBackend.QUALCOMM_HEXAGON_NPU)

    def test_clipboard_sensitive_content_exclusion(self):
        # Normal content
        normal_text = "Meeting summary from architecture review"
        self.assertEqual(
            ClipboardPrivacyFilter.filter_text_for_history(normal_text),
            normal_text,
        )

        # API Key
        api_key_text = "sk-1234567890abcdef1234567890abcdef"
        filtered_key = ClipboardPrivacyFilter.filter_text_for_history(api_key_text)
        self.assertIn("[REDACTED", filtered_key)

        # Password assignment
        pwd_text = "password=SuperSecretPassword123!"
        filtered_pwd = ClipboardPrivacyFilter.filter_text_for_history(pwd_text)
        self.assertIn("[REDACTED", filtered_pwd)

        # Private Key
        priv_key = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0...\n-----END RSA PRIVATE KEY-----"
        filtered_pk = ClipboardPrivacyFilter.filter_text_for_history(priv_key)
        self.assertIn("[REDACTED", filtered_pk)

    def test_nuclear_delete_all_data(self):
        self.task_mgr.create_task("Task to delete")
        self.memory_store.add_memory("Secret meeting notes")

        # Verify items exist
        self.assertEqual(len(self.task_mgr.list_tasks()), 1)
        self.assertEqual(len(self.memory_store.search("meeting")), 1)

        # Execute wipe
        counts = self.memory_store.delete_all_data()
        self.assertEqual(counts["tasks"], 1)
        self.assertEqual(counts["memory_items"], 1)

        # Verify completely empty
        self.assertEqual(len(self.task_mgr.list_tasks()), 0)
        self.assertEqual(len(self.memory_store.search("meeting")), 0)


if __name__ == "__main__":
    unittest.main()
