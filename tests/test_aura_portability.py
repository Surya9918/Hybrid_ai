"""
AURA Companion - Test Suite for AURA OS Portability & Platform Decoupling (Section 11)
Verifies:
1. Core logic executes independently without Win32 or Windows App SDK dependencies.
2. AURA OS adapter interface contracts match core expectations.
3. System capabilities are queried gracefully without false claims of implementation.
"""

import unittest
from src.aura_runtime.platform.aura_os_adapter import AuraOsPlatformAdapter
from src.aura_runtime.platform.contracts import IPlatformAdapter
from src.aura_runtime.storage.db import DatabaseManager
from src.aura_runtime.tasks.task_manager import TaskManager
from src.aura_runtime.tools.registry import ToolRegistry
from src.aura_runtime.tools.builtin_tools import register_all_builtin_tools
from src.aura_runtime.tasks.reminder_manager import ReminderManager
from src.aura_runtime.memory.memory_store import MemoryStore
from src.aura_runtime.tools.engine import AgenticExecutionEngine
from src.aura_runtime.tools.schema import ToolExecutionRequest, ExecutionState


class TestAuraPortability(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager(":memory:")
        self.task_manager = TaskManager(self.db)
        self.reminder_manager = ReminderManager(self.db)
        self.memory_store = MemoryStore(self.db)
        self.aura_adapter = AuraOsPlatformAdapter()

        self.registry = ToolRegistry()
        register_all_builtin_tools(
            self.registry,
            self.aura_adapter,
            self.task_manager,
            self.reminder_manager,
            self.memory_store,
        )
        self.engine = AgenticExecutionEngine(self.registry)

    def tearDown(self):
        self.db.close()

    def test_aura_os_adapter_contract_conformance(self):
        # Must implement abstract interface IPlatformAdapter
        self.assertIsInstance(self.aura_adapter, IPlatformAdapter)

    def test_graceful_handling_of_pending_kernel_services(self):
        # AURA OS microkernel hasn't implemented process spawn yet
        req = ToolExecutionRequest(
            request_id="req_aura_001",
            tool_name="open_app",
            arguments={"app_name": "aura-terminal"},
        )
        res = self.engine.execute_request(req)
        self.assertTrue(res.success)
        self.assertFalse(res.output.get("launched"))
        self.assertIn("aura.proc.spawn", res.output.get("message"))

    def test_shared_core_platform_neutrality(self):
        # Memory, tasks, and state machine execute with zero Windows APIs
        tid = self.task_manager.create_task("Compile AURA kernel on RISC-V")
        self.assertIsNotNone(self.task_manager.get_task(tid))
        self.memory_store.add_memory("AURA OS microkernel architecture reference")
        self.assertEqual(len(self.memory_store.search("microkernel")), 1)


if __name__ == "__main__":
    unittest.main()
