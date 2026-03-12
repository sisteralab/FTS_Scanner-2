from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
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

from fts_scanner.devices.lockin_types import LOCKIN_ADAPTER_LABELS, LockInAdapterType
from fts_scanner.presentation.controller import MainController


class SetupTab(QWidget):
    """Setup tab for connection addresses and device initialization."""

    def __init__(self, controller: MainController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller

        layout = QVBoxLayout(self)

        conn_box = QGroupBox("Connection Settings", self)
        self._conn_form = QFormLayout(conn_box)

        self.simulation_checkbox = QCheckBox("Simulation mode", conn_box)
        self.simulation_checkbox.setChecked(self._controller.config.use_simulation)

        self.lockin_adapter_combo = QComboBox(conn_box)
        for value, text in LOCKIN_ADAPTER_LABELS.items():
            self.lockin_adapter_combo.addItem(text, value)

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

        self.lockin_visa_resource_edit = QLineEdit(conn_box)
        self.lockin_visa_resource_edit.setText(self._controller.config.lock_in_visa_resource)

        self.lockin_visa_library_edit = QLineEdit(conn_box)
        self.lockin_visa_library_edit.setText(self._controller.config.lock_in_visa_library)
        self.lockin_visa_library_edit.setPlaceholderText("Optional, e.g. /Library/Frameworks/VISA.framework/VISA")

        self.motor_name_edit = QLineEdit(conn_box)
        self.motor_name_edit.setText(self._controller.config.motor_name or "")

        self.ximc_path_edit = QLineEdit(conn_box)
        self.ximc_path_edit.setText(str(self._controller.config.ximc_root))
        self.ximc_browse_button = QPushButton("Browse...", conn_box)
        ximc_row_widget = QWidget(conn_box)
        ximc_row_layout = QHBoxLayout(ximc_row_widget)
        ximc_row_layout.setContentsMargins(0, 0, 0, 0)
        ximc_row_layout.addWidget(self.ximc_path_edit, 1)
        ximc_row_layout.addWidget(self.ximc_browse_button, 0)

        self._conn_form.addRow(self.simulation_checkbox)
        self._conn_form.addRow("Lock-In adapter", self.lockin_adapter_combo)
        self._conn_form.addRow("Prologix host", self.lockin_host_edit)
        self._conn_form.addRow("Prologix ethernet port", self.lockin_port_spin)
        self._conn_form.addRow("Prologix USB serial port", self.lockin_usb_port_edit)
        self._conn_form.addRow("Lock-In GPIB address", self.lockin_gpib_spin)
        self._conn_form.addRow("VISA resource", self.lockin_visa_resource_edit)
        self._conn_form.addRow("VISA library", self.lockin_visa_library_edit)
        self._conn_form.addRow("Motor name", self.motor_name_edit)
        self._conn_form.addRow("XIMC path", ximc_row_widget)

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
        self.ximc_browse_button.clicked.connect(self._on_browse_ximc)
        self.lockin_adapter_combo.currentIndexChanged.connect(self._update_adapter_fields)
        self.simulation_checkbox.toggled.connect(self._update_adapter_fields)
        self._controller.setup_status.connect(self._on_setup_status)

        self._update_adapter_fields()

    def _on_initialize_clicked(self) -> None:
        self._controller.initialize_devices(
            use_simulation=self.simulation_checkbox.isChecked(),
            lock_in_adapter=str(self.lockin_adapter_combo.currentData()),
            lock_in_host=self.lockin_host_edit.text(),
            lock_in_port=self.lockin_port_spin.value(),
            lock_in_usb_port=self.lockin_usb_port_edit.text(),
            lock_in_gpib_address=self.lockin_gpib_spin.value(),
            lock_in_visa_resource=self.lockin_visa_resource_edit.text(),
            lock_in_visa_library=self.lockin_visa_library_edit.text(),
            motor_name=self.motor_name_edit.text(),
            ximc_root=self.ximc_path_edit.text(),
        )

    def _update_adapter_fields(self) -> None:
        adapter = str(self.lockin_adapter_combo.currentData())
        simulated = self.simulation_checkbox.isChecked()

        is_eth = adapter == LockInAdapterType.PROLOGIX_ETHERNET
        is_usb = adapter == LockInAdapterType.PROLOGIX_USB
        is_visa = adapter == LockInAdapterType.KEYSIGHT_VISA

        self._set_row_visible(self.lockin_host_edit, is_eth and not simulated)
        self._set_row_visible(self.lockin_port_spin, is_eth and not simulated)
        self._set_row_visible(self.lockin_usb_port_edit, is_usb and not simulated)
        self._set_row_visible(self.lockin_gpib_spin, (is_eth or is_usb) and not simulated)
        self._set_row_visible(self.lockin_visa_resource_edit, is_visa and not simulated)
        self._set_row_visible(self.lockin_visa_library_edit, is_visa and not simulated)

    def _set_row_visible(self, field: QWidget, visible: bool) -> None:
        label = self._conn_form.labelForField(field)
        if label is not None:
            label.setVisible(visible)
        field.setVisible(visible)

    def _on_browse_ximc(self) -> None:
        current = self.ximc_path_edit.text().strip() or "."
        selected = QFileDialog.getExistingDirectory(self, "Select XIMC folder", current)
        if selected:
            self.ximc_path_edit.setText(selected)

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
