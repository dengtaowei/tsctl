# -*- coding: utf-8 -*-
"""Desktop launcher and login-autostart integration."""
from __future__ import print_function

import os

from tsctl import platform as app_platform
from tsctl import runtime


def main_py_path():
    return os.path.join(runtime.project_root(), "main.py")


def linux_autostart_path():
    return os.path.join(
        app_platform.config_home(), "autostart", "tsctl.desktop"
    )


def linux_launcher_path():
    return os.path.join(
        app_platform.data_home(), "applications", "tsctl.desktop"
    )


def windows_startup_path():
    return os.path.join(
        app_platform.config_home(),
        "Microsoft",
        "Windows",
        "Start Menu",
        "Programs",
        "Startup",
        "tsctl.bat",
    )


def desktop_entry(exec_line, icon_path, autostart=False):
    lines = [
        "[Desktop Entry]",
        "Type=Application",
        "Version=1.0",
        "Name=tsctl",
        "Comment=Tailscale manager",
        "Exec=%s" % exec_line,
        "Icon=%s" % icon_path,
        "Terminal=false",
        "Categories=Network;",
        "StartupNotify=true",
        "StartupWMClass=tsctl",
    ]
    if autostart:
        lines.append("X-GNOME-Autostart-enabled=true")
    lines.append("")
    return "\n".join(lines)


def _write(path, content):
    directory = os.path.dirname(path)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    with open(path, "w") as stream:
        stream.write(content)


def _autostart_body(icon_path):
    return desktop_entry(
        runtime.launch_exec_line(["--minimized"]), icon_path, autostart=True
    )


def _windows_startup_body():
    quoted = " ".join(
        '"%s"' % part for part in runtime.launch_command(["--minimized"])
    )
    return '@echo off\r\nstart "" %s\r\n' % quoted


def _launcher_body(icon_path):
    return desktop_entry(runtime.launch_exec_line(), icon_path)


def ensure_launcher(icon_path):
    """Install/update the Linux application launcher."""
    if not app_platform.IS_LINUX:
        return
    _write(linux_launcher_path(), _launcher_body(icon_path))


def refresh_entries(icon_path):
    """Re-point launcher and any enabled autostart entry at this build.

    Called on every startup: moving the project or swapping a source run for a
    frozen binary would otherwise leave ``Exec=`` on a path that no longer
    exists.
    """
    if app_platform.IS_LINUX:
        ensure_launcher(icon_path)
        if is_enabled():
            _write(linux_autostart_path(), _autostart_body(icon_path))
        return
    if app_platform.IS_WINDOWS and is_enabled():
        _write(windows_startup_path(), _windows_startup_body())


def is_enabled():
    if app_platform.IS_LINUX:
        return os.path.isfile(linux_autostart_path())
    if app_platform.IS_WINDOWS:
        return os.path.isfile(windows_startup_path())
    return False


def set_enabled(enabled, icon_path=""):
    """Enable/disable login autostart. Return ``(ok, message)``."""
    # A frozen build launches the binary itself, which is always present.
    if not runtime.is_frozen() and not os.path.isfile(main_py_path()):
        return False, "找不到 main.py: %s" % main_py_path()

    if app_platform.IS_LINUX:
        path = linux_autostart_path()
        if enabled:
            _write(path, _autostart_body(icon_path))
            ensure_launcher(icon_path)
            return True, "已写入 %s" % path
        if os.path.isfile(path):
            os.remove(path)
        return True, "已取消开机自启"

    if app_platform.IS_WINDOWS:
        path = windows_startup_path()
        if enabled:
            _write(path, _windows_startup_body())
            return True, "已写入 %s" % path
        if os.path.isfile(path):
            os.remove(path)
        return True, "已取消开机自启"

    return False, "当前平台不支持自动配置开机自启"
