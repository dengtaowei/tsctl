# -*- coding: utf-8 -*-
"""Desktop launcher and login-autostart integration."""
from __future__ import print_function

import os
import sys

from tsctl import platform as app_platform


def project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main_py_path():
    return os.path.join(project_root(), "main.py")


def python_executable():
    return os.path.abspath(sys.executable)


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


def ensure_launcher(icon_path):
    """Install/update the Linux application launcher."""
    if not app_platform.IS_LINUX:
        return
    path = linux_launcher_path()
    exec_line = "%s %s" % (python_executable(), main_py_path())
    _write(path, desktop_entry(exec_line, icon_path))


def is_enabled():
    if app_platform.IS_LINUX:
        return os.path.isfile(linux_autostart_path())
    if app_platform.IS_WINDOWS:
        return os.path.isfile(windows_startup_path())
    return False


def set_enabled(enabled, icon_path=""):
    """Enable/disable login autostart. Return ``(ok, message)``."""
    main_py = main_py_path()
    if not os.path.isfile(main_py):
        return False, "找不到 main.py: %s" % main_py

    if app_platform.IS_LINUX:
        path = linux_autostart_path()
        if enabled:
            exec_line = "%s %s --minimized" % (python_executable(), main_py)
            _write(path, desktop_entry(exec_line, icon_path, autostart=True))
            ensure_launcher(icon_path)
            return True, "已写入 %s" % path
        if os.path.isfile(path):
            os.remove(path)
        return True, "已取消开机自启"

    if app_platform.IS_WINDOWS:
        path = windows_startup_path()
        if enabled:
            line = '@echo off\r\nstart "" "%s" "%s" --minimized\r\n' % (
                python_executable(),
                main_py,
            )
            _write(path, line)
            return True, "已写入 %s" % path
        if os.path.isfile(path):
            os.remove(path)
        return True, "已取消开机自启"

    return False, "当前平台不支持自动配置开机自启"
