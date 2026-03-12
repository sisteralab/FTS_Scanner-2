from __future__ import annotations

import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from fts_scanner.config import AppConfig
from fts_scanner.presentation.controller import MainController


class _RunningThreadStub:
    def isRunning(self) -> bool:  # noqa: N802
        return True

    def quit(self) -> None:
        return None

    def wait(self, msecs: int = 0) -> bool:
        return True


class TestControllerInteractions(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.controller = MainController(config=AppConfig(), project_root=Path("."))

    def tearDown(self) -> None:
        self.controller._thread = None
        self.controller._motor_worker = None
        self.controller._lockin_worker = None
        self.controller.shutdown()

    def test_start_monitoring_blocked_while_measurement_running(self) -> None:
        self.controller._thread = _RunningThreadStub()
        self.controller._lock_in_ready = True
        self.controller._lockin_worker = object()

        statuses: list[str] = []
        self.controller.status_changed.connect(statuses.append)

        self.controller.start_monitoring()

        self.assertFalse(self.controller._monitor_timer.isActive())
        self.assertIn("Monitoring is unavailable while measurement is running", statuses)

    def test_motion_commands_blocked_while_measurement_running(self) -> None:
        self.controller._thread = _RunningThreadStub()
        self.controller._motor_ready = True
        self.controller._motor_worker = object()

        move_to_calls: list[tuple[int, int]] = []
        jog_calls: list[int] = []
        statuses: list[str] = []

        self.controller.motor_move_to_requested.connect(
            lambda target, wait: move_to_calls.append((int(target), int(wait)))
        )
        self.controller.motor_start_jog_requested.connect(lambda direction: jog_calls.append(int(direction)))
        self.controller.status_changed.connect(statuses.append)

        self.controller.move_motor_to(12345, wait_ms=100)
        accepted = self.controller.start_motor_jog(1)

        self.assertFalse(accepted)
        self.assertEqual(move_to_calls, [])
        self.assertEqual(jog_calls, [])
        self.assertIn("Motor control is disabled while measurement is running", statuses)

    def test_start_motor_jog_emits_when_idle(self) -> None:
        self.controller._motor_ready = True
        self.controller._motor_worker = object()

        jog_calls: list[int] = []
        self.controller.motor_start_jog_requested.connect(lambda direction: jog_calls.append(int(direction)))

        accepted = self.controller.start_motor_jog(-1)

        self.assertTrue(accepted)
        self.assertEqual(jog_calls, [-1])


if __name__ == "__main__":
    unittest.main()
