from __future__ import annotations

import datetime

import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from fts_scanner.domain.models import STAGE_STEP_UM, ScanSettings
from fts_scanner.presentation.controller import MainController
from fts_scanner.presentation.widgets.table_view import MeasureTableView
from fts_scanner.store.measure_store import MeasureManager, MeasureTableModel


class MeasureTab(QWidget):
    """Measurement tab with scan configuration, progress and plots."""

    def __init__(self, controller: MainController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller

        self._measurement_x: list[int] = []
        self._measurement_y: list[float] = []
        self._current_repeat = 0
        self._active_settings: ScanSettings | None = None
        self._total_points = 0

        root = QHBoxLayout(self)

        left_panel = QVBoxLayout()
        root.addLayout(left_panel, 0)

        settings_box = QGroupBox("Scan Settings", self)
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

        left_panel.addWidget(settings_box)

        actions_box = QGroupBox("Measurement", self)
        actions_layout = QGridLayout(actions_box)

        self.start_button = QPushButton("Start", actions_box)
        self.pause_button = QPushButton("Pause", actions_box)
        self.resume_button = QPushButton("Resume", actions_box)
        self.stop_button = QPushButton("Stop", actions_box)
        self.save_all_button = QPushButton("Save all", actions_box)
        self.motor_position_label = QLabel("--", actions_box)
        self.motor_state_label = QLabel("Not initialized", actions_box)

        self.progress_bar = QProgressBar(actions_box)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)

        actions_layout.addWidget(self.start_button, 0, 0)
        actions_layout.addWidget(self.pause_button, 0, 1)
        actions_layout.addWidget(self.resume_button, 1, 0)
        actions_layout.addWidget(self.stop_button, 1, 1)
        actions_layout.addWidget(self.progress_bar, 2, 0, 1, 2)
        actions_layout.addWidget(self.save_all_button, 3, 0, 1, 2)
        actions_layout.addWidget(QLabel("Motor position (steps)", actions_box), 4, 0)
        actions_layout.addWidget(self.motor_position_label, 4, 1)
        actions_layout.addWidget(QLabel("Motor state", actions_box), 5, 0)
        actions_layout.addWidget(self.motor_state_label, 5, 1)

        left_panel.addWidget(actions_box)
        left_panel.addStretch(1)

        right_panel = QVBoxLayout()
        root.addLayout(right_panel, 1)

        plots = QHBoxLayout()
        right_panel.addLayout(plots, 3)

        self.interferogram_plot = pg.PlotWidget(self)
        self.interferogram_plot.setBackground("w")
        self.interferogram_plot.setTitle("Interferogram")
        self.interferogram_plot.setLabel("left", "Signal")
        self.interferogram_plot.setLabel("bottom", "Position (steps)")
        self.interferogram_plot.showGrid(x=True, y=True)
        self._interferogram_curve = self.interferogram_plot.plot([], [], pen=pg.mkPen(color=(200, 0, 0), width=2))
        plots.addWidget(self.interferogram_plot, 1)

        self.spectrum_plot = pg.PlotWidget(self)
        self.spectrum_plot.setBackground("w")
        self.spectrum_plot.setTitle("Spectrum (FFT)")
        self.spectrum_plot.setLabel("left", "Amplitude (sqrt|FFT|)")
        self.spectrum_plot.setLabel("bottom", "Frequency (THz, approx)")
        self.spectrum_plot.showGrid(x=True, y=True)
        self._spectrum_curve = self.spectrum_plot.plot([], [], pen=pg.mkPen(color=(0, 100, 180), width=2))
        plots.addWidget(self.spectrum_plot, 1)

        self.table_view = MeasureTableView(self)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_view.setAutoScroll(True)
        self.table_model = MeasureTableModel()
        MeasureManager.table = self.table_model
        self.table_view.setModel(self.table_model)
        right_panel.addWidget(self.table_view, 2)

        self.start_button.clicked.connect(self._on_start)
        self.pause_button.clicked.connect(self._controller.pause_measurement)
        self.resume_button.clicked.connect(self._controller.resume_measurement)
        self.stop_button.clicked.connect(self._controller.stop_measurement)
        self.save_all_button.clicked.connect(self._on_save_all)

        self.wait_spin.valueChanged.connect(self._update_summary_labels)
        self.pos_spin.valueChanged.connect(self._update_summary_labels)
        self.neg_spin.valueChanged.connect(self._update_summary_labels)
        self.step_spin.valueChanged.connect(self._update_summary_labels)
        self.repeat_spin.valueChanged.connect(self._update_summary_labels)

        self._controller.measurement_started.connect(self._on_measurement_started)
        self._controller.measurement_point.connect(self._on_measurement_point)
        self._controller.measurement_finished.connect(self._on_measurement_finished)
        self._controller.measurement_failed.connect(self._on_measurement_failed)
        self._controller.motor_position_signal.connect(self._on_motor_position)
        self._controller.motor_state_signal.connect(self._on_motor_state)

        self._update_summary_labels()
        self._set_measure_buttons(running=False)

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

    def _on_start(self) -> None:
        self._active_settings = self._scan_settings()
        self._total_points = self._active_settings.point_count * self._active_settings.repeats
        self.progress_bar.setRange(0, max(1, self._total_points))
        self.progress_bar.setValue(0)

        self._current_repeat = 0
        self._measurement_x.clear()
        self._measurement_y.clear()
        self._interferogram_curve.setData([], [])
        self._spectrum_curve.setData([], [])

        self._controller.start_measurement(self._active_settings)

    def _on_measurement_started(self) -> None:
        self._set_measure_buttons(running=True)

    def _on_measurement_point(self, point: dict) -> None:
        repeat = int(point.get("repeat", 0))
        index = int(point.get("index", 0))

        if repeat != self._current_repeat and index == 0:
            self._current_repeat = repeat
            self._measurement_x.clear()
            self._measurement_y.clear()

        self._measurement_x.append(int(point["position_steps"]))
        self._measurement_y.append(float(point["signal"]))
        self._interferogram_curve.setData(self._measurement_x, self._measurement_y)
        self._update_spectrum()

        if self._active_settings is not None:
            done = repeat * self._active_settings.point_count + index + 1
            self.progress_bar.setValue(min(done, self.progress_bar.maximum()))

    def _on_measurement_finished(self) -> None:
        self._set_measure_buttons(running=False)
        self.progress_bar.setValue(self.progress_bar.maximum())

    def _on_measurement_failed(self, error: str) -> None:
        self._set_measure_buttons(running=False)
        QMessageBox.critical(self, "Measurement failed", error)

    def _set_measure_buttons(self, running: bool) -> None:
        self.start_button.setEnabled(not running)
        self.pause_button.setEnabled(running)
        self.resume_button.setEnabled(running)
        self.stop_button.setEnabled(running)

    def _on_motor_position(self, position: int) -> None:
        self.motor_position_label.setText(str(position))

    def _on_motor_state(self, state: str) -> None:
        self.motor_state_label.setText(state)

    def _update_spectrum(self) -> None:
        if len(self._measurement_y) < 8 or self._active_settings is None:
            self._spectrum_curve.setData([], [])
            return

        signal = np.asarray(self._measurement_y, dtype=float)
        signal = signal - signal.mean()
        window = np.hanning(signal.size)
        spectrum = np.fft.rfft(signal * window)
        magnitude_raw = np.abs(spectrum)
        magnitude = np.sqrt(np.clip(magnitude_raw, 0.0, None))

        # Michelson geometry: optical path difference is 2x mirror travel.
        sample_spacing_um = self._active_settings.step_units * STAGE_STEP_UM * 2.0
        freq_per_um = np.fft.rfftfreq(signal.size, d=sample_spacing_um)
        freq_thz = freq_per_um * 299.792458
        self._spectrum_curve.setData(freq_thz.tolist(), magnitude.tolist())

    def _on_save_all(self) -> None:
        MeasureManager.save_all()
