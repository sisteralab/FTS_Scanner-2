from __future__ import annotations

import time
import unittest

from fts_scanner.devices.simulated import SimulatedLockInDevice, SimulatedMotorDevice
from fts_scanner.domain.models import ScanSettings
from fts_scanner.use_cases.initialize import InitializeHardwareUseCase
from fts_scanner.use_cases.measure_spectrogram import MeasureSpectrogramUseCase
from fts_scanner.use_cases.monitor import ReadSignalUseCase


class TrackingMotor(SimulatedMotorDevice):
    def __init__(self) -> None:
        super().__init__()
        self.move_to_timestamps: list[float] = []

    def move_to(self, steps: int) -> None:
        super().move_to(steps)
        self.move_to_timestamps.append(time.monotonic())


class TrackingLockIn(SimulatedLockInDevice):
    def __init__(self) -> None:
        super().__init__(noise_scale=0.0)
        self.read_timestamps: list[float] = []

    def read_signal(self) -> float:
        self.read_timestamps.append(time.monotonic())
        return super().read_signal()


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
        self.assertEqual(self.motor.get_position(), 0)

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
        self.assertEqual(self.motor.get_position(), 0)

    def test_measurement_waits_before_first_point(self) -> None:
        motor = TrackingMotor()
        lock_in = TrackingLockIn()
        settings = ScanSettings(
            wait_time_ms=40,
            positive_border_mm=0.0,
            negative_border_mm=0.0,
            step_units=1,
            repeats=1,
        )
        motor.initialize()
        lock_in.initialize()
        use_case = MeasureSpectrogramUseCase(motor, lock_in)

        points = list(use_case.execute(settings=settings))

        self.assertEqual(len(points), 1)
        self.assertGreaterEqual(len(motor.move_to_timestamps), 1)
        self.assertGreaterEqual(len(lock_in.read_timestamps), 1)
        first_move_ts = motor.move_to_timestamps[0]
        first_read_ts = lock_in.read_timestamps[0]
        self.assertGreaterEqual(first_read_ts - first_move_ts, 0.03)


if __name__ == "__main__":
    unittest.main()
