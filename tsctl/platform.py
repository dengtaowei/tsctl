# -*- coding: utf-8 -*-
"""Small, dependency-free platform and executable discovery helpers."""
from __future__ import print_function

import os
import platform as stdlib_platform
import shutil
import sys


IS_WINDOWS = sys.platform.startswith("win")
IS_LINUX = sys.platform.startswith("linux")


def system_name():
    """Return the host operating-system name."""
    return stdlib_platform.system()


def which(command):
    """Return the executable path for *command*, if it is available."""
    return shutil.which(command)


def config_home():
    if IS_WINDOWS:
        return os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.environ.get("XDG_CONFIG_HOME") or os.path.join(
        os.path.expanduser("~"), ".config"
    )


def data_home():
    if IS_WINDOWS:
        return os.environ.get("LOCALAPPDATA") or config_home()
    return os.environ.get("XDG_DATA_HOME") or os.path.join(
        os.path.expanduser("~"), ".local", "share"
    )


def find_tailscale():
    """Locate the Tailscale CLI on Linux or Windows."""
    path = which("tailscale")
    if path:
        return path
    if IS_WINDOWS:
        candidates = [
            os.path.join(
                os.environ.get("ProgramFiles", r"C:\Program Files"),
                "Tailscale",
                "tailscale.exe",
            ),
            os.path.join(
                os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
                "Tailscale",
                "tailscale.exe",
            ),
        ]
        for candidate in candidates:
            if os.path.isfile(candidate):
                return candidate
    return None


def systemctl_path():
    """Return the installed systemctl path or its conventional location."""
    return which("systemctl") or "/usr/bin/systemctl"
