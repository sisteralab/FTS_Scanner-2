from __future__ import annotations

import unittest
from unittest.mock import patch

from fts_scanner.devices.simulated import SimulatedLockInDevice, SimulatedMotorDevice
from fts_scanner.domain.models import ScanSettings
from fts_scanner.use_cases.initialize import InitializeHardwareUseCase
from fts_scanner.use_cases.measure_spectrogram import MeasureSpectrogramUseCase
from fts_scanner.use_cases.monitor import ReadSignalUseCase


class _FakeMotor:
    def __init__(self) -> None:
        self.position = 0
        self.calls: list[tuple] = []

    def initialize(self) -> None:
        self.calls.append(("initialize",))

    def move_to(self, steps: int) -> None:
        self.calls.append(("move_to", int(steps)))
        self.position = int(steps)

    def move_by(self, delta_steps: int) -> None:
        self.calls.append(("move_by", int(delta_steps)))
        self.position += int(delta_steps)

    def wait_for_stop(self, timeout_ms: int) -> None:
        self.calls.append(("wait_for_stop", int(timeout_ms)))

    def get_position(self) -> int:
        self.calls.append(("get_position",))
        return self.position

    def set_zero(self) -> None:
        self.calls.append(("set_zero",))
        self.position = 0

    def stop(self) -> None:
        self.calls.append(("stop",))

    def start_jog(self, direction: int) -> None:
        self.calls.append(("start_jog", int(direction)))

    def get_motion_params(self) -> tuple[int, int]:
        return 1000, 1000

    def set_motion_params(self, speed: int, acceleration: int) -> None:
        self.calls.append(("set_motion_params", int(speed), int(acceleration)))

    def shutdown(self) -> None:
        self.calls.append(("shutdown",))


class _FakeLockIn:
    def initialize(self) -> None:
        return None

    def identify(self) -> str:
        return "FAKE,SR830,0,1.0"

    def read_signal(self) -> float:
        return 1.0

    def shutdown(self) -> None:
        return None


class TestUseCases(unittest.TestCase):
    def setUp(self) -> None:
        self.motor = SimulatedMotorDevice()
        self.lock_in = SimulatedLockInDevice(noise_scale=0.0)

    def test_initialize_hardware(self) -> None:
        report = InitializeHardwareUseCase(self.motor, self.lock_in).execute()
        self.assertIn("SIMULATED", report.lock_in_idn)
        self.assertEqual(report.motor_position_steps, 0)

    def test_read_signal(self) -> None:
        self.lock_in.initialize()
        value = ReadSignalUseCase(self.lock_in).execute()
        self.assertIsInstance(value, float)

    def test_measure_spectrogram_collects_expected_points(self) -> None:
        settings = ScanSettings(
            wait_time_ms=1,
            positive_border_mm=0.02,
            negative_border_mm=0.02,
            step_units=4,
            repeats=1,
        )
        self.motor.initialize()
        self.lock_in.initialize()
        use_case = MeasureSpectrogramUseCase(self.motor, self.lock_in)

        points = list(use_case.execute(settings=settings))
        self.assertEqual(len(points), settings.point_count)
        self.assertTrue(all(isinstance(point.signal, float) for point in points))

    def test_measure_spectrogram_can_stop_early(self) -> None:
        settings = ScanSettings(
            wait_time_ms=1,
            positive_border_mm=0.05,
            negative_border_mm=0.05,
            step_units=2,
            repeats=1,
        )
        self.motor.initialize()
        self.lock_in.initialize()
        use_case = MeasureSpectrogramUseCase(self.motor, self.lock_in)

        counter = {"i": 0}

        def should_stop() -> bool:
            counter["i"] += 1
            return counter["i"] > 3

        points = list(use_case.execute(settings=settings, should_stop=should_stop))
        self.assertLess(len(points), settings.point_count)

    def test_measure_waits_before_first_point_and_returns_home(self) -> None:
        settings = ScanSettings(
            wait_time_ms=250,
            positive_border_mm=0.02,
            negative_border_mm=0.02,
            step_units=4,
            repeats=1,
        )
        motor = _FakeMotor()
        lock_in = _FakeLockIn()
        use_case = MeasureSpectrogramUseCase(motor, lock_in)

        states: list[str] = []
        sleeps: list[float] = []

        with patch(
            "fts_scanner.use_cases.measure_spectrogram.time.sleep",
            side_effect=lambda sec: sleeps.append(float(sec)),
        ):
            points = list(use_case.execute(settings=settings, on_state=states.append))

        self.assertEqual(len(points), settings.point_count)
        self.assertTrue(sleeps)
        self.assertAlmostEqual(sleeps[0], settings.wait_time_ms / 1000.0, places=6)
        self.assertIn(("move_to", 0), motor.calls)
        self.assertIn("Returning home 0", states)
        self.assertIn("Home 0 reached", states)


if __name__ == "__main__":
    unittest.main()
