# -*- coding: utf-8 -*-
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

from tsctl.controller import AppController
from tsctl.models import StatusSnapshot
from tsctl.ui.main_window import MainWindow


class ButtonWiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def make_window(self, running):
        config_data = {
            "app_autostart": False,
            "start_tailscale_on_launch": False,
        }
        with patch("tsctl.controller.config.load", return_value=config_data):
            with patch("tsctl.controller.autostart.is_enabled", return_value=False):
                controller = AppController()
        controller.state.snapshot = StatusSnapshot(
            cli_path="/bin/tailscale", running=running
        )
        window = MainWindow(controller)
        window.hide()
        return window, controller

    def test_stop_button_keeps_interactive_escalation(self):
        window, controller = self.make_window(running=True)
        with patch.object(controller, "_launch"):
            with patch("tsctl.controller.backend.stop_tailscale") as stop:
                window.stop_button.click()
                controller._launch.call_args[0][1]()
        self.assertIs(stop.call_args[1]["interactive"], True)

    def test_start_button_keeps_interactive_escalation(self):
        window, controller = self.make_window(running=False)
        with patch.object(controller, "_launch"):
            with patch("tsctl.controller.backend.start_tailscale") as start:
                window.start_button.click()
                controller._launch.call_args[0][1]()
        self.assertIs(start.call_args[1]["interactive"], True)


if __name__ == "__main__":
    unittest.main()
