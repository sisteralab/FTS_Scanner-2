from __future__ import annotations

import os
import time
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication

from fts_scanner.devices.interfaces import MotorMotionStatus
from fts_scanner.presentation.device_workers import MotorIoWorker
from fts_scanner.presentation.motor_command_client import MotorCommandClient

_APP = QApplication.instance() or QApplication([])


class SimpleMotor:
    def __init__(self) -> None:
        self.position = 0
        self.speed = 1000
        self.acceleration = 500

    def initialize(self) -> None:
        return None

    def move_to(self, steps: int) -> None:
        self.position = int(steps)

    def move_by(self, delta_steps: int) -> None:
        self.position += int(delta_steps)

    def wait_for_stop(self, timeout_ms: int) -> None:
        return None

    def get_position(self) -> int:
        return int(self.position)

    def set_zero(self) -> None:
        self.position = 0

    def stop(self) -> None:
        return None

    def start_jog(self, direction: int) -> None:
        return None

    def get_motion_params(self) -> tuple[int, int]:
        return int(self.speed), int(self.acceleration)

    def set_motion_params(self, speed: int, acceleration: int) -> None:
        self.speed = int(speed)
        self.acceleration = int(acceleration)

    def get_motion_status(self) -> MotorMotionStatus:
        return MotorMotionStatus(
            is_moving=False,
            has_error=False,
            command="idle",
            command_code=0,
        )

    def shutdown(self) -> None:
        return None


class TestMotorCommandClient(unittest.TestCase):
    def setUp(self) -> None:
        self.worker = MotorIoWorker(SimpleMotor())
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.start()
        self.client = MotorCommandClient(self.worker)

    def tearDown(self) -> None:
        self.thread.quit()
        self.thread.wait(1500)

    def test_main_thread_commands_complete_without_gui_event_pump(self) -> None:
        start = time.monotonic()

        self.client.move_to(42)
        position = self.client.get_position()
        speed, acceleration = self.client.set_motion_params(1200, 600)

        elapsed = time.monotonic() - start
        self.assertLess(elapsed, 1.0)
        self.assertEqual(position, 42)
        self.assertEqual((speed, acceleration), (1200, 600))


if __name__ == "__main__":
    unittest.main()
