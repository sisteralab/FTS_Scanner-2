from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from fts_scanner.presentation.controller import MainController


class SetupTab(QWidget):
    """Setup tab for connection addresses and device initialization."""

    def __init__(self, controller: MainController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller

        layout = QVBoxLayout(self)

        conn_box = QGroupBox("Connection Settings", self)
        conn_form = QFormLayout(conn_box)

        self.simulation_checkbox = QCheckBox("Simulation mode", conn_box)
        self.simulation_checkbox.setChecked(True)

        self.lockin_resource_edit = QLineEdit(conn_box)
        self.lockin_resource_edit.setText(self._controller.config.lock_in_resource)

        self.motor_name_edit = QLineEdit(conn_box)
        self.motor_name_edit.setText(self._controller.config.motor_name or "")

        self.ximc_path_edit = QLineEdit(conn_box)
        self.ximc_path_edit.setText(str(self._controller.config.ximc_root))

        conn_form.addRow(self.simulation_checkbox)
        conn_form.addRow("Lock-In VISA resource", self.lockin_resource_edit)
        conn_form.addRow("Motor name", self.motor_name_edit)
        conn_form.addRow("XIMC path", self.ximc_path_edit)

        layout.addWidget(conn_box)

        actions = QHBoxLayout()
        self.init_button = QPushButton("Initialize / Test", self)
        actions.addWidget(self.init_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        status_box = QGroupBox("Connection Status", self)
        status_form = QFormLayout(status_box)
        self.motor_status_label = QLabel("Unknown", status_box)
        self.lockin_status_label = QLabel("Unknown", status_box)
        self.summary_label = QLabel("Not initialized", status_box)
        status_form.addRow("Motor", self.motor_status_label)
        status_form.addRow("Lock-In", self.lockin_status_label)
        status_form.addRow("Summary", self.summary_label)
        layout.addWidget(status_box)
        layout.addStretch(1)

        self.init_button.clicked.connect(self._on_initialize_clicked)
        self._controller.setup_status.connect(self._on_setup_status)

    def _on_initialize_clicked(self) -> None:
        self._controller.initialize_devices(
            use_simulation=self.simulation_checkbox.isChecked(),
            lock_in_resource=self.lockin_resource_edit.text(),
            motor_name=self.motor_name_edit.text(),
            ximc_root=self.ximc_path_edit.text(),
        )

    def _on_setup_status(self, motor_ok: bool, lockin_ok: bool, message: str) -> None:
        self.motor_status_label.setText("Connected" if motor_ok else "Failed")
        self.lockin_status_label.setText("Connected" if lockin_ok else "Failed")
        self.motor_status_label.setStyleSheet(
            "color: #1e7f35;" if motor_ok else "color: #b22323;"
        )
        self.lockin_status_label.setStyleSheet(
            "color: #1e7f35;" if lockin_ok else "color: #b22323;"
        )
        self.summary_label.setText(message)
