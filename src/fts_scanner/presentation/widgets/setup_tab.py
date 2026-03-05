from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from fts_scanner.devices.thzdaqapi_lockin import LockInAdapterType
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
        self.simulation_checkbox.setChecked(False)

        self.lockin_adapter_combo = QComboBox(conn_box)
        self.lockin_adapter_combo.addItem("Prologix Ethernet", LockInAdapterType.PROLOGIX_ETHERNET)
        self.lockin_adapter_combo.addItem("Prologix USB", LockInAdapterType.PROLOGIX_USB)
        self.lockin_adapter_combo.addItem("VISA (legacy)", "visa")

        current_adapter = self._controller.config.lock_in_adapter
        index = self.lockin_adapter_combo.findData(current_adapter)
        if index >= 0:
            self.lockin_adapter_combo.setCurrentIndex(index)

        self.lockin_host_edit = QLineEdit(conn_box)
        self.lockin_host_edit.setText(self._controller.config.lock_in_host)

        self.lockin_port_spin = QSpinBox(conn_box)
        self.lockin_port_spin.setRange(1, 65535)
        self.lockin_port_spin.setValue(self._controller.config.lock_in_port)

        self.lockin_usb_port_edit = QLineEdit(conn_box)
        self.lockin_usb_port_edit.setText(self._controller.config.lock_in_usb_port)

        self.lockin_gpib_spin = QSpinBox(conn_box)
        self.lockin_gpib_spin.setRange(0, 30)
        self.lockin_gpib_spin.setValue(self._controller.config.lock_in_gpib_address)

        self.lockin_resource_edit = QLineEdit(conn_box)
        self.lockin_resource_edit.setText(self._controller.config.lock_in_resource)

        self.thzdaqapi_path_edit = QLineEdit(conn_box)
        self.thzdaqapi_path_edit.setText(str(self._controller.config.thzdaqapi_src))

        self.motor_name_edit = QLineEdit(conn_box)
        self.motor_name_edit.setText(self._controller.config.motor_name or "")

        self.ximc_path_edit = QLineEdit(conn_box)
        self.ximc_path_edit.setText(str(self._controller.config.ximc_root))

        conn_form.addRow(self.simulation_checkbox)
        conn_form.addRow("Lock-In adapter", self.lockin_adapter_combo)
        conn_form.addRow("Prologix host", self.lockin_host_edit)
        conn_form.addRow("Prologix ethernet port", self.lockin_port_spin)
        conn_form.addRow("Prologix USB serial port", self.lockin_usb_port_edit)
        conn_form.addRow("Lock-In GPIB address", self.lockin_gpib_spin)
        conn_form.addRow("Lock-In VISA resource", self.lockin_resource_edit)
        conn_form.addRow("thzdaqapi src path", self.thzdaqapi_path_edit)
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
        self.summary_label.setWordWrap(True)
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
            lock_in_adapter=str(self.lockin_adapter_combo.currentData()),
            lock_in_host=self.lockin_host_edit.text(),
            lock_in_port=self.lockin_port_spin.value(),
            lock_in_usb_port=self.lockin_usb_port_edit.text(),
            lock_in_gpib_address=self.lockin_gpib_spin.value(),
            thzdaqapi_src=self.thzdaqapi_path_edit.text(),
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
