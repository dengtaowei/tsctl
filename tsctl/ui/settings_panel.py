# -*- coding: utf-8 -*-
"""Settings card with no filesystem or privilege logic."""
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QCheckBox, QFrame, QLabel, QSizePolicy, QVBoxLayout

from tsctl import config


class SettingsPanel(QFrame):
    app_autostart_changed = pyqtSignal(bool)
    start_on_launch_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(SettingsPanel, self).__init__(parent)
        self.setObjectName("card")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        title = QLabel("设置")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        self.app_autostart = QCheckBox("开机（登录桌面后）自动启动本工具")
        self.start_on_launch = QCheckBox("本工具启动时自动启动 Tailscale 服务")
        layout.addWidget(self.app_autostart)
        layout.addWidget(self.start_on_launch)

        note = QLabel(
            "配置 %s\n取消勾选只影响下次启动；本工具拉起的服务在托盘退出时停止。"
            % config.config_path()
        )
        note.setObjectName("noteLabel")
        note.setWordWrap(True)
        layout.addWidget(note)

        self.app_autostart.toggled.connect(self.app_autostart_changed)
        self.start_on_launch.toggled.connect(self.start_on_launch_changed)

    def render(self, app_autostart, start_on_launch):
        self.app_autostart.blockSignals(True)
        self.start_on_launch.blockSignals(True)
        self.app_autostart.setChecked(bool(app_autostart))
        self.start_on_launch.setChecked(bool(start_on_launch))
        self.app_autostart.blockSignals(False)
        self.start_on_launch.blockSignals(False)
