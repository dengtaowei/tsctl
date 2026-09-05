# -*- coding: utf-8 -*-
"""Application controller: state, background work and lifecycle policy."""
from __future__ import print_function

import os

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from tsctl import autostart, backend, config, icons, priv
from tsctl.models import AppState
from tsctl.workers import TaskWorker


class AppController(QObject):
    state_changed = pyqtSignal(object)
    error = pyqtSignal(str)
    privilege_install_requested = pyqtSignal()
    privilege_remove_requested = pyqtSignal()
    quit_ready = pyqtSignal()

    def __init__(self, parent=None):
        super(AppController, self).__init__(parent)
        settings = config.load()
        actual_autostart = autostart.is_enabled()
        if settings["app_autostart"] != actual_autostart:
            settings["app_autostart"] = actual_autostart
            config.save(settings)

        self.state = AppState(
            app_autostart=settings["app_autostart"],
            start_on_launch=settings["start_tailscale_on_launch"],
        )
        self._workers = {}
        self._refresh_running = False
        self._refresh_pending = False
        self._action_context = None
        self._autostart_checked = False
        self._shutdown_started = False

        self._timer = QTimer(self)
        self._timer.setInterval(3000)
        self._timer.timeout.connect(self.refresh)

    def start(self):
        self._timer.start()
        self.refresh()

    def _emit(self):
        self.state_changed.emit(self.state)

    def _set_busy(self, message):
        self.state.busy = True
        self.state.busy_message = message
        self.state.message = ""
        self._timer.stop()
        self._emit()

    def _clear_busy(self):
        self.state.busy = False
        self.state.busy_message = ""
        if not self.state.shutting_down:
            self._timer.start()

    def _launch(self, task_id, function):
        worker = TaskWorker(task_id, function, self)
        self._workers[task_id] = worker
        worker.succeeded.connect(self._task_succeeded)
        worker.failed.connect(self._task_failed)
        worker.finished.connect(lambda: self._worker_finished(task_id))
        worker.start()

    def _worker_finished(self, task_id):
        worker = self._workers.pop(task_id, None)
        if worker is not None:
            worker.deleteLater()
        if (
            self.state.shutting_down
            and task_id != "shutdown-stop"
            and not self._workers
        ):
            QTimer.singleShot(0, self._begin_shutdown)

    def refresh(self):
        if self.state.shutting_down or self.state.busy:
            self._refresh_pending = True
            return
        if self._refresh_running:
            self._refresh_pending = True
            return
        self._refresh_running = True
        self._launch("refresh", backend.fetch_snapshot)

    def start_tailscale(self, interactive=True, automatic=False):
        if self.state.busy or self.state.shutting_down:
            return
        was_running = self.state.snapshot.running
        self._action_context = ("start", not was_running, automatic)
        message = (
            "正在自动启动 Tailscale 服务，请稍等…"
            if automatic
            else "正在启动 Tailscale 服务，请稍等…"
        )
        self._set_busy(message)
        self._launch(
            "action",
            lambda: backend.start_tailscale(interactive=interactive),
        )

    def stop_tailscale(self, interactive=True):
        if self.state.busy or self.state.shutting_down:
            return
        self._action_context = ("stop", False, False)
        self._set_busy("正在停止 Tailscale 服务，请稍等…")
        self._launch(
            "action",
            lambda: backend.stop_tailscale(interactive=interactive),
        )

    def set_app_autostart(self, enabled):
        if self.state.busy:
            return
        previous = self.state.app_autostart
        self.state.app_autostart = bool(enabled)
        self._set_busy("正在更新开机自启设置…")
        icon_path = icons.icon_png_path()
        self._launch(
            "setting-app-autostart",
            lambda: (previous, autostart.set_enabled(bool(enabled), icon_path)),
        )

    def set_start_on_launch(self, enabled):
        enabled = bool(enabled)
        self.state.start_on_launch = enabled
        self._save_settings()
        self._emit()
        if enabled:
            self._launch("privilege-probe", priv.has_passwordless_tailscaled)
        elif os.path.isfile(priv.SUDOERS_PATH) or os.path.isfile(
            priv.POLKIT_RULES_PATH
        ):
            self.privilege_remove_requested.emit()

    def resolve_privilege_install(self, install):
        if not install:
            self.state.message = (
                "已保存自动启动设置，但未安装免密权限；登录自启可能失败。"
            )
            self.state.message_level = "warning"
            self._emit()
            return
        self._set_busy("正在安装最小免密权限…")
        self._launch("privilege-install", priv.install_passwordless)

    def resolve_privilege_remove(self, remove):
        if not remove:
            return
        self._set_busy("正在移除免密权限…")
        self._launch("privilege-remove", priv.uninstall_passwordless)

    def request_quit(self):
        if self.state.shutting_down:
            return
        self.state.shutting_down = True
        self._timer.stop()
        self.state.busy = True
        self.state.busy_message = "正在退出，请稍等…"
        self._emit()
        if self._workers:
            return
        self._begin_shutdown()

    def _begin_shutdown(self):
        if self._shutdown_started:
            return
        self._shutdown_started = True
        if self.state.started_by_us:
            self._set_busy("正在停止由本工具启动的 Tailscale 服务…")
            self._launch(
                "shutdown-stop",
                lambda: backend.stop_tailscale(interactive=True),
            )
        else:
            self.quit_ready.emit()

    def _save_settings(self):
        config.save(
            {
                "app_autostart": self.state.app_autostart,
                "start_tailscale_on_launch": self.state.start_on_launch,
            }
        )

    def _task_succeeded(self, task_id, result):
        if task_id == "refresh":
            self._refresh_running = False
            self.state.snapshot = result
            self._emit()
            if not self._autostart_checked and not self.state.shutting_down:
                self._autostart_checked = True
                if self.state.start_on_launch and not result.running:
                    QTimer.singleShot(
                        0,
                        lambda: self.start_tailscale(
                            interactive=False, automatic=True
                        ),
                    )
            if self._refresh_pending and not self.state.shutting_down:
                self._refresh_pending = False
                QTimer.singleShot(0, self.refresh)
            return

        if task_id == "action":
            ok, message = result
            context = self._action_context
            self._action_context = None
            if ok and context:
                action, started_here, _automatic = context
                if action == "start" and started_here:
                    self.state.started_by_us = True
                elif action == "stop":
                    self.state.started_by_us = False
            self._clear_busy()
            self.state.message = message
            self.state.message_level = "success" if ok else "error"
            self._emit()
            if not ok:
                self.error.emit(message or "操作失败")
            self.refresh()
            return

        if task_id == "setting-app-autostart":
            previous, payload = result
            ok, message = payload
            if not ok:
                self.state.app_autostart = previous
                self.error.emit(message)
            self._save_settings()
            self._clear_busy()
            self.state.message = message
            self.state.message_level = "success" if ok else "error"
            self._emit()
            return

        if task_id == "privilege-probe":
            if not result:
                self.privilege_install_requested.emit()
            return

        if task_id in ("privilege-install", "privilege-remove"):
            ok, message = result
            self._clear_busy()
            self.state.message = message
            self.state.message_level = "success" if ok else "error"
            self._emit()
            if not ok:
                self.error.emit(message)
            return

        if task_id == "shutdown-stop":
            ok, message = result
            self.state.started_by_us = False
            if not ok:
                self.error.emit(message or "退出时停止 tailscaled 失败")
            self.quit_ready.emit()

    def _task_failed(self, task_id, message):
        if task_id == "refresh":
            self._refresh_running = False
            self.state.message = "刷新失败: %s" % message
            self.state.message_level = "error"
            self._emit()
            return
        self._clear_busy()
        self.state.message = message
        self.state.message_level = "error"
        self._emit()
        self.error.emit(message)
        if task_id == "shutdown-stop":
            self.quit_ready.emit()
