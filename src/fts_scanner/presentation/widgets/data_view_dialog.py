from __future__ import annotations

import json
from typing import Any

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QPlainTextEdit, QVBoxLayout


class DataViewDialog(QDialog):
    """Dialog showing full measurement payload as JSON."""

    def __init__(self, parent=None, payload: dict[str, Any] | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Measurement data")
        self.resize(700, 500)

        viewer = QPlainTextEdit(self)
        viewer.setReadOnly(True)
        viewer.setPlainText(json.dumps(payload or {}, ensure_ascii=False, indent=2))

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, parent=self)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(viewer)
        layout.addWidget(buttons)
