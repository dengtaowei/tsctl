# -*- coding: utf-8 -*-
"""Core data models shared by the backend and future frontends."""
from __future__ import print_function

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Peer:
    """One node from a Tailscale status snapshot."""

    name: str
    ip: str
    os: str
    online: bool
    active: bool
    path: str
    is_self: bool = False


@dataclass(frozen=True)
class StatusSnapshot:
    """A coherent view derived from one Tailscale status query."""

    cli_path: Optional[str]
    running: bool
    ipv4: str = ""
    peers: List[Peer] = field(default_factory=list)
    raw_display: str = ""
    backend_state: Optional[str] = None
    status_data: Optional[Dict[str, Any]] = None
    error: str = ""


@dataclass
class AppState:
    """Single mutable application state owned by ``AppController``."""

    snapshot: StatusSnapshot = field(
        default_factory=lambda: StatusSnapshot(cli_path=None, running=False)
    )
    app_autostart: bool = False
    start_on_launch: bool = False
    started_by_us: bool = False
    busy: bool = False
    busy_message: str = ""
    message: str = ""
    message_level: str = "info"
    shutting_down: bool = False
