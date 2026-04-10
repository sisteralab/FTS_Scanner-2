from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock

from fts_scanner.devices.interfaces import MotorDevice, MotorMotionStatus


@dataclass(slots=True)
class SerializedMotorDevice:
    """Thread-safe proxy that serializes all access to one motor backend."""

    inner: MotorDevice
    _lock: RLock = field(default_factory=RLock)

    def initialize(self) -> None:
        with self._lock:
            self.inner.initialize()

    def move_to(self, steps: int) -> None:
        with self._lock:
            self.inner.move_to(steps)

    def move_by(self, delta_steps: int) -> None:
        with self._lock:
            self.inner.move_by(delta_steps)

    def wait_for_stop(self, timeout_ms: int) -> None:
        with self._lock:
            self.inner.wait_for_stop(timeout_ms)

    def get_position(self) -> int:
        with self._lock:
            return self.inner.get_position()

    def set_zero(self) -> None:
        with self._lock:
            self.inner.set_zero()

    def stop(self) -> None:
        with self._lock:
            self.inner.stop()

    def start_jog(self, direction: int) -> None:
        with self._lock:
            self.inner.start_jog(direction)

    def get_motion_params(self) -> tuple[int, int]:
        with self._lock:
            return self.inner.get_motion_params()

    def set_motion_params(self, speed: int, acceleration: int) -> None:
        with self._lock:
            self.inner.set_motion_params(speed, acceleration)

    def get_motion_status(self) -> MotorMotionStatus:
        with self._lock:
            return self.inner.get_motion_status()

    def shutdown(self) -> None:
        with self._lock:
            self.inner.shutdown()
