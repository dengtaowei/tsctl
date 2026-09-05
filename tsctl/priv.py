# -*- coding: utf-8 -*-
"""Install passwordless start/stop for tailscaled (Linux).

Ubuntu 18.04/20.04 ship polkit 0.105, which cannot narrowly allow a single
systemd unit via JS rules. We therefore install a *minimal* sudoers drop-in
that only permits systemctl start|stop|restart tailscaled for the current
user. On newer polkit we also drop a rules.d file for the same verbs.
"""
from __future__ import print_function

import getpass
import os
import tempfile

from tsctl import platform as app_platform
from tsctl.runner import run


IS_LINUX = app_platform.IS_LINUX

SUDOERS_PATH = "/etc/sudoers.d/tsctl-tailscaled"
POLKIT_RULES_PATH = "/etc/polkit-1/rules.d/49-tsctl-tailscaled.rules"


def _run(cmd, timeout=120):
    """Compatibility wrapper returning (returncode, stdout, stderr)."""
    return run(cmd, timeout=timeout)


def systemctl_path():
    return app_platform.systemctl_path()


def has_passwordless_tailscaled():
    """True if sudoers/polkit already allows passwordless start/stop of tailscaled."""
    if not IS_LINUX:
        return True
    # NOPASSWD is only for start|stop|restart — do not probe with status.
    # sudo -n -l lists allowed commands without needing a password when cached/rules exist.
    code, out, err = _run(["sudo", "-n", "-l"], timeout=15)
    text = (out or "") + (err or "")
    low = text.lower()
    if "password is required" in low or "a terminal is required" in low:
        return False
    if code != 0:
        return False
    if "tailscaled" not in low:
        return False
    # Prefer explicit NOPASSWD match; some locales still print the path
    return "nopasswd" in low or "start tailscaled" in low


def _sudoers_body(user, ctl):
    # List both resolved path and common aliases so matching is reliable
    paths = {ctl, "/usr/bin/systemctl", "/bin/systemctl"}
    lines = [
        "# Written by tsctl — allow passwordless control of tailscaled only",
        "# Do not edit by hand unless you know sudoers syntax",
    ]
    for p in sorted(paths):
        lines.append(
            "%s ALL=(root) NOPASSWD: %s start tailscaled, %s stop tailscaled, "
            "%s restart tailscaled"
            % (user, p, p, p)
        )
    lines.append("")
    return "\n".join(lines)


def _polkit_rules_body(user):
    # For polkit >= 0.106; ignored on Ubuntu 20.04 (0.105) but harmless if present
    return (
        "/* Written by tsctl — passwordless start/stop/restart tailscaled */\n"
        "polkit.addRule(function(action, subject) {\n"
        "    if (subject.user !== \"%s\") {\n"
        "        return;\n"
        "    }\n"
        "    if (action.id !== \"org.freedesktop.systemd1.manage-units\") {\n"
        "        return;\n"
        "    }\n"
        "    var unit = action.lookup(\"unit\");\n"
        "    var verb = action.lookup(\"verb\");\n"
        "    if (unit === \"tailscaled.service\" &&\n"
        "        (verb === \"start\" || verb === \"stop\" || verb === \"restart\")) {\n"
        "        return polkit.Result.YES;\n"
        "    }\n"
        "});\n"
        % user
    )


def install_passwordless(user=None):
    """
    Install sudoers (+ polkit rules when applicable) via pkexec.
    Returns (ok, message).
    """
    if not IS_LINUX:
        return True, "非 Linux，无需安装"
    user = user or getpass.getuser()
    ctl = systemctl_path()
    sudoers = _sudoers_body(user, ctl)
    polkit = _polkit_rules_body(user)

    # Write temp files then pkexec install
    td = tempfile.mkdtemp(prefix="tsctl-priv-")
    try:
        sudoers_tmp = os.path.join(td, "tsctl-tailscaled")
        polkit_tmp = os.path.join(td, "49-tsctl-tailscaled.rules")
        with open(sudoers_tmp, "w") as f:
            f.write(sudoers)
        with open(polkit_tmp, "w") as f:
            f.write(polkit)

        script = os.path.join(td, "install.sh")
        with open(script, "w") as f:
            f.write(
                "#!/bin/bash\n"
                "set -e\n"
                "install -m 440 '%s' '%s'\n"
                "if ! visudo -cf '%s'; then\n"
                "  rm -f '%s'\n"
                "  exit 1\n"
                "fi\n"
                "mkdir -p /etc/polkit-1/rules.d\n"
                "install -m 644 '%s' '%s'\n"
                "echo OK\n"
                % (
                    sudoers_tmp,
                    SUDOERS_PATH,
                    SUDOERS_PATH,
                    SUDOERS_PATH,
                    polkit_tmp,
                    POLKIT_RULES_PATH,
                )
            )
        os.chmod(script, 0o755)

        if app_platform.which("pkexec"):
            code, out, err = _run(["pkexec", script], timeout=180)
        else:
            code, out, err = _run(["sudo", script], timeout=180)

        if code != 0:
            return False, (err or out or "安装失败").strip()

        if not has_passwordless_tailscaled():
            return (
                True,
                "权限文件已写入，但当前会话尚未生效；请重新登录桌面后再试。"
                "\n已安装: %s" % SUDOERS_PATH,
            )
        return True, "已安装免密权限（仅限 systemctl start/stop/restart tailscaled）"
    finally:
        try:
            for name in os.listdir(td):
                try:
                    os.remove(os.path.join(td, name))
                except OSError:
                    pass
            os.rmdir(td)
        except OSError:
            pass


def uninstall_passwordless():
    """Remove sudoers/polkit files via pkexec. Returns (ok, message)."""
    if not IS_LINUX:
        return True, "非 Linux"
    script_body = (
        "#!/bin/bash\n"
        "rm -f %s %s\n"
        "echo OK\n" % (SUDOERS_PATH, POLKIT_RULES_PATH)
    )
    td = tempfile.mkdtemp(prefix="tsctl-priv-")
    try:
        script = os.path.join(td, "uninstall.sh")
        with open(script, "w") as f:
            f.write(script_body)
        os.chmod(script, 0o755)
        if app_platform.which("pkexec"):
            code, out, err = _run(["pkexec", script], timeout=120)
        else:
            code, out, err = _run(["sudo", script], timeout=120)
        if code != 0:
            return False, (err or out or "卸载失败").strip()
        return True, "已移除免密权限文件"
    finally:
        try:
            for name in os.listdir(td):
                try:
                    os.remove(os.path.join(td, name))
                except OSError:
                    pass
            os.rmdir(td)
        except OSError:
            pass


def explain_dialog_text():
    return (
        "「启动时自动启动 Tailscale」需要能免密启停服务，否则无人值守时会卡住密码框。\n\n"
        "Ubuntu 20.04 等旧版 polkit（0.105）无法只放行某一个 systemd 单元，"
        "因此安装「最小免密权限」：\n"
        "• /etc/sudoers.d/tsctl-tailscaled\n"
        "  仅允许当前用户：systemctl start|stop|restart tailscaled\n"
        "• /etc/polkit-1/rules.d/49-tsctl-tailscaled.rules\n"
        "  （新版 polkit 可用；旧版可忽略）\n\n"
        "不会放行其它系统命令。安装时会弹出一次管理员密码；"
        "之后启停与登录自启均可免密。\n\n"
        "是否现在安装？"
    )
