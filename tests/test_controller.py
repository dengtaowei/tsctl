# -*- coding: utf-8 -*-
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

from tsctl.controller import AppController
from tsctl.models import StatusSnapshot


class ControllerOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def make_controller(self):
        config_data = {
            "app_autostart": False,
            "start_tailscale_on_launch": False,
        }
        with patch("tsctl.controller.config.load", return_value=config_data):
            with patch("tsctl.controller.autostart.is_enabled", return_value=False):
                return AppController()

    def test_starting_stopped_service_sets_ownership(self):
        controller = self.make_controller()
        controller._action_context = ("start", True, False)
        with patch.object(controller, "refresh"):
            controller._task_succeeded("action", (True, "ok"))
        self.assertTrue(controller.state.started_by_us)

    def test_starting_preexisting_service_does_not_set_ownership(self):
        controller = self.make_controller()
        controller._action_context = ("start", False, False)
        with patch.object(controller, "refresh"):
            controller._task_succeeded("action", (True, "ok"))
        self.assertFalse(controller.state.started_by_us)

    def test_stop_clears_ownership(self):
        controller = self.make_controller()
        controller.state.started_by_us = True
        controller._action_context = ("stop", False, False)
        with patch.object(controller, "refresh"):
            controller._task_succeeded("action", (True, "ok"))
        self.assertFalse(controller.state.started_by_us)

    def test_quit_stops_only_owned_service(self):
        controller = self.make_controller()
        controller.state.started_by_us = True
        controller.state.snapshot = StatusSnapshot(
            cli_path="/bin/tailscale", running=True
        )
        with patch.object(controller, "_launch") as launch:
            controller.request_quit()
        self.assertEqual(launch.call_args[0][0], "shutdown-stop")

    def test_quit_skips_preexisting_service(self):
        controller = self.make_controller()
        emitted = []
        controller.quit_ready.connect(lambda: emitted.append(True))
        controller.request_quit()
        self.assertEqual(emitted, [True])


if __name__ == "__main__":
    unittest.main()
