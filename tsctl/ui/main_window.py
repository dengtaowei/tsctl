# -*- coding: utf-8 -*-
"""Main window: widgets and rendering only."""
from __future__ import print_function

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from tsctl import backend, priv, theme
from tsctl.ui.peers_table import PeersTable
from tsctl.ui.settings_panel import SettingsPanel
from tsctl.ui.tray import TrayController


class RawStatusWindow(QWidget):
    def __init__(self, parent=None):
        super(RawStatusWindow, self).__init__(
            parent, Qt.Tool | Qt.WindowCloseButtonHint
        )
        self.setWindowTitle("tsctl · 原始 status")
        self.resize(720, 260)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        self.editor = QTextEdit()
        self.editor.setObjectName("rawStatus")
        self.editor.setReadOnly(True)
        font = QFont("Monospace")
        font.setStyleHint(QFont.TypeWriter)
        font.setPointSize(10)
        self.editor.setFont(font)
        layout.addWidget(self.editor)

    def set_text(self, text):
        self.editor.setPlainText(text or "")


class MainWindow(QMainWindow):
    def __init__(self, controller, start_minimized=False):
        super(MainWindow, self).__init__()
        self.controller = controller
        self._really_quit = False
        self._last_message = ""
        self.setWindowTitle("tsctl")
        self.resize(860, 700)
        self.setMinimumSize(720, 560)

        root = QWidget()
        root.setObjectName("centralRoot")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(14)

        header = QHBoxLayout()
        brand = QVBoxLayout()
        brand.setSpacing(2)
        title = QLabel("tsctl")
        title.setObjectName("brandTitle")
        subtitle = QLabel("Tailscale 本机管理")
        subtitle.setObjectName("brandSub")
        brand.addWidget(title)
        brand.addWidget(subtitle)
        header.addLayout(brand, 1)
        self.badge = QLabel("—")
        self.badge.setObjectName("badgeStopped")
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setMinimumWidth(72)
        header.addWidget(self.badge, 0, Qt.AlignVCenter)
        layout.addLayout(header)

        status_card = QFrame()
        status_card.setObjectName("statusBar")
        status_layout = QHBoxLayout(status_card)
        status_layout.setContentsMargins(16, 12, 16, 12)
        self.status_line = QLabel("本机 IP —  ·  CLI —")
        self.status_line.setObjectName("statusLine")
        self.status_line.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.status_line.setWordWrap(True)
        status_layout.addWidget(self.status_line)
        layout.addWidget(status_card)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        self.start_button = self._button("启动", "btnPrimary")
        self.stop_button = self._button("停止", "btnDanger")
        self.refresh_button = self._button("刷新", "btnGhost")
        actions.addWidget(self.start_button)
        actions.addWidget(self.stop_button)
        actions.addWidget(self.refresh_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.message = QLabel("")
        self.message.setObjectName("actionHint")
        self.message.setWordWrap(True)
        self.message.hide()
        layout.addWidget(self.message)

        peers_header = QHBoxLayout()
        peers_title = QLabel("节点列表 · 双击复制 IP")
        peers_title.setObjectName("sectionTitle")
        peers_header.addWidget(peers_title, 1)
        self.raw_button = QPushButton("打开原始 status ↗")
        self.raw_button.setObjectName("btnLink")
        self.raw_button.setFlat(True)
        self.raw_button.setCursor(Qt.PointingHandCursor)
        peers_header.addWidget(self.raw_button, 0, Qt.AlignRight)
        layout.addLayout(peers_header)

        self.peers = PeersTable()
        self.peers.setMinimumHeight(180)
        layout.addWidget(self.peers, 1)

        self.settings = SettingsPanel()
        layout.addWidget(self.settings)

        footer = QLabel(backend.platform_hint())
        footer.setObjectName("footerLabel")
        layout.addWidget(footer)

        self.raw_window = RawStatusWindow(self)
        self.tray = TrayController(self)

        # clicked(bool) would land on the first slot argument, so drop it here.
        self.start_button.clicked.connect(lambda: self.controller.start_tailscale())
        self.stop_button.clicked.connect(lambda: self.controller.stop_tailscale())
        self.refresh_button.clicked.connect(lambda: self.controller.refresh())
        self.raw_button.clicked.connect(self._show_raw)
        self.peers.ip_copied.connect(self._copy_ip)
        self.settings.app_autostart_changed.connect(
            self.controller.set_app_autostart
        )
        self.settings.start_on_launch_changed.connect(
            self.controller.set_start_on_launch
        )

        self.controller.state_changed.connect(self.render)
        self.controller.error.connect(self._show_error)
        self.controller.privilege_install_requested.connect(
            self._ask_install_privilege
        )
        self.controller.privilege_remove_requested.connect(
            self._ask_remove_privilege
        )
        self.controller.quit_ready.connect(self._finish_quit)

        self.tray.show_requested.connect(self.show_from_tray)
        self.tray.start_requested.connect(self.controller.start_tailscale)
        self.tray.stop_requested.connect(self.controller.stop_tailscale)
        self.tray.refresh_requested.connect(self.controller.refresh)
        self.tray.quit_requested.connect(self.quit_app)

        if start_minimized and self.tray.available:
            self.hide()
        else:
            self.show()

    def _button(self, text, object_name):
        button = QPushButton(text)
        button.setObjectName(object_name)
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumSize(88, 36)
        return button

    def _set_badge(self, kind, text):
        object_name = {
            "running": "badgeRunning",
            "stopped": "badgeStopped",
            "busy": "badgeBusy",
        }[kind]
        self.badge.setObjectName(object_name)
        self.badge.setText(text)
        self.badge.style().unpolish(self.badge)
        self.badge.style().polish(self.badge)

    def render(self, state):
        snapshot = state.snapshot
        cli = snapshot.cli_path or "未找到"
        self.status_line.setText(
            "本机 IP  %s    ·    CLI  %s" % (snapshot.ipv4 or "—", cli)
        )
        self.peers.set_peers(snapshot.peers if snapshot.running else [])
        self.raw_window.set_text(snapshot.raw_display)
        self.settings.render(state.app_autostart, state.start_on_launch)

        if state.busy:
            self._set_badge("busy", "处理中")
            self.message.setStyleSheet("color: %s;" % theme.ACCENT)
            self.message.setText(state.busy_message)
            self.message.show()
        else:
            self._set_badge(
                "running" if snapshot.running else "stopped",
                "运行中" if snapshot.running else "未运行",
            )
            if state.message:
                color = (
                    theme.SUCCESS
                    if state.message_level == "success"
                    else theme.DANGER
                    if state.message_level == "error"
                    else theme.WARNING
                )
                self.message.setStyleSheet("color: %s;" % color)
                self.message.setText(state.message)
                self.message.show()
                if state.message != self._last_message:
                    self.tray.notify(
                        state.message,
                        warning=state.message_level == "error",
                    )
                    self._last_message = state.message
            else:
                self.message.hide()

        self.start_button.setEnabled(not state.busy and not snapshot.running)
        self.stop_button.setEnabled(not state.busy and snapshot.running)
        self.refresh_button.setEnabled(not state.busy)
        self.settings.setEnabled(not state.busy)
        self.tray.render(snapshot.running, snapshot.ipv4)

    def _show_raw(self):
        self.raw_window.show()
        self.raw_window.raise_()
        self.raw_window.activateWindow()

    def _copy_ip(self, ip):
        QApplication.clipboard().setText(ip)
        self.tray.notify("已复制 IP: %s" % ip)

    def _show_error(self, message):
        QMessageBox.warning(self, "操作失败", message)

    def _ask_install_privilege(self):
        answer = QMessageBox.question(
            self,
            "需要免密权限",
            priv.explain_dialog_text(),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        self.controller.resolve_privilege_install(answer == QMessageBox.Yes)

    def _ask_remove_privilege(self):
        answer = QMessageBox.question(
            self,
            "移除免密权限",
            "是否同时删除已安装的免密权限文件？\n"
            "取消勾选不会立即停止当前服务。\n"
            "删除后，退出时停服务可能需要再次输入管理员密码。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        self.controller.resolve_privilege_remove(answer == QMessageBox.Yes)

    def show_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def quit_app(self):
        self._really_quit = True
        self.controller.request_quit()

    def _finish_quit(self):
        self.raw_window.close()
        self.tray.hide()
        QApplication.instance().quit()

    def closeEvent(self, event):
        if self.tray.available and not self._really_quit:
            self.hide()
            self.tray.notify(
                "已最小化到托盘；托盘「退出」才会结束进程。", timeout=2500
            )
            event.ignore()
            return
        if not self._really_quit:
            self._really_quit = True
            self.controller.request_quit()
            event.ignore()
            return
        event.accept()
