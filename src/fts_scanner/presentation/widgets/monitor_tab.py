from __future__ import annotations

import time

import pyqtgraph as pg
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from fts_scanner.presentation.controller import MainController


class MonitorTab(QWidget):
    """Monitor tab for motor control and live lock-in stream."""

    def __init__(self, controller: MainController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller

        self._signal_samples: list[tuple[float, float]] = []

        self._jog_direction = 0
        self._jog_timer = QTimer(self)
        self._jog_timer.setInterval(120)
        self._jog_timer.timeout.connect(self._jog_tick)

        layout = QVBoxLayout(self)

        actions = QHBoxLayout()
        self.start_monitor_button = QPushButton("Start Monitoring", self)
        self.stop_monitor_button = QPushButton("Stop Monitoring", self)
        actions.addWidget(self.start_monitor_button)
        actions.addWidget(self.stop_monitor_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        motor_box = QGroupBox("Motor", self)
        motor_layout = QGridLayout(motor_box)

        self.motor_position_label = QLabel("0", motor_box)
        self.jog_step_spin = QSpinBox(motor_box)
        self.jog_step_spin.setRange(1, 5000)
        self.jog_step_spin.setValue(200)

        self.jog_left_button = QPushButton("Jog -", motor_box)
        self.jog_right_button = QPushButton("Jog +", motor_box)
        self.set_zero_button = QPushButton("Set Zero", motor_box)

        self.target_position_spin = QSpinBox(motor_box)
        self.target_position_spin.setRange(-2_000_000, 2_000_000)
        self.move_to_button = QPushButton("Move To", motor_box)

        motor_layout.addWidget(QLabel("Current position (steps)"), 0, 0)
        motor_layout.addWidget(self.motor_position_label, 0, 1)
        motor_layout.addWidget(QLabel("Jog step (steps)"), 1, 0)
        motor_layout.addWidget(self.jog_step_spin, 1, 1)
        motor_layout.addWidget(self.jog_left_button, 2, 0)
        motor_layout.addWidget(self.jog_right_button, 2, 1)
        motor_layout.addWidget(self.set_zero_button, 3, 0, 1, 2)
        motor_layout.addWidget(QLabel("Target position"), 4, 0)
        motor_layout.addWidget(self.target_position_spin, 4, 1)
        motor_layout.addWidget(self.move_to_button, 5, 0, 1, 2)
        layout.addWidget(motor_box)

        lockin_box = QGroupBox("Lock-In Stream", self)
        lockin_layout = QVBoxLayout(lockin_box)

        top_info = QFormLayout()
        self.current_signal_label = QLabel("--", lockin_box)
        self.window_seconds_spin = QSpinBox(lockin_box)
        self.window_seconds_spin.setRange(1, 600)
        self.window_seconds_spin.setValue(30)
        top_info.addRow("Current signal", self.current_signal_label)
        top_info.addRow("Visible window (s)", self.window_seconds_spin)

        self.stream_plot = pg.PlotWidget(lockin_box)
        self.stream_plot.setBackground("w")
        self.stream_plot.setLabel("left", "Signal")
        self.stream_plot.setLabel("bottom", "Time (s)")
        self.stream_plot.showGrid(x=True, y=True)
        self._stream_curve = self.stream_plot.plot([], [], pen=pg.mkPen(color=(0, 120, 160), width=2))

        lockin_layout.addLayout(top_info)
        lockin_layout.addWidget(self.stream_plot)
        layout.addWidget(lockin_box, 1)

        self.start_monitor_button.clicked.connect(self._start_monitoring)
        self.stop_monitor_button.clicked.connect(self._controller.stop_monitoring)

        self.jog_left_button.pressed.connect(lambda: self._start_jog(-1))
        self.jog_right_button.pressed.connect(lambda: self._start_jog(1))
        self.jog_left_button.released.connect(self._stop_jog)
        self.jog_right_button.released.connect(self._stop_jog)

        self.set_zero_button.clicked.connect(self._controller.set_motor_zero)
        self.move_to_button.clicked.connect(self._move_to_target)

        self._controller.monitoring_signal.connect(self._on_signal)
        self._controller.motor_position_signal.connect(self._on_motor_position)
        self._controller.monitoring_state_changed.connect(self._set_monitor_buttons_state)
        self._set_monitor_buttons_state(False)

    def _start_monitoring(self) -> None:
        self._signal_samples.clear()
        self._stream_curve.setData([], [])
        self._controller.start_monitoring()

    def _start_jog(self, direction: int) -> None:
        self._jog_direction = direction
        self._jog_tick()
        self._jog_timer.start()

    def _stop_jog(self) -> None:
        self._jog_timer.stop()
        self._jog_direction = 0
        self._controller.stop_motor_motion()

    def _jog_tick(self) -> None:
        if self._jog_direction == 0:
            return
        step = self.jog_step_spin.value() * self._jog_direction
        self._controller.move_motor_by(step, wait_ms=80)

    def _move_to_target(self) -> None:
        self._controller.move_motor_to(self.target_position_spin.value(), wait_ms=100)

    def _on_motor_position(self, position: int) -> None:
        self.motor_position_label.setText(str(position))

    def _on_signal(self, value: float) -> None:
        self.current_signal_label.setText(f"{value:.6f}")
        timestamp = time.time()
        self._signal_samples.append((timestamp, value))
        window = float(self.window_seconds_spin.value())
        latest_ts = self._signal_samples[-1][0]
        while self._signal_samples and (latest_ts - self._signal_samples[0][0]) >= window:
            self._signal_samples.pop(0)
        if not self._signal_samples:
            self._stream_curve.setData([], [])
            return

        base_ts = self._signal_samples[0][0]
        x = [t - base_ts for t, _ in self._signal_samples]
        y = [v for _, v in self._signal_samples]
        self._stream_curve.setData(x, y)

    def _set_monitor_buttons_state(self, is_running: bool) -> None:
        self.start_monitor_button.setEnabled(not is_running)
        self.stop_monitor_button.setEnabled(is_running)
