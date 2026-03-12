from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from fts_scanner.presentation.widgets.monitor_tab import MonitorTab


class _FakeController(QObject):
    monitoring_signal = Signal(float)
    motor_position_signal = Signal(int)
    motor_state_signal = Signal(str)
    motor_motion_params_signal = Signal(int, int)
    monitoring_state_changed = Signal(bool)
    measurement_started = Signal()
    measurement_finished = Signal()
    measurement_failed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._allow_jog = True
        self.stop_calls = 0
        self.move_to_calls: list[tuple[int, int]] = []
        self.set_motion_calls: list[tuple[int, int]] = []
        self.start_monitor_calls = 0
        self.stop_monitor_calls = 0
        self.set_zero_calls = 0
        self.read_motion_calls = 0
        self.config = type("Cfg", (), {"motor_speed": 1000, "motor_acceleration": 1000})()

    def start_monitoring(self) -> None:
        self.start_monitor_calls += 1

    def stop_monitoring(self) -> None:
        self.stop_monitor_calls += 1

    def start_motor_jog(self, direction: int) -> bool:
        return self._allow_jog and direction != 0

    def stop_motor_motion(self) -> None:
        self.stop_calls += 1

    def set_motor_zero(self) -> None:
        self.set_zero_calls += 1

    def move_motor_to(self, target_steps: int, wait_ms: int = 100) -> None:
        self.move_to_calls.append((int(target_steps), int(wait_ms)))

    def set_motor_motion_params(self, speed: int, acceleration: int) -> None:
        self.set_motion_calls.append((int(speed), int(acceleration)))

    def read_motor_motion_params(self) -> None:
        self.read_motion_calls += 1


class TestMonitorTabInteractions(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_rejected_jog_does_not_trigger_stop(self) -> None:
        controller = _FakeController()
        controller._allow_jog = False
        tab = MonitorTab(controller)

        tab._start_jog(1)
        tab._stop_jog()

        self.assertEqual(controller.stop_calls, 0)

    def test_accepted_jog_triggers_stop_on_release(self) -> None:
        controller = _FakeController()
        controller._allow_jog = True
        tab = MonitorTab(controller)

        tab._start_jog(-1)
        tab._stop_jog()

        self.assertEqual(controller.stop_calls, 1)


if __name__ == "__main__":
    unittest.main()
