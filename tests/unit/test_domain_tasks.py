from __future__ import annotations

import unittest
from unittest.mock import AsyncMock

from mcp_proxmox.domains.tasks import task_list, task_log, task_status
from mcp_proxmox.pve.models.responses import TaskListEntry, TaskLogEntry, TaskStatus


class MockPveClient:
    def __init__(self) -> None:
        self.get_tasks = AsyncMock()
        self.get_task_status = AsyncMock()
        self.get_task_log = AsyncMock()


class TaskDomainTests(unittest.IsolatedAsyncioTestCase):
    async def test_task_list_returns_count_and_tasks(self) -> None:
        client = MockPveClient()
        client.get_tasks.return_value = [
            TaskListEntry(
                upid="UPID:pve:00000001:00000001:00000001:qemcreate:root@pam:",
                node="pve1",
                status="stopped",
                exitstatus="OK",
            ),
        ]

        result = await task_list(client)

        self.assertEqual(result["count"], 1)
        self.assertEqual(len(result["tasks"]), 1)
        self.assertEqual(result["tasks"][0]["upid"], "UPID:pve:00000001:00000001:00000001:qemcreate:root@pam:")

    async def test_task_list_passes_filters_to_client(self) -> None:
        client = MockPveClient()
        client.get_tasks.return_value = []

        await task_list(client, node="pve1", user="root@pam", vmid=100, type_filter="qemu", status="running", limit=10)

        client.get_tasks.assert_awaited_once_with(
            node="pve1", user="root@pam", vmid=100, type_filter="qemu", status="running", limit=10
        )

    async def test_task_status_returns_upid_and_status(self) -> None:
        client = MockPveClient()
        client.get_task_status.return_value = TaskStatus(status="stopped", exitstatus="OK")
        upid = "UPID:pve:00000001:00000001:00000001:qemcreate:root@pam:"

        result = await task_status(client, upid)

        self.assertEqual(result["upid"], upid)
        self.assertEqual(result["status"], "stopped")
        self.assertEqual(result["exitstatus"], "OK")

    async def test_task_status_passes_node_to_client(self) -> None:
        client = MockPveClient()
        client.get_task_status.return_value = TaskStatus(status="running")
        upid = "UPID:pve1:00000001:00000001:00000001:qemcreate:root@pam:"

        await task_status(client, upid, node="pve1")

        client.get_task_status.assert_awaited_once_with(upid, node="pve1")

    async def test_task_log_returns_lines_with_text_mapped(self) -> None:
        client = MockPveClient()
        client.get_task_log.return_value = [
            TaskLogEntry(t="starting backup"),
            TaskLogEntry(t=" [...] 100%", n=42),
        ]
        upid = "UPID:pve:00000001:00000001:00000001:vzdump:root@pam:"

        result = await task_log(client, upid, "pve1")

        self.assertEqual(result["upid"], upid)
        self.assertEqual(result["total_lines"], 2)
        self.assertEqual(result["lines"][0]["text"], "starting backup")
        self.assertEqual(result["lines"][1]["text"], " [...] 100%")
        self.assertEqual(result["lines"][1]["lineno"], 42)

    async def test_task_log_passes_start_to_client(self) -> None:
        client = MockPveClient()
        client.get_task_log.return_value = []
        upid = "UPID:pve:00000001:00000001:00000001:vzdump:root@pam:"

        await task_log(client, upid, "pve1", start=5)

        client.get_task_log.assert_awaited_once_with("pve1", upid, start=5)

    async def test_task_log_without_lineno(self) -> None:
        client = MockPveClient()
        client.get_task_log.return_value = [
            TaskLogEntry(t="TASK ERROR: failed"),
        ]
        upid = "UPID:pve:00000001:00000001:00000001:vzdump:root@pam:"

        result = await task_log(client, upid, "pve1")

        self.assertEqual(result["total_lines"], 1)
        self.assertNotIn("lineno", result["lines"][0])


if __name__ == "__main__":
    unittest.main()
