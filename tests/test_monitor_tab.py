from __future__ import annotations

import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QHideEvent
from PySide6.QtWidgets import QApplication

_APP = QApplication.instance() or QApplication([])

from fts_scanner.presentation.widgets.monitor_tab import MonitorTab


class FakeController(QObject):
    monitoring_signal = Signal(float)
    motor_position_signal = Signal(int)
    motor_motion_params_signal = Signal(int, int)
    motor_state_signal = Signal(str)
    monitoring_state_changed = Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.config = SimpleNamespace(motor_speed=1000, motor_acceleration=500)
        self.stop_calls = 0

    def start_monitoring(self) -> None:
        return None

    def stop_monitoring(self) -> None:
        return None

    def start_motor_jog(self, direction: int) -> None:
        return None

    def stop_motor_motion(self) -> None:
        self.stop_calls += 1

    def set_motor_zero(self) -> None:
        return None

    def move_motor_to(self, target_steps: int, wait_ms: int = 100) -> None:
        return None

    def set_motor_motion_params(self, speed: int, acceleration: int) -> None:
        return None

    def read_motor_motion_params(self) -> None:
        return None


class TestMonitorTab(unittest.TestCase):
    def test_hide_event_does_not_stop_regular_motion(self) -> None:
        controller = FakeController()
        tab = MonitorTab(controller)

        tab.hideEvent(QHideEvent())

        self.assertEqual(controller.stop_calls, 0)

    def test_hide_event_stops_active_jog(self) -> None:
        controller = FakeController()
        tab = MonitorTab(controller)
        tab._jog_direction = 1

        tab.hideEvent(QHideEvent())

        self.assertEqual(controller.stop_calls, 1)


if __name__ == "__main__":
    unittest.main()
