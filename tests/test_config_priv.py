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

    def test_frozen_launch_uses_executable_only(self):
        from tsctl import runtime

        with patch.object(runtime, "is_frozen", return_value=True):
            with patch.object(sys, "executable", "/opt/tsctl/bin/tsctl"):
                self.assertEqual(
                    runtime.launch_command(["--minimized"]),
                    ["/opt/tsctl/bin/tsctl", "--minimized"],
                )
                self.assertEqual(
                    runtime.launch_exec_line(["--minimized"]),
                    "/opt/tsctl/bin/tsctl --minimized",
                )

    def _fake_exec_line(self, extra_args=None):
        if extra_args:
            return "/opt/tsctl/bin/tsctl --minimized"
        return "/opt/tsctl/bin/tsctl"

    def test_refresh_rewrites_stale_autostart(self):
        with tempfile.TemporaryDirectory() as directory:
            config_home = os.path.join(directory, "config")
            data_home = os.path.join(directory, "data")
            os.makedirs(os.path.join(config_home, "autostart"))
            stale = os.path.join(config_home, "autostart", "tsctl.desktop")
            with open(stale, "w") as stream:
                stream.write(
                    autostart.desktop_entry(
                        "/usr/bin/python3 /old/tailscale/main.py --minimized",
                        "/old/icon.png",
                        autostart=True,
                    )
                )
            env = {
                "XDG_CONFIG_HOME": config_home,
                "XDG_DATA_HOME": data_home,
            }
            with patch.dict(os.environ, env, clear=False):
                with patch(
                    "tsctl.runtime.launch_exec_line",
                    side_effect=self._fake_exec_line,
                ):
                    autostart.refresh_entries("/opt/icon.png")
            with open(stale) as stream:
                body = stream.read()
            self.assertIn("Exec=/opt/tsctl/bin/tsctl --minimized", body)
            self.assertIn("Icon=/opt/icon.png", body)
            self.assertNotIn("/old/tailscale/main.py", body)

    def test_refresh_does_not_create_autostart_when_disabled(self):
        with tempfile.TemporaryDirectory() as directory:
            config_home = os.path.join(directory, "config")
            data_home = os.path.join(directory, "data")
            env = {
                "XDG_CONFIG_HOME": config_home,
                "XDG_DATA_HOME": data_home,
            }
            with patch.dict(os.environ, env, clear=False):
                with patch(
                    "tsctl.runtime.launch_exec_line",
                    side_effect=self._fake_exec_line,
                ):
                    autostart.refresh_entries("/opt/icon.png")
                self.assertFalse(
                    os.path.exists(autostart.linux_autostart_path())
                )
                self.assertTrue(os.path.isfile(autostart.linux_launcher_path()))

    def test_icon_cache_lives_under_data_home(self):
        from tsctl import icons

        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                os.environ, {"XDG_DATA_HOME": directory}, clear=False
            ):
                path = icons.icon_png_path()
        self.assertEqual(
            path, os.path.join(directory, "tsctl", "icons", "tsctl.png")
        )


if __name__ == "__main__":
    unittest.main()
