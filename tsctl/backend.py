# -*- coding: utf-8 -*-
"""Cross-platform helpers around the installed Tailscale CLI/service."""
from __future__ import print_function

import json
import time

from tsctl import platform as app_platform
from tsctl.models import Peer, StatusSnapshot
from tsctl.runner import run


IS_WINDOWS = app_platform.IS_WINDOWS
IS_LINUX = app_platform.IS_LINUX

def _which_tailscale():
    """Compatibility alias for the centralized platform helper."""
    return app_platform.find_tailscale()


def _run(cmd, timeout=60):
    """Compatibility wrapper returning (returncode, stdout, stderr)."""
    return run(cmd, timeout=timeout)


def find_tailscale():
    return app_platform.find_tailscale()


def _first_ipv4(ips):
    if not ips:
        return ""
    for ip in ips:
        if ip and ":" not in ip:
            return ip
    return ips[0] if ips else ""


def _peer_path(p):
    """Human-readable path: direct address, relay, or idle."""
    cur = p.get("CurAddr") or ""
    if cur:
        return "direct %s" % cur
    relay = p.get("Relay") or ""
    if relay and p.get("Active"):
        return "DERP(%s)" % relay
    if relay:
        return "relay %s" % relay
    if p.get("Online"):
        return "idle"
    return "—"


def _peers_from_status(data):
    peers = []
    self_p = data.get("Self") or {}
    peers.append(
        Peer(
            name=self_p.get("HostName") or "self",
            ip=_first_ipv4(self_p.get("TailscaleIPs") or []),
            os=self_p.get("OS") or "",
            online=bool(self_p.get("Online", True)),
            active=True,
            path="(本机)",
            is_self=True,
        )
    )

    items = list((data.get("Peer") or {}).values())
    items.sort(key=lambda p: (not p.get("Online"), (p.get("HostName") or "").lower()))
    for p in items:
        name = p.get("HostName") or p.get("DNSName") or "?"
        if isinstance(name, str) and name.endswith("."):
            name = name.rstrip(".")
        peers.append(
            Peer(
                name=name,
                ip=_first_ipv4(p.get("TailscaleIPs") or []),
                os=p.get("OS") or "",
                online=bool(p.get("Online")),
                active=bool(p.get("Active")),
                path=_peer_path(p),
                is_self=False,
            )
        )
    return peers


def _status_display(peers, backend_state):
    """Build compact display text without issuing a second CLI query."""
    if not peers:
        return backend_state or "(空)"
    lines = []
    for peer in peers:
        state = "active" if peer.active else ("online" if peer.online else "offline")
        lines.append(
            "%-15s  %-28s  %-8s  %s"
            % (peer.ip or "-", peer.name, state, peer.path)
        )
    return "\n".join(lines)


def _systemd_running():
    if not IS_LINUX:
        return None
    result = run(
        [app_platform.which("systemctl") or "systemctl", "is-active", "tailscaled"],
        timeout=3,
    )
    state = result.stdout.strip()
    if result.returncode == 0 and state == "active":
        return True
    if state in ("inactive", "failed", "dead", "deactivating"):
        return False
    return None


def fetch_snapshot():
    """Fetch one coherent status snapshot.

    A successful call derives daemon state, local IPv4, peers, and display text
    from the same ``tailscale status --json`` response. Systemd is consulted
    only when that response cannot establish whether the daemon is available.
    """
    ts = app_platform.find_tailscale()
    if not ts:
        snapshot = StatusSnapshot(
            cli_path=None,
            running=False,
            raw_display="未找到 tailscale 命令。请先安装 Tailscale。",
            error="no tailscale",
        )
    else:
        result = run([ts, "status", "--json"], timeout=15)
        data = None
        parse_error = ""
        if result.returncode == 0 and result.stdout.strip():
            try:
                data = json.loads(result.stdout)
            except ValueError:
                parse_error = "bad json"

        if data is not None:
            peers = _peers_from_status(data)
            backend_state = data.get("BackendState")
            snapshot = StatusSnapshot(
                cli_path=ts,
                running=True,
                ipv4=_first_ipv4((data.get("Self") or {}).get("TailscaleIPs") or []),
                peers=peers,
                raw_display=_status_display(peers, backend_state),
                backend_state=backend_state,
                status_data=data,
            )
        else:
            message = (result.stderr or result.stdout or parse_error).strip()
            running = _systemd_running()
            if running is None:
                low = message.lower()
                running = (
                    "logged out" in low
                    or "stopped" in low
                ) and not (
                    "doesn't appear to be running" in low
                    or "not running" in low
                    or "failed to connect" in low
                )
            snapshot = StatusSnapshot(
                cli_path=ts,
                running=bool(running),
                raw_display=message
                or ("tailscale status 失败, code=%s" % result.returncode),
                error=message or "status failed",
            )

    return snapshot


