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

        for repeat in range(settings.repeats):
            if stop_check():
                break
            self._motor.move_to(settings.start_steps)
            self._motor.wait_for_stop(settings.wait_time_ms)

            for index in range(settings.point_count):
                if stop_check():
                    break

                while pause_check() and not stop_check():
                    time.sleep(0.05)

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

        if stop_check():
            self._motor.stop()
