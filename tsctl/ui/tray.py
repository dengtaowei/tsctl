# -*- coding: utf-8 -*-
"""System tray presentation and signals."""
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QAction, QMenu, QSystemTrayIcon

from tsctl import icons


class TrayController(QObject):
    show_requested = pyqtSignal()
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    refresh_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super(TrayController, self).__init__(parent)
        self.tray = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(parent)
        menu = QMenu()
        for label, signal in (
            ("显示窗口", self.show_requested),
            (None, None),
            ("启动", self.start_requested),
            ("停止", self.stop_requested),
            ("刷新", self.refresh_requested),
            (None, None),
            ("退出", self.quit_requested),
        ):
            if label is None:
                menu.addSeparator()
                continue
            action = QAction(label, menu)
            action.triggered.connect(signal.emit)
            menu.addAction(action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._activated)
        self.render(False, "")
        self.tray.show()

    @property
    def available(self):
        return self.tray is not None

    def _activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_requested.emit()

    def render(self, running, ip):
        if not self.tray:
            return
        self.tray.setIcon(icons.make_tray_icon(running))
        tip = "tsctl · 运行中" if running else "tsctl · 未运行"
        if ip:
            tip += " · %s" % ip
        self.tray.setToolTip(tip)

    def notify(self, message, warning=False, timeout=2500):
        if not self.tray or not message:
            return
        icon = QSystemTrayIcon.Warning if warning else QSystemTrayIcon.Information
        self.tray.showMessage("tsctl", message, icon, timeout)

    def hide(self):
        if self.tray:
            self.tray.hide()
