# -*- coding: utf-8 -*-
import json
import unittest
from unittest.mock import patch

from tsctl import backend
from tsctl.runner import CommandResult


class SnapshotTests(unittest.TestCase):
    def test_snapshot_uses_one_json_query(self):
        payload = {
            "BackendState": "Running",
            "Self": {
                "HostName": "local",
                "OS": "linux",
                "Online": True,
                "TailscaleIPs": ["100.64.0.1", "fd7a::1"],
            },
            "Peer": {
                "node-key": {
                    "HostName": "peer",
                    "OS": "linux",
                    "Online": True,
                    "Active": True,
                    "CurAddr": "192.0.2.1:41641",
                    "TailscaleIPs": ["100.64.0.2"],
                }
            },
        }
        result = CommandResult(0, json.dumps(payload), "")
        with patch.object(backend.app_platform, "find_tailscale", return_value="/bin/ts"):
            with patch.object(backend, "run", return_value=result) as command:
                snapshot = backend.fetch_snapshot()

        self.assertTrue(snapshot.running)
        self.assertEqual(snapshot.ipv4, "100.64.0.1")
        self.assertEqual([peer.name for peer in snapshot.peers], ["local", "peer"])
        self.assertEqual(snapshot.peers[1].path, "direct 192.0.2.1:41641")
        command.assert_called_once_with(
            ["/bin/ts", "status", "--json"], timeout=15
        )

    def test_missing_cli_returns_stopped_snapshot(self):
        with patch.object(backend.app_platform, "find_tailscale", return_value=None):
            snapshot = backend.fetch_snapshot()
        self.assertFalse(snapshot.running)
        self.assertIn("未找到", snapshot.raw_display)


if __name__ == "__main__":
    unittest.main()
