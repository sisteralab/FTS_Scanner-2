from __future__ import annotations

import datetime

import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from fts_scanner.domain.models import STAGE_STEP_UM, ScanSettings
from fts_scanner.presentation.controller import MainController
from fts_scanner.presentation.widgets.table_view import MeasureTableView
from fts_scanner.store.measure_store import MeasureManager, MeasureTableModel


class MainWindow(QMainWindow):
    """Main application view for FTS initialization, monitor and measurements."""

    def __init__(self, controller: MainController) -> None:
        super().__init__()
        self._controller = controller

        self.setWindowTitle("FTS Scanner")
        self.resize(1300, 800)

        self._measurement_x: list[int] = []
        self._measurement_y: list[float] = []
        self._current_repeat: int = 0
        self._active_scan_settings: ScanSettings | None = None

        root = QWidget(self)
        self.setCentralWidget(root)

        main_layout = QHBoxLayout(root)

        controls = self._build_controls()
        main_layout.addWidget(controls, 0)

        right_side = QVBoxLayout()
        main_layout.addLayout(right_side, 1)

        plot_layout = QHBoxLayout()
        right_side.addLayout(plot_layout, 3)

        self.plot_widget = pg.PlotWidget(self)
        self.plot_widget.setBackground("w")
        self.plot_widget.setTitle("Interferogram")
        self.plot_widget.setLabel("left", "Signal")
        self.plot_widget.setLabel("bottom", "Position (steps)")
        self.plot_widget.showGrid(x=True, y=True)
        self._curve = self.plot_widget.plot([], [], pen=pg.mkPen(color=(200, 0, 0), width=2))
        plot_layout.addWidget(self.plot_widget, 1)

        self.spectrum_plot_widget = pg.PlotWidget(self)
        self.spectrum_plot_widget.setBackground("w")
        self.spectrum_plot_widget.setTitle("Spectrum (FFT)")
        self.spectrum_plot_widget.setLabel("left", "Magnitude")
        self.spectrum_plot_widget.setLabel("bottom", "Frequency (THz, approx)")
        self.spectrum_plot_widget.showGrid(x=True, y=True)
        self._spectrum_curve = self.spectrum_plot_widget.plot([], [], pen=pg.mkPen(color=(0, 100, 180), width=2))
        plot_layout.addWidget(self.spectrum_plot_widget, 1)

        self.table_view = MeasureTableView(self)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_view.setAutoScroll(True)
        self.table_model = MeasureTableModel()
        MeasureManager.table = self.table_model
        self.table_view.setModel(self.table_model)
        right_side.addWidget(self.table_view, 2)

        self.setStatusBar(QStatusBar(self))

        self._bind_controller()
        self._update_summary_labels()
        self._set_measurement_buttons_state(running=False)

    def _build_controls(self) -> QWidget:
        panel = QWidget(self)
        layout = QVBoxLayout(panel)

        init_box = QGroupBox("Initialization", panel)
        init_layout = QGridLayout(init_box)
        self.simulate_checkbox = QCheckBox("Simulation mode", init_box)
        self.simulate_checkbox.setChecked(True)
        self.initialize_button = QPushButton("Initialize", init_box)
        self.monitor_start_button = QPushButton("Start monitor", init_box)
        self.monitor_stop_button = QPushButton("Stop monitor", init_box)
        self.current_signal_label = QLabel("Signal: --", init_box)
        init_layout.addWidget(self.simulate_checkbox, 0, 0, 1, 2)
        init_layout.addWidget(self.initialize_button, 1, 0, 1, 2)
        init_layout.addWidget(self.monitor_start_button, 2, 0)
        init_layout.addWidget(self.monitor_stop_button, 2, 1)
        init_layout.addWidget(self.current_signal_label, 3, 0, 1, 2)
        layout.addWidget(init_box)

        settings_box = QGroupBox("Scan settings", panel)
        settings_layout = QGridLayout(settings_box)
        self.wait_spin = QSpinBox(settings_box)
        self.wait_spin.setRange(1, 400_000)
        self.wait_spin.setValue(400)
        self.pos_spin = QDoubleSpinBox(settings_box)
        self.pos_spin.setRange(0.01, 200.0)
        self.pos_spin.setValue(10.0)
        self.neg_spin = QDoubleSpinBox(settings_box)
        self.neg_spin.setRange(0.01, 200.0)
        self.neg_spin.setValue(10.0)
        self.step_spin = QSpinBox(settings_box)
        self.step_spin.setRange(1, 1000)
        self.step_spin.setValue(10)
        self.repeat_spin = QSpinBox(settings_box)
        self.repeat_spin.setRange(1, 100)
        self.repeat_spin.setValue(1)

        self.summary_time = QLabel("Duration: --", settings_box)
        self.summary_points = QLabel("Points: --", settings_box)
        self.summary_resolution = QLabel("Resolution: --", settings_box)

        settings_layout.addWidget(QLabel("Wait time (ms)", settings_box), 0, 0)
        settings_layout.addWidget(self.wait_spin, 0, 1)
        settings_layout.addWidget(QLabel("+ Border (mm)", settings_box), 1, 0)
        settings_layout.addWidget(self.pos_spin, 1, 1)
        settings_layout.addWidget(QLabel("- Border (mm)", settings_box), 2, 0)
        settings_layout.addWidget(self.neg_spin, 2, 1)
        settings_layout.addWidget(QLabel("Step (x2.5 um)", settings_box), 3, 0)
        settings_layout.addWidget(self.step_spin, 3, 1)
        settings_layout.addWidget(QLabel("Repeats", settings_box), 4, 0)
        settings_layout.addWidget(self.repeat_spin, 4, 1)
        settings_layout.addWidget(self.summary_time, 5, 0, 1, 2)
        settings_layout.addWidget(self.summary_points, 6, 0, 1, 2)
        settings_layout.addWidget(self.summary_resolution, 7, 0, 1, 2)
        layout.addWidget(settings_box)

        actions_box = QGroupBox("Measurement", panel)
        actions_layout = QGridLayout(actions_box)
        self.measure_start_button = QPushButton("Start", actions_box)
        self.measure_pause_button = QPushButton("Pause", actions_box)
        self.measure_resume_button = QPushButton("Resume", actions_box)
        self.measure_stop_button = QPushButton("Stop", actions_box)
        self.save_all_button = QPushButton("Save all", actions_box)
        actions_layout.addWidget(self.measure_start_button, 0, 0)
        actions_layout.addWidget(self.measure_pause_button, 0, 1)
        actions_layout.addWidget(self.measure_resume_button, 1, 0)
        actions_layout.addWidget(self.measure_stop_button, 1, 1)
        actions_layout.addWidget(self.save_all_button, 2, 0, 1, 2)
        layout.addWidget(actions_box)

        layout.addStretch(1)

        self.initialize_button.clicked.connect(self._on_initialize_clicked)
        self.monitor_start_button.clicked.connect(self._controller.start_monitoring)
        self.monitor_stop_button.clicked.connect(self._controller.stop_monitoring)

        self.measure_start_button.clicked.connect(self._on_start_measurement)
        self.measure_pause_button.clicked.connect(self._controller.pause_measurement)
        self.measure_resume_button.clicked.connect(self._controller.resume_measurement)
        self.measure_stop_button.clicked.connect(self._controller.stop_measurement)
        self.save_all_button.clicked.connect(self._on_save_all)

        self.wait_spin.valueChanged.connect(self._update_summary_labels)
        self.pos_spin.valueChanged.connect(self._update_summary_labels)
        self.neg_spin.valueChanged.connect(self._update_summary_labels)
        self.step_spin.valueChanged.connect(self._update_summary_labels)
        self.repeat_spin.valueChanged.connect(self._update_summary_labels)

        return panel

    def _bind_controller(self) -> None:
        self._controller.status_changed.connect(self.statusBar().showMessage)
        self._controller.monitoring_signal.connect(self._on_monitoring_signal)
        self._controller.measurement_started.connect(lambda: self._set_measurement_buttons_state(running=True))
        self._controller.measurement_finished.connect(lambda: self._set_measurement_buttons_state(running=False))
        self._controller.measurement_failed.connect(self._on_measurement_failed)
        self._controller.measurement_point.connect(self._on_measurement_point)
        self._controller.initialized.connect(self._on_initialized)

    def _on_initialize_clicked(self) -> None:
        self._controller.initialize_devices(use_simulation=self.simulate_checkbox.isChecked())

    def _on_initialized(self, ok: bool) -> None:
        if not ok:
            message = self._controller.last_error or "Device initialization failed"
            QMessageBox.critical(self, "Initialization", message)

    def _on_start_measurement(self) -> None:
        self._active_scan_settings = self._scan_settings()
        self._current_repeat = 0
        self._measurement_x.clear()
        self._measurement_y.clear()
        self._curve.setData([], [])
        self._spectrum_curve.setData([], [])
        self._controller.start_measurement(self._active_scan_settings)

    def _on_measurement_point(self, point: dict) -> None:
        repeat = int(point.get("repeat", 0))
        index = int(point.get("index", 0))
        if repeat != self._current_repeat and index == 0:
            self._current_repeat = repeat
            self._measurement_x.clear()
            self._measurement_y.clear()
        self._measurement_x.append(int(point["position_steps"]))
        self._measurement_y.append(float(point["signal"]))
        self._curve.setData(self._measurement_x, self._measurement_y)
        self._update_spectrum_curve()

    def _on_measurement_failed(self, error: str) -> None:
        self._set_measurement_buttons_state(running=False)
        QMessageBox.critical(self, "Measurement failed", error)

    def _on_monitoring_signal(self, value: float) -> None:
        self.current_signal_label.setText(f"Signal: {value:.6f}")

    def _set_measurement_buttons_state(self, running: bool) -> None:
        self.measure_start_button.setEnabled(not running)
        self.measure_pause_button.setEnabled(running)
        self.measure_resume_button.setEnabled(running)
        self.measure_stop_button.setEnabled(running)

    def _scan_settings(self) -> ScanSettings:
        return ScanSettings(
            wait_time_ms=self.wait_spin.value(),
            positive_border_mm=self.pos_spin.value(),
            negative_border_mm=self.neg_spin.value(),
            step_units=self.step_spin.value(),
            repeats=self.repeat_spin.value(),
        )

    def _update_summary_labels(self) -> None:
        settings = self._scan_settings()
        seconds = ((settings.wait_time_ms + 100) * 1.5 * settings.point_count * settings.repeats) / 1000
        approx_time = datetime.timedelta(seconds=int(seconds))
        self.summary_time.setText(f"Duration: {approx_time}")
        self.summary_points.setText(f"Points: {settings.point_count} x {settings.repeats}")
        self.summary_resolution.setText(f"Resolution: ~{settings.resolution_thz} THz")

    def _on_save_all(self) -> None:
        path = MeasureManager.save_all()
        if path is None:
            self.statusBar().showMessage("Nothing to save")
        else:
            self.statusBar().showMessage(f"Saved: {path}")

    def closeEvent(self, event) -> None:  # noqa: N802
        self._controller.shutdown()
        event.accept()

    def _update_spectrum_curve(self) -> None:
        """Recompute and redraw FFT spectrum for current interferogram."""
        if len(self._measurement_y) < 8:
            self._spectrum_curve.setData([], [])
            return

        settings = self._active_scan_settings
        if settings is None:
            return

        signal = np.asarray(self._measurement_y, dtype=float)
        signal = signal - signal.mean()
        window = np.hanning(signal.size)
        spectrum = np.fft.rfft(signal * window)
        magnitude = np.abs(spectrum)

        sample_spacing_um = settings.step_units * STAGE_STEP_UM
        freq_per_um = np.fft.rfftfreq(signal.size, d=sample_spacing_um)
        freq_thz = freq_per_um * 299.792458
        self._spectrum_curve.setData(freq_thz.tolist(), magnitude.tolist())
