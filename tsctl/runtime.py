# -*- coding: utf-8 -*-
"""Runtime path helpers for source runs and frozen builds."""
from __future__ import print_function

import os
import sys

from tsctl import platform as app_platform


def is_frozen():
    return bool(getattr(sys, "frozen", False))


def project_root():
    """Directory that contains the app package / binary."""
    if is_frozen():
        return os.path.dirname(os.path.abspath(sys.executable))
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, ".."))


def writable_data_dir():
    """User-writable data (icons cache etc.)."""
    return os.path.join(app_platform.data_home(), "tsctl")


def launch_command(extra_args=None):
    """Command list used by desktop entries / Startup scripts."""
    extra_args = list(extra_args or [])
    if is_frozen():
        return [os.path.abspath(sys.executable)] + extra_args
    return [
        os.path.abspath(sys.executable),
        os.path.join(project_root(), "main.py"),
    ] + extra_args


def launch_exec_line(extra_args=None):
    """Shell Exec= line for .desktop files."""
    parts = []
    for part in launch_command(extra_args):
        if " " in part:
            parts.append('"%s"' % part)
        else:
            parts.append(part)
    return " ".join(parts)
