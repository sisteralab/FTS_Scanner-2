from __future__ import annotations

import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from fts_scanner.config import AppConfig
from fts_scanner.presentation.controller import MainController

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
        self.controller._motor_command_client = FakeMotorCommandClient()

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


if __name__ == "__main__":
    unittest.main()
