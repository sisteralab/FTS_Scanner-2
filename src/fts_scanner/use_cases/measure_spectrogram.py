from __future__ import annotations

import time
from collections.abc import Callable, Iterator

from fts_scanner.devices.interfaces import LockInDevice, MotorDevice
from fts_scanner.domain.models import ScanSettings, SpectrumPoint


class MeasureSpectrogramUseCase:
    """Perform full FTS spectrogram scan point-by-point."""

    def __init__(self, motor: MotorDevice, lock_in: LockInDevice) -> None:
        self._motor = motor
        self._lock_in = lock_in

    def execute(
        self,
        settings: ScanSettings,
        should_stop: Callable[[], bool] | None = None,
        should_pause: Callable[[], bool] | None = None,
    ) -> Iterator[SpectrumPoint]:
        """Yield measurement points as they are acquired."""
        stop_check = should_stop or (lambda: False)
        pause_check = should_pause or (lambda: False)

        wait_seconds = max(0.0, settings.wait_time_ms / 1000.0)
        stop_requested = False
        try:
            for repeat in range(settings.repeats):
                if stop_check():
                    stop_requested = True
                    break

                self._motor.move_to(settings.start_steps)
                self._motor.wait_for_stop(settings.wait_time_ms)

                # Let lock-in settle at scan start before first sample.
                if not self._delay_with_controls(wait_seconds, stop_check, pause_check):
                    stop_requested = True
                    break

                for index in range(settings.point_count):
                    if stop_check():
                        stop_requested = True
                        break

                    while pause_check() and not stop_check():
                        time.sleep(0.05)
                    if stop_check():
                        stop_requested = True
                        break

                    position = self._motor.get_position()
                    signal = self._lock_in.read_signal()
                    yield SpectrumPoint(
                        index=index,
                        repeat=repeat,
                        position_steps=position,
                        signal=signal,
                    )

                    is_last_point = index == settings.point_count - 1
                    if not is_last_point and not stop_check():
                        self._motor.move_by(settings.step_units)
                        self._motor.wait_for_stop(settings.wait_time_ms)
        finally:
            if stop_requested:
                self._motor.stop()
            self._motor.move_to(0)
            self._motor.wait_for_stop(settings.wait_time_ms)

    @staticmethod
    def _delay_with_controls(
        delay_seconds: float,
        stop_check: Callable[[], bool],
        pause_check: Callable[[], bool],
    ) -> bool:
        if delay_seconds <= 0:
            return not stop_check()
        deadline = time.monotonic() + delay_seconds
        while time.monotonic() < deadline:
            if stop_check():
                return False
            while pause_check() and not stop_check():
                time.sleep(0.05)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(0.05, remaining))
        return not stop_check()
