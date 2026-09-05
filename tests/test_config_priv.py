# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

from tsctl import autostart, config, priv
from tsctl.runner import run


class ConfigTests(unittest.TestCase):
    def test_defaults_and_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                os.environ, {"XDG_CONFIG_HOME": directory}, clear=False
            ):
                self.assertEqual(config.load(), config.DEFAULTS)
                saved = config.save(
                    {
                        "app_autostart": True,
                        "start_tailscale_on_launch": False,
                    }
                )
                self.assertTrue(saved["app_autostart"])
                self.assertEqual(config.load(), saved)


class PrivilegeRuleTests(unittest.TestCase):
    def test_sudoers_is_narrowly_scoped(self):
        body = priv._sudoers_body("alice", "/usr/bin/systemctl")
        self.assertIn(
            "alice ALL=(root) NOPASSWD: /usr/bin/systemctl start tailscaled",
            body,
        )
        self.assertNotIn("enable tailscaled", body)
        self.assertNotIn(" ALL=(ALL) ALL", body)

    def test_polkit_is_scoped_to_tailscaled(self):
        body = priv._polkit_rules_body("alice")
        self.assertIn('subject.user !== "alice"', body)
        self.assertIn('unit === "tailscaled.service"', body)
        self.assertIn('verb === "start"', body)


class InfrastructureTests(unittest.TestCase):
    def test_runner_maps_timeout(self):
        result = run(
            [sys.executable, "-c", "import time; time.sleep(1)"],
            timeout=0.01,
        )
        self.assertEqual(result.returncode, 124)

    def test_desktop_entry_contains_grouping_and_icon(self):
        body = autostart.desktop_entry(
            "/usr/bin/python3 /opt/tsctl/main.py", "/opt/tsctl/icon.png"
        )
        self.assertIn("StartupWMClass=tsctl", body)
        self.assertIn("Icon=/opt/tsctl/icon.png", body)
        self.assertNotIn("X-GNOME-Autostart-enabled", body)


if __name__ == "__main__":
    unittest.main()
