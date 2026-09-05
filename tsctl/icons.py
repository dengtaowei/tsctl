# -*- coding: utf-8 -*-
"""Application and tray icon generation."""
from __future__ import print_function

import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QIcon, QPainter, QPixmap


def project_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, ".."))


def icon_png_path():
    """Cached PNG used by window chrome and .desktop Icon=."""
    d = os.path.join(project_root(), "icons")
    return os.path.join(d, "tsctl.png")


def make_app_icon():
    """Brand icon: green disc + TS (also used when PNG not yet written)."""
    size = 256
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor("#0ea5e9"))
    p.setPen(Qt.NoPen)
    p.drawEllipse(8, 8, size - 16, size - 16)
    p.setBrush(QColor("#22c55e"))
    p.drawEllipse(48, 48, size - 96, size - 96)
    p.setPen(QColor("#ffffff"))
    font = QFont("Sans Serif")
    font.setBold(True)
    font.setPixelSize(96)
    p.setFont(font)
    p.drawText(pm.rect(), Qt.AlignCenter, "TS")
    p.end()
    return QIcon(pm)


def ensure_icon_png():
    """Write icons/tsctl.png if missing or empty. Returns path."""
    path = icon_png_path()
    d = os.path.dirname(path)
    if not os.path.isdir(d):
        os.makedirs(d)
    if os.path.isfile(path) and os.path.getsize(path) > 0:
        return path
    icon = make_app_icon()
    pm = icon.pixmap(256, 256)
    pm.save(path, "PNG")
    return path


def load_app_icon():
    path = ensure_icon_png()
    icon = QIcon(path)
    if icon.isNull():
        return make_app_icon()
    return icon


def make_tray_icon(running):
    """Create a compact status icon for the system tray."""
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#0066FF" if running else "#A3A3A3"))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(4, 4, size - 8, size - 8)
    painter.setBrush(QColor("#059669" if running else "#E5E5E5"))
    painter.drawEllipse(16, 16, size - 32, size - 32)
    painter.end()
    return QIcon(pixmap)
