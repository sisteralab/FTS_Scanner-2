from __future__ import annotations

import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

_APP = QApplication.instance() or QApplication([])

from fts_scanner.presentation.widgets.measure_tab import MeasureTab


class FakeController(QObject):
    measurement_started = Signal()
    measurement_point = Signal(dict)
    measurement_finished = Signal()
    measurement_failed = Signal(str)
    motor_state_signal = Signal(str)
    setup_status = Signal(bool, bool, str)

    def __init__(self) -> None:
        super().__init__()
        self.config = SimpleNamespace()

    def start_measurement(self, settings) -> None:  # noqa: ANN001
        return None

    def pause_measurement(self) -> None:
        return None

    def resume_measurement(self) -> None:
        return None

    def stop_measurement(self) -> None:
        return None


class TestMeasureTab(unittest.TestCase):
    def test_start_disabled_until_devices_initialized(self) -> None:
        controller = FakeController()
        tab = MeasureTab(controller)

        self.assertFalse(tab.start_button.isEnabled())

        controller.setup_status.emit(True, True, "ok")

        self.assertTrue(tab.start_button.isEnabled())

    def test_live_motor_detail_updates_during_measurement(self) -> None:
        controller = FakeController()
        tab = MeasureTab(controller)
        controller.setup_status.emit(True, True, "ok")

        controller.measurement_started.emit()
        controller.motor_state_signal.emit("Moving: cmd=move, position=150, target=300")

        self.assertIn("Moving: cmd=move", tab.motor_detail_label.text())
        self.assertEqual(tab.motor_state_badge.toolTip(), "Measurement: starting motor scan")


if __name__ == "__main__":
    unittest.main()
