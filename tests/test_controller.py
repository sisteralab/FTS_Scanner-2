from __future__ import annotations

import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from fts_scanner.config import AppConfig
from fts_scanner.presentation.controller import MainController
from fts_scanner.store.measure_store import MeasureManager, MeasureType

_APP = QApplication.instance() or QApplication([])


class FakeMotorCommandClient:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def move_to(self, steps: int) -> None:
        self.calls.append(("move_to", int(steps)))

    def move_by(self, delta_steps: int) -> None:
        self.calls.append(("move_by", int(delta_steps)))

    def set_zero(self) -> None:
        self.calls.append(("set_zero",))

    def stop(self) -> None:
        self.calls.append(("stop",))

    def start_jog(self, direction: int) -> None:
        self.calls.append(("start_jog", int(direction)))

    def get_motion_params(self) -> tuple[int, int]:
        self.calls.append(("get_motion_params",))
        return 1400, 650

    def set_motion_params(self, speed: int, acceleration: int) -> tuple[int, int]:
        self.calls.append(("set_motion_params", int(speed), int(acceleration)))
        return int(speed), int(acceleration)


class TestMainControllerMotorCommands(unittest.TestCase):
    def setUp(self) -> None:
        config = AppConfig(
            use_simulation=True,
            settings_organization="ASC Test",
            settings_application="FTS Scanner Controller Test",
            settings_file=Path.cwd() / "tests" / "controller-settings.ini",
        )
        self.controller = MainController(config, Path.cwd())
        self.controller._motor_ready = True
        self.controller._lock_in_ready = True
        self.controller._motor_command_client = FakeMotorCommandClient()
        MeasureManager._instances.clear()
        MeasureManager.latest_id = 0
        MeasureManager.table = None

    def tearDown(self) -> None:
        self.controller.stop_monitoring()
        MeasureManager._instances.clear()
        MeasureManager.latest_id = 0
        MeasureManager.table = None

    def test_move_motor_to_uses_motor_command_client(self) -> None:
        self.controller.move_motor_to(125)

        self.assertEqual(
            self.controller._motor_command_client.calls,
            [("move_to", 125)],
        )

    def test_read_motor_motion_params_updates_config_from_motor_client(self) -> None:
        self.controller.read_motor_motion_params()

        self.assertEqual(
            self.controller._motor_command_client.calls,
            [("get_motion_params",)],
        )
        self.assertEqual(self.controller.config.motor_speed, 1400)
        self.assertEqual(self.controller.config.motor_acceleration, 650)

    def test_lockin_monitor_recording_uses_time_and_voltage_arrays(self) -> None:
        self.controller.start_monitoring(record_stream=True, poll_interval_ms=750)

        self.controller._on_lockin_signal(1.25)
        self.controller._on_lockin_signal(1.50)
        self.controller.stop_monitoring()

        measure = MeasureManager.all().last()
        self.assertIsNotNone(measure)
        self.assertEqual(measure.measure_type, MeasureType.LOCKIN_MONITOR)
        self.assertEqual(measure.points_count, 2)
        self.assertEqual(measure.data["voltage"], [1.25, 1.50])
        self.assertEqual(len(measure.data["time"]), 2)
        self.assertGreaterEqual(measure.data["time"][0], 0.0)
        self.assertGreaterEqual(measure.data["time"][1], measure.data["time"][0])
        self.assertEqual(measure.data["meta"]["status"], "stopped")
        self.assertEqual(measure.data["meta"]["samples_count"], 2)
        self.assertEqual(measure.data["settings"]["sample_interval_ms"], 750)

    def test_monitoring_poll_interval_is_clamped(self) -> None:
        self.controller.start_monitoring(poll_interval_ms=20_000)

        self.assertEqual(self.controller._monitor_timer.interval(), 10_000)


if __name__ == "__main__":
    unittest.main()
