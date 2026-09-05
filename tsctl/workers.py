# -*- coding: utf-8 -*-
"""Reusable one-shot background task for blocking system operations."""
from __future__ import print_function

from PyQt5.QtCore import QThread, pyqtSignal


class TaskWorker(QThread):
    succeeded = pyqtSignal(str, object)
    failed = pyqtSignal(str, str)

    def __init__(self, task_id, function, parent=None):
        super(TaskWorker, self).__init__(parent)
        self.task_id = task_id
        self.function = function

    def run(self):
        try:
            self.succeeded.emit(self.task_id, self.function())
        except Exception as exc:
            self.failed.emit(self.task_id, str(exc))
