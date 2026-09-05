# -*- coding: utf-8 -*-
"""Unified subprocess execution for tsctl."""
from __future__ import print_function

import subprocess
from collections import namedtuple


CommandResult = namedtuple("CommandResult", "returncode stdout stderr")


def run(command, timeout=60):
    """Run a command and return a :class:`CommandResult`.

    Missing executables and timeouts retain the legacy return codes used by
    tsctl: 127 and 124 respectively.
    """
    try:
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            universal_newlines=True,
        )
        return CommandResult(
            process.returncode,
            process.stdout or "",
            process.stderr or "",
        )
    except OSError as exc:
        return CommandResult(127, "", str(exc))
    except subprocess.TimeoutExpired:
        return CommandResult(124, "", "timeout")
