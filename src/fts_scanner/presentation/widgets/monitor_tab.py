from __future__ import annotations

import time

import pyqtgraph as pg
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QStyle,
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
        self._motor_ready = False
        self._lockin_ready = False
        self._measurement_running = False

        layout = QVBoxLayout(self)

        actions = QHBoxLayout()
        self.start_monitor_button = QPushButton("Start Monitoring", self)
        self.stop_monitor_button = QPushButton("Stop Monitoring", self)
        self.start_monitor_button.setIcon(self._std_icon("SP_MediaPlay"))
        self.stop_monitor_button.setIcon(self._std_icon("SP_MediaStop"))
        self.start_monitor_button.setStyleSheet("background: #2d8548;")
        self.stop_monitor_button.setStyleSheet("background: #b22323;")
        actions.addWidget(self.start_monitor_button)
        actions.addWidget(self.stop_monitor_button)
        self.save_monitor_stream_checkbox = QCheckBox("Save Lock-In stream", self)
        self.save_monitor_stream_checkbox.setToolTip(
            "Store monitor samples as time/voltage arrays in the measurements table"
        )
        actions.addWidget(self.save_monitor_stream_checkbox)
        actions.addStretch(1)
        layout.addLayout(actions)

        motor_box = QGroupBox("Motor", self)
        motor_box.setMaximumWidth(620)
        motor_layout = QVBoxLayout(motor_box)

        self.motor_position_label = QLabel("0", motor_box)
        self.motor_state_label = QLabel("Idle", motor_box)
        self.motor_state_label.setWordWrap(True)
        self.motor_state_label.setStyleSheet(
            "background: #eef6ff; border: 1px solid #c9ddf7; border-radius: 7px; "
            "padding: 4px 8px; font-weight: 600; color: #244b7c;"
        )

        self.jog_left_button = QPushButton("Hold Left", motor_box)
        self.jog_right_button = QPushButton("Hold Right", motor_box)
        self.set_zero_button = QPushButton("Set Zero", motor_box)
        self.emergency_stop_button = QPushButton("Emergency Stop", motor_box)
        self.emergency_stop_button.setStyleSheet("background: #b22323; color: white; font-weight: 600;")
        self.jog_left_button.setIcon(self._std_icon("SP_ArrowLeft"))
        self.jog_right_button.setIcon(self._std_icon("SP_ArrowRight"))
        self.set_zero_button.setIcon(self._std_icon("SP_DialogResetButton"))
        self.emergency_stop_button.setIcon(self._std_icon("SP_BrowserStop"))

        self.speed_spin = QSpinBox(motor_box)
        self.speed_spin.setRange(1, 5_000_000)
        self.speed_spin.setValue(self._controller.config.motor_speed)
        self.speed_spin.setFixedWidth(180)

        self.accel_spin = QSpinBox(motor_box)
        self.accel_spin.setRange(1, 5_000_000)
        self.accel_spin.setValue(self._controller.config.motor_acceleration)
        self.accel_spin.setFixedWidth(180)

        self.apply_motion_button = QPushButton("Apply Speed/Accel", motor_box)
        self.reload_motion_button = QPushButton("Read From Motor", motor_box)
        self.apply_motion_button.setIcon(self._std_icon("SP_DialogApplyButton"))
        self.reload_motion_button.setIcon(self._std_icon("SP_BrowserReload"))
        self.apply_motion_button.setFixedWidth(170)
        self.reload_motion_button.setFixedWidth(170)

        self.target_position_spin = QSpinBox(motor_box)
        self.target_position_spin.setRange(-2_000_000, 2_000_000)
        self.target_position_spin.setFixedWidth(180)
        self.move_to_button = QPushButton("Move To", motor_box)
        self.move_to_button.setIcon(self._std_icon("SP_ArrowRight"))
        self.move_to_button.setFixedWidth(170)
        self.jog_left_button.setFixedWidth(170)
        self.jog_right_button.setFixedWidth(170)
        self.set_zero_button.setFixedWidth(170)
        self.emergency_stop_button.setFixedWidth(170)

        info_form = QFormLayout()
        info_form.addRow("Current position (steps)", self.motor_position_label)
        info_form.addRow("Motor state", self.motor_state_label)
        info_form.addRow("Speed", self.speed_spin)
        info_form.addRow("Acceleration", self.accel_spin)
        info_form.addRow("Target position", self.target_position_spin)
        motor_layout.addLayout(info_form)

        motion_buttons = QHBoxLayout()
        motion_buttons.addWidget(self.apply_motion_button)
        motion_buttons.addWidget(self.reload_motion_button)
        motion_buttons.addStretch(1)
        motor_layout.addLayout(motion_buttons)

        move_buttons = QHBoxLayout()
        move_buttons.addWidget(self.move_to_button)
        move_buttons.addStretch(1)
        motor_layout.addLayout(move_buttons)

        jog_buttons = QHBoxLayout()
        jog_buttons.addWidget(self.jog_left_button)
        jog_buttons.addWidget(self.jog_right_button)
        jog_buttons.addStretch(1)
        motor_layout.addLayout(jog_buttons)

        safety_buttons = QHBoxLayout()
        safety_buttons.addWidget(self.set_zero_button)
        safety_buttons.addWidget(self.emergency_stop_button)
        safety_buttons.addStretch(1)
        motor_layout.addLayout(safety_buttons)
        motor_layout.addStretch(1)

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
        self.emergency_stop_button.clicked.connect(self._emergency_stop)
        self.move_to_button.clicked.connect(self._move_to_target)
        self.apply_motion_button.clicked.connect(self._apply_motion_params)
        self.reload_motion_button.clicked.connect(self._controller.read_motor_motion_params)

        self._controller.monitoring_signal.connect(self._on_signal)
        self._controller.motor_position_signal.connect(self._on_motor_position)
        self._controller.motor_motion_params_signal.connect(self._on_motion_params)
        self._controller.motor_state_signal.connect(self._on_motor_state)
        self._controller.monitoring_state_changed.connect(self._set_monitor_buttons_state)
        self._controller.setup_status.connect(self._on_setup_status)
        self._controller.measurement_started.connect(self._on_measurement_started)
        self._controller.measurement_finished.connect(self._on_measurement_finished)
        self._controller.measurement_failed.connect(self._on_measurement_failed)
        self._set_monitor_buttons_state(False)
        self._refresh_motor_controls()

    def _start_monitoring(self) -> None:
        self._signal_samples.clear()
        self._stream_curve.setData([], [])
        self._controller.start_monitoring(self.save_monitor_stream_checkbox.isChecked())

    def _start_jog(self, direction: int) -> None:
        self._jog_direction = direction
        self._controller.start_motor_jog(direction)

    def _stop_jog(self) -> None:
        if self._jog_direction == 0:
            return
        self._jog_direction = 0
        self._controller.stop_motor_motion()

    def _emergency_stop(self) -> None:
        self._jog_direction = 0
        self._controller.stop_motor_motion()

    def _move_to_target(self) -> None:
        self._jog_direction = 0
        self._controller.move_motor_to(self.target_position_spin.value(), wait_ms=100)

    def _apply_motion_params(self) -> None:
        self._controller.set_motor_motion_params(
            speed=self.speed_spin.value(),
            acceleration=self.accel_spin.value(),
        )

    def _on_motor_position(self, position: int) -> None:
        self.motor_position_label.setText(str(position))

    def _on_motion_params(self, speed: int, acceleration: int) -> None:
        self.speed_spin.setValue(int(speed))
        self.accel_spin.setValue(int(acceleration))

    def _on_motor_state(self, state: str) -> None:
        self.motor_state_label.setText(state)
        self._set_state_chip_style(state)

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
        monitoring_available = self._motor_ready or self._lockin_ready
        self.start_monitor_button.setEnabled(monitoring_available and not is_running)
        self.stop_monitor_button.setEnabled(is_running)
        self.save_monitor_stream_checkbox.setEnabled(self._lockin_ready and not is_running)

    def _on_setup_status(self, motor_ok: bool, lockin_ok: bool, _message: str) -> None:
        self._motor_ready = bool(motor_ok)
        self._lockin_ready = bool(lockin_ok)
        self._refresh_motor_controls()
        self._set_monitor_buttons_state(False)

    def _on_measurement_started(self) -> None:
        self._measurement_running = True
        self._refresh_motor_controls()

    def _on_measurement_finished(self) -> None:
        self._measurement_running = False
        self._refresh_motor_controls()

    def _on_measurement_failed(self, _error: str) -> None:
        self._measurement_running = False
        self._refresh_motor_controls()

    def _refresh_motor_controls(self) -> None:
        manual_control_enabled = self._motor_ready and not self._measurement_running
        for widget in (
            self.jog_left_button,
            self.jog_right_button,
            self.set_zero_button,
            self.speed_spin,
            self.accel_spin,
            self.apply_motion_button,
            self.reload_motion_button,
            self.target_position_spin,
            self.move_to_button,
        ):
            widget.setEnabled(manual_control_enabled)
        self.emergency_stop_button.setEnabled(self._motor_ready)

    def hideEvent(self, event) -> None:  # noqa: N802, ANN001
        # Tab switching should not cancel normal moves or measurement motion.
        # Only stop an actively held jog because the release event may never arrive.
        self._stop_jog()
        super().hideEvent(event)

    def _std_icon(self, name: str) -> QIcon:
        enum_item = getattr(QStyle.StandardPixmap, name, None)
        if enum_item is None:
            return QIcon()
        return self.style().standardIcon(enum_item)

    def _set_state_chip_style(self, state_text: str) -> None:
        text = state_text.lower()
        if "error" in text or "failed" in text:
            bg, border, fg = "#ffe8e8", "#f2b2b2", "#8c1d1d"
        elif "moving" in text or "jog" in text:
            bg, border, fg = "#fff3df", "#f0cc8f", "#7a4a00"
        else:
            bg, border, fg = "#e8f7eb", "#b6e0bd", "#1e6a2f"
        self.motor_state_label.setStyleSheet(
            f"background: {bg}; border: 1px solid {border}; border-radius: 7px; "
            f"padding: 4px 8px; font-weight: 600; color: {fg};"
        )
