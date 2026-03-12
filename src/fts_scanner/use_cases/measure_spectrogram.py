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
        on_state: Callable[[str], None] | None = None,
    ) -> Iterator[SpectrumPoint]:
        """Yield measurement points as they are acquired."""
        stop_check = should_stop or (lambda: False)
        pause_check = should_pause or (lambda: False)
        state_cb = on_state or (lambda _state: None)

        try:
            for repeat in range(settings.repeats):
                if stop_check():
                    break
                state_cb("Moving to scan start")
                self._motor.move_to(settings.start_steps)
                self._motor.wait_for_stop(max(2000, settings.wait_time_ms * 5))

                # Let lock-in integrate before the very first point.
                state_cb("Integrating before first point")
                time.sleep(settings.wait_time_ms / 1000.0)

                for index in range(settings.point_count):
                    if stop_check():
                        break

                    if pause_check() and not stop_check():
                        state_cb("Paused")
                    while pause_check() and not stop_check():
                        time.sleep(0.05)

                    state_cb("Acquiring point")
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
                        state_cb("Moving to next point")
                        self._motor.move_by(settings.step_units)
                        self._motor.wait_for_stop(max(2000, settings.wait_time_ms * 5))
                        time.sleep(settings.wait_time_ms / 1000.0)
        finally:
            if stop_check():
                state_cb("Stopping motion")
                self._motor.stop()

            # Always return stage to home at the end.
            state_cb("Returning home 0")
            try:
                self._motor.move_to(0)
                self._motor.wait_for_stop(15_000)
                state_cb("Home 0 reached")
            except Exception:  # noqa: BLE001
                state_cb("Home return failed")
