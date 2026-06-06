from __future__ import annotations

import unittest
from unittest.mock import AsyncMock

from mcp_proxmox.domains.tasks import task_follow, task_list, task_log, task_status, task_wait
from mcp_proxmox.pve.client.core import PveApiError
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

    # --- task_wait tests ---

    async def test_task_wait_returns_immediately_when_stopped(self) -> None:
        client = MockPveClient()
        client.get_task_status.return_value = TaskStatus(status="stopped", exitstatus="OK")
        upid = "UPID:pve:00000001:00000001:00000001:qemcreate:root@pam:"

        result = await task_wait(client, upid, timeout=10)

        self.assertEqual(result["upid"], upid)
        self.assertEqual(result["status"], "stopped")
        self.assertEqual(result["exitstatus"], "OK")
        self.assertTrue(result["completed"])
        self.assertIn("wait_seconds", result)

    async def test_task_wait_polls_until_stopped(self) -> None:
        client = MockPveClient()
        client.get_task_status = AsyncMock(
            side_effect=[
                TaskStatus(status="running"),
                TaskStatus(status="running"),
                TaskStatus(status="stopped", exitstatus="OK"),
            ]
        )
        upid = "UPID:pve:00000001:00000001:00000001:qemcreate:root@pam:"

        result = await task_wait(client, upid, timeout=10, poll_interval=0.01)

        self.assertTrue(result["completed"])
        self.assertEqual(result["status"], "stopped")
        self.assertEqual(result["exitstatus"], "OK")
        self.assertEqual(client.get_task_status.await_count, 3)

    async def test_task_wait_returns_timeout_when_exceeded(self) -> None:
        client = MockPveClient()
        client.get_task_status.return_value = TaskStatus(status="running")
        upid = "UPID:pve:00000001:00000001:00000001:qemcreate:root@pam:"

        result = await task_wait(client, upid, timeout=0.01, poll_interval=0.01)

        self.assertFalse(result["completed"])
        self.assertTrue(result["timed_out"])
        self.assertEqual(result["status"], "running")

    async def test_task_wait_timeout_with_no_status(self) -> None:
        client = MockPveClient()
        client.get_task_status.side_effect = PveApiError("transient error", "/path", status_code=503)
        upid = "UPID:pve:..."

        result = await task_wait(client, upid, timeout=0.01, poll_interval=0.01)

        self.assertFalse(result["completed"])
        self.assertTrue(result["timed_out"])
        self.assertEqual(result["status"], "unknown")

    async def test_task_wait_returns_not_found_on_404(self) -> None:
        client = MockPveClient()
        client.get_task_status.side_effect = PveApiError("not found", "/path", status_code=404)
        upid = "UPID:pve:..."

        result = await task_wait(client, upid, timeout=10)

        self.assertFalse(result["completed"])
        self.assertEqual(result["error"], "task_not_found")

    async def test_task_wait_returns_api_error_on_4xx(self) -> None:
        client = MockPveClient()
        client.get_task_status.side_effect = PveApiError("bad request", "/path", status_code=400)
        upid = "UPID:pve:..."

        result = await task_wait(client, upid, timeout=10)

        self.assertFalse(result["completed"])
        self.assertEqual(result["error"], "api_error")

    async def test_task_wait_retries_on_5xx(self) -> None:
        client = MockPveClient()
        client.get_task_status = AsyncMock(
            side_effect=[
                PveApiError("server error", "/path", status_code=503),
                PveApiError("server error", "/path", status_code=502),
                TaskStatus(status="stopped", exitstatus="OK"),
            ]
        )
        upid = "UPID:pve:..."

        result = await task_wait(client, upid, timeout=10, poll_interval=0.01)

        self.assertTrue(result["completed"])
        self.assertEqual(result["exitstatus"], "OK")

    async def test_task_wait_passes_node_to_client(self) -> None:
        client = MockPveClient()
        client.get_task_status.side_effect = [
            TaskStatus(status="running"),
            TaskStatus(status="stopped", exitstatus="OK"),
        ]
        upid = "UPID:pve1:..."

        await task_wait(client, upid, node="pve1", timeout=10, poll_interval=0.01)

        assert client.get_task_status.await_count >= 1

    # --- task_follow tests ---

    async def test_task_follow_returns_log_when_stopped(self) -> None:
        client = MockPveClient()
        client.get_task_status.return_value = TaskStatus(status="stopped", exitstatus="OK")
        client.get_task_log.return_value = [
            TaskLogEntry(t="line1", n=0),
            TaskLogEntry(t="line2", n=1),
        ]
        upid = "UPID:pve:..."
        node = "pve1"

        result = await task_follow(client, upid, node, timeout=10)

        self.assertTrue(result["completed"])
        self.assertEqual(result["status"], "stopped")
        self.assertEqual(result["total_lines"], 2)
        self.assertEqual(result["lines"][0]["text"], "line1")
        self.assertEqual(result["lines"][1]["text"], "line2")

    async def test_task_follow_polls_until_stopped(self) -> None:
        client = MockPveClient()
        client.get_task_status = AsyncMock(
            side_effect=[
                TaskStatus(status="running"),
                TaskStatus(status="stopped", exitstatus="OK"),
            ]
        )
        client.get_task_log.return_value = [TaskLogEntry(t="progress", n=0)]
        upid = "UPID:pve:..."

        result = await task_follow(client, upid, "pve1", timeout=10, poll_interval=0.01)

        self.assertTrue(result["completed"])
        self.assertEqual(result["status"], "stopped")
        self.assertGreaterEqual(client.get_task_status.await_count, 2)

    async def test_task_follow_returns_timeout_with_partial_log(self) -> None:
        client = MockPveClient()
        client.get_task_status.return_value = TaskStatus(status="running")
        client.get_task_log.return_value = [
            TaskLogEntry(t="running task...", n=0),
            TaskLogEntry(t=" [...] 30%", n=3),
        ]
        upid = "UPID:pve:..."

        result = await task_follow(client, upid, "pve1", timeout=0.01, poll_interval=0.01)

        self.assertFalse(result["completed"])
        self.assertTrue(result["timed_out"])
        self.assertIn("lines", result)
        self.assertGreater(result["total_lines"], 0)

    async def test_task_follow_incremental_log(self) -> None:
        client = MockPveClient()
        client.get_task_status = AsyncMock(
            side_effect=[
                TaskStatus(status="running"),
                TaskStatus(status="running"),
                TaskStatus(status="stopped", exitstatus="OK"),
            ]
        )
        client.get_task_log = AsyncMock(
            side_effect=[
                [TaskLogEntry(t="line0", n=0)],
                [TaskLogEntry(t="line1", n=1)],
                [TaskLogEntry(t="line2", n=2)],
            ]
        )
        upid = "UPID:pve:..."

        result = await task_follow(client, upid, "pve1", timeout=10, poll_interval=0.01)

        self.assertEqual(result["total_lines"], 3)
        self.assertEqual(result["lines"][0]["text"], "line0")
        self.assertEqual(result["lines"][1]["text"], "line1")
        self.assertEqual(result["lines"][2]["text"], "line2")

    async def test_task_follow_log_truncated_at_limit(self) -> None:
        client = MockPveClient()
        client.get_task_status.return_value = TaskStatus(status="stopped", exitstatus="OK")
        many_lines = [TaskLogEntry(t=f"line{i}", n=i) for i in range(6000)]
        client.get_task_log.return_value = many_lines
        upid = "UPID:pve:..."

        result = await task_follow(client, upid, "pve1", timeout=10)

        self.assertTrue(result["log_truncated"])
        self.assertEqual(result["total_lines"], 5000)
        self.assertEqual(len(result["lines"]), 5000)

    async def test_task_follow_returns_not_found_on_404(self) -> None:
        client = MockPveClient()
        client.get_task_status.side_effect = PveApiError("not found", "/path", status_code=404)
        upid = "UPID:pve:..."

        result = await task_follow(client, upid, "pve1", timeout=10)

        self.assertFalse(result["completed"])
        self.assertEqual(result["error"], "task_not_found")

    async def test_task_follow_retries_on_5xx_status(self) -> None:
        client = MockPveClient()
        client.get_task_status = AsyncMock(
            side_effect=[
                PveApiError("server error", "/path", status_code=503),
                TaskStatus(status="stopped", exitstatus="OK"),
            ]
        )
        client.get_task_log.return_value = []
        upid = "UPID:pve:..."

        result = await task_follow(client, upid, "pve1", timeout=10, poll_interval=0.01)

        self.assertTrue(result["completed"])

    async def test_task_follow_handles_log_api_error(self) -> None:
        client = MockPveClient()
        client.get_task_status.return_value = TaskStatus(status="stopped", exitstatus="OK")
        client.get_task_log.side_effect = PveApiError("log error", "/path", status_code=500)
        upid = "UPID:pve:..."

        result = await task_follow(client, upid, "pve1", timeout=10)

        self.assertTrue(result["completed"])
        self.assertEqual(result["total_lines"], 0)


if __name__ == "__main__":
    unittest.main()