def _linux_systemctl(action, allow_interactive=True):
    """action: start|stop|restart — prefer passwordless sudo.

    Do NOT fall back to plain ``systemctl``: without rights it waits on a
    polkit password dialog and freezes the GUI worker for up to the timeout.
    Interactive path uses pkexec only when allow_interactive is True.
    """
    ctl = app_platform.which("systemctl") or "systemctl"
    if action not in ("start", "stop", "restart"):
        return _run([ctl, action, "tailscaled"], timeout=15)

    code, out, err = _run(["sudo", "-n", ctl, action, "tailscaled"], timeout=30)
    if code == 0:
        return code, out, err

    sudo_msg = (err or out or "").strip()
    if allow_interactive and app_platform.which("pkexec"):
        code2, out2, err2 = _run(
            ["pkexec", ctl, action, "tailscaled"], timeout=90
        )
        if code2 == 0:
            return code2, out2, err2
        return code2, out2, (err2 or out2 or sudo_msg or "pkexec 失败").strip()

    hint = sudo_msg or "需要管理员权限"
    if "password" in hint.lower() or code != 0:
        hint += (
            "\n请在工具中勾选「启动时自动启动」并安装免密权限，"
            "或手动: sudo systemctl %s tailscaled" % action
        )
    return code, out, hint


def _windows_service(action):
    """action: start|stop|query"""
    if action == "query":
        return _run(["sc", "query", "Tailscale"], timeout=30)
    # net start/stop needs admin elevation on some setups
    verb = "start" if action == "start" else "stop"
    return _run(["net", verb, "Tailscale"], timeout=60)


def _backend_state(ts=None):
    """Return (BackendState or None, err_text). Uses status --json."""
    ts = ts or _which_tailscale()
    if not ts:
        return None, "no tailscale"
    code, out, err = _run([ts, "status", "--json"], timeout=4)
    if code != 0:
        return None, (err or out or "").strip()
    try:
        data = json.loads(out or "{}")
    except ValueError:
        return None, "bad json"
    return data.get("BackendState"), ""


def _wait_backend_state(ts, timeout_s=8.0):
    """Poll until status --json answers or timeout. Return BackendState or None."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        state, _error = _backend_state(ts)
        if state:
            return state
        time.sleep(0.25)
    return None


def start_tailscale(interactive=True):
    """Start daemon (and bring link up when possible). Returns (ok, message).

    interactive=False: never pop pkexec (for login autostart / quiet start).
    """
    ts = _which_tailscale()
    if not ts:
        return False, "未找到 tailscale，请先安装官方客户端。"

    if IS_LINUX:
        code, out, err = _linux_systemctl("start", allow_interactive=interactive)
        if code != 0:
            return False, (err or out or "systemctl start 失败").strip()

        # Daemon often restores the last session by itself after start.
        # Wait for the socket, then skip `up` when already Running — calling
        # `up` immediately after start can block until our timeout even though
        # the node is fine (race with daemon init / prefs lock).
        state = _wait_backend_state(ts, timeout_s=8.0)
        if state == "Running":
            return True, "已启动 tailscaled"
        if state == "NeedsLogin":
            return (
                True,
                "服务已启动，但尚未登录。请在终端执行: tailscale up",
            )

        c2, o2, e2 = _run([ts, "up"], timeout=15)
        if c2 == 0 or "already" in ((o2 + e2).lower()):
            return True, "已启动 tailscaled"
        up_err = (e2 or o2).strip()
        if "access denied" in up_err.lower() or "prefs write" in up_err.lower():
            # If status became Running anyway, treat as OK
            st2, _ = _backend_state(ts)
            if st2 == "Running":
                return True, "已启动 tailscaled（up 无写 prefs 权限，可忽略）"
            return (
                True,
                "服务已启动，但 tailscale up 无权限。\n"
                "请执行一次: sudo tailscale set --operator=$USER\n"
                "详情: %s" % up_err,
            )
        st3, _ = _backend_state(ts)
        if st3 == "Running":
            return True, "已启动 tailscaled"
        if c2 == 124 or "timeout" in up_err.lower():
            return (
                True,
                "服务已启动；tailscale up 未在时限内返回"
                "（节点若已在列表中可忽略）",
            )
        return True, "服务已启动；tailscale up: %s" % up_err

    if IS_WINDOWS:
        code, out, err = _windows_service("start")
        # 2 often means already running
        if code not in (0, 2) and "already been started" not in (out + err):
            # Still try up — service may already be running
            pass
        state = _wait_backend_state(ts, timeout_s=8.0)
        if state == "Running":
            return True, "已启动 / 已连接"
        c2, o2, e2 = _run([ts, "up"], timeout=20)
        if c2 != 0:
            return False, (e2 or o2 or "tailscale up 失败").strip()
        return True, "已启动 / 已连接"

    return False, "不支持的平台: %s" % app_platform.system_name()


def stop_tailscale(interactive=True):
    """Stop connectivity. Linux stops daemon; Windows prefers down."""
    ts = _which_tailscale()
    if not ts:
        return False, "未找到 tailscale。"

    if IS_LINUX:
        code, out, err = _linux_systemctl("stop", allow_interactive=interactive)
        if code != 0:
            return False, (err or out or "systemctl stop 失败").strip()
        return True, "已停止 tailscaled"

    if IS_WINDOWS:
        c1, o1, e1 = _run([ts, "down"], timeout=30)
        if c1 != 0:
            return False, (e1 or o1 or "tailscale down 失败").strip()
        return True, "已断开 (tailscale down)"

    return False, "不支持的平台: %s" % app_platform.system_name()


def platform_hint():
    if IS_LINUX:
        return "关闭窗口进入托盘 · 托盘「退出」结束进程"
    if IS_WINDOWS:
        return "关闭窗口进入托盘 · 停止使用 tailscale down"
    return app_platform.system_name()
