from __future__ import annotations

from typing import Optional

from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import QAbstractItemView, QMessageBox

from fts_scanner.presentation.widgets.comment_dialog import CommentDialog
from fts_scanner.presentation.widgets.data_view_dialog import DataViewDialog
from fts_scanner.store.measure_store import MeasureModel


class MeasureTableView(QtWidgets.QTableView):
    """Table view with context actions for stored measurements."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        self._menu = QtWidgets.QMenu(self)
        self._action_comment = self._menu.addAction("Comment")
        self._action_view = self._menu.addAction("View")
        self._action_save = self._menu.addAction("Save")
        self._action_delete = self._menu.addAction("Delete")

        self._action_comment.triggered.connect(self.comment_selected_row)
        self._action_view.triggered.connect(self.view_selected_row)
        self._action_save.triggered.connect(self.save_selected_row)
        self._action_delete.triggered.connect(self.delete_selected_row)

    def _show_context_menu(self, pos: QtCore.QPoint) -> None:
        self._menu.exec(self.mapToGlobal(pos))

    def _selected_row(self) -> int | None:
        selection = self.selectionModel()
        if selection is None:
            return None
        rows = list({index.row() for index in selection.selectedIndexes()})
        return rows[0] if rows else None

    def save_selected_row(self) -> None:
        model = self.model()
        row = self._selected_row()
        if model is None or row is None:
            return
        model.manager.save_by_index(row)

    def get_selected_measure_model(self) -> Optional[MeasureModel]:
        model = self.model()
        row = self._selected_row()
        if model is None or row is None:
            return None
        measure_model_id = model._data[row][0]
        return model.manager.get(id=measure_model_id)

    def comment_selected_row(self) -> None:
        measure_model = self.get_selected_measure_model()
        if measure_model is None:
            return

        dialog = CommentDialog(self, measure_model.comment)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            measure_model.comment = dialog.comment_edit.toPlainText()
            measure_model.objects.update_table()

    def view_selected_row(self) -> None:
        measure_model = self.get_selected_measure_model()
        if measure_model is None:
            return

        dialog = DataViewDialog(self, measure_model.to_json())
        dialog.exec()

    def delete_selected_row(self) -> None:
        model = self.model()
        row = self._selected_row()
        if model is None or row is None:
            return

        measure = model.manager.all()[row]
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Deleting data")
        dlg.setText(
            f"Are you sure you want to delete measurement "
            f"'{measure.type_display} {measure.finished}'?"
        )
        dlg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        dlg.setIcon(QMessageBox.Icon.Question)

        if dlg.exec() == QMessageBox.StandardButton.Yes:
            model.manager.delete_by_index(row)
