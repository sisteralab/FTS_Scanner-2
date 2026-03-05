from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QTextEdit


class CommentDialog(QDialog):
    """Dialog for editing measurement comment."""

    def __init__(self, parent=None, text: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit comment")

        self.comment_edit = QTextEdit(self)
        self.comment_edit.setPlainText(text)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.comment_edit)
        layout.addWidget(buttons)
