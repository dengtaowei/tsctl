# -*- coding: utf-8 -*-
"""Peer list widget."""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem

from tsctl import theme


class PeersTable(QTableWidget):
    ip_copied = pyqtSignal(str)

    def __init__(self, parent=None):
        super(PeersTable, self).__init__(0, 5, parent)
        self.setHorizontalHeaderLabels(["名称", "IP", "系统", "状态", "路径"])
        header = self.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(38)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setShowGrid(False)
        self.setFocusPolicy(Qt.NoFocus)
        self.setWordWrap(False)
        self.setTextElideMode(Qt.ElideRight)
        self.doubleClicked.connect(self._copy_ip)

    def set_peers(self, peers):
        self.setRowCount(0)
        for peer in peers:
            row = self.rowCount()
            self.insertRow(row)
            if peer.is_self:
                status = "本机"
            elif peer.online and peer.active:
                status = "在线 / 活跃"
            elif peer.online:
                status = "在线"
            else:
                status = "离线"
            values = [peer.name, peer.ip, peer.os, status, peer.path]
            for column, text in enumerate(values):
                item = QTableWidgetItem(text)
                if column == 1:
                    item.setData(Qt.UserRole, peer.ip)
                    item.setForeground(QColor(theme.ACCENT))
                elif column == 3 and (peer.online or peer.is_self):
                    item.setForeground(QColor(theme.SUCCESS))
                elif not peer.online and not peer.is_self:
                    item.setForeground(QColor(theme.MUTED))
                if peer.is_self and column == 0:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                self.setItem(row, column, item)
        self.resizeColumnToContents(1)
        if self.columnWidth(1) < 128:
            self.setColumnWidth(1, 128)

    def _copy_ip(self, index):
        item = self.item(index.row(), 1)
        if not item:
            return
        ip = item.data(Qt.UserRole) or item.text()
        if ip:
            self.ip_copied.emit(ip)
