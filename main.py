#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tsctl — minimal Tailscale manager (PyQt5)."""
from __future__ import print_function

import sys

# Help X11/GNOME map this process to StartupWMClass=tsctl (not "python3")
if sys.argv and sys.argv[0].endswith("main.py"):
    sys.argv[0] = "tsctl"

from PyQt5.QtWidgets import QApplication

from tsctl import autostart
from tsctl.controller import AppController
from tsctl import icons as appicons
from tsctl import theme
from tsctl.ui.main_window import MainWindow


def main():
    start_minimized = "--minimized" in sys.argv
    app = QApplication(sys.argv)
    app.setApplicationName("tsctl")
    app.setApplicationDisplayName("tsctl")
    app.setOrganizationName("tsctl")
    app.setStyle("Fusion")
    app.setStyleSheet(theme.app_stylesheet())
    # Match ~/.local/share/applications/tsctl.desktop
    if hasattr(app, "setDesktopFileName"):
        app.setDesktopFileName("tsctl")

    icon = appicons.load_app_icon()
    app.setWindowIcon(icon)
    autostart.refresh_entries(appicons.ensure_icon_png())

    app.setQuitOnLastWindowClosed(False)
    controller = AppController(app)
    win = MainWindow(controller, start_minimized=start_minimized)
    win.setWindowIcon(icon)
    controller.start()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
