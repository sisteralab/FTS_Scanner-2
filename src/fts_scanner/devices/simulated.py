from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from threading import RLock
import time


@dataclass(slots=True)
class SimulatedMotorDevice:
    """In-memory motor emulator for development without hardware."""

    position_steps: int = 0
    motion_speed: int = 1000
    motion_acceleration: int = 1000
    _jog_direction: int = 0
    _last_update_ts: float = field(default_factory=time.monotonic)
    _lock: RLock = field(default_factory=RLock, repr=False)

    def initialize(self) -> None:
        """No-op for simulator."""

    def move_to(self, steps: int) -> None:
        """Set absolute position."""
        with self._lock:
            self._update_jog_position()
            self.position_steps = int(steps)

    def move_by(self, delta_steps: int) -> None:
        """Shift by delta steps."""
        with self._lock:
            self._update_jog_position()
            self.position_steps += int(delta_steps)

    def wait_for_stop(self, timeout_ms: int) -> None:
        """No-op for simulator."""

    def get_position(self) -> int:
        """Return current position."""
        with self._lock:
            self._update_jog_position()
            return self.position_steps

    def set_zero(self) -> None:
        """Set current simulated position to zero."""
        with self._lock:
            self._update_jog_position()
            self.position_steps = 0

    def stop(self) -> None:
        """Stop continuous jog motion."""
        with self._lock:
            self._update_jog_position()
            self._jog_direction = 0

    def start_jog(self, direction: int) -> None:
        """Start continuous jog in `-1`/`+1` direction."""
        with self._lock:
            self._update_jog_position()
            self._jog_direction = 1 if direction > 0 else -1

    def get_motion_params(self) -> tuple[int, int]:
        """Return current simulated speed and acceleration."""
        with self._lock:
            return self.motion_speed, self.motion_acceleration

    def set_motion_params(self, speed: int, acceleration: int) -> None:
        """Apply simulated speed and acceleration."""
        with self._lock:
            self.motion_speed = max(1, int(speed))
            self.motion_acceleration = max(1, int(acceleration))

    def shutdown(self) -> None:
        """No-op for simulator."""

    def _update_jog_position(self) -> None:
        now = time.monotonic()
        dt = now - self._last_update_ts
        self._last_update_ts = now
        if self._jog_direction == 0 or dt <= 0:
            return

        # Approximate continuous travel using current speed (steps/s).
        delta = int(self._jog_direction * self.motion_speed * dt)
        if delta == 0:
            delta = self._jog_direction
        self.position_steps += delta


@dataclass(slots=True)
class SimulatedLockInDevice:
    """Generates pseudo-signal for scan and monitoring."""

    noise_scale: float = 0.03
    _phase: float = 0.0
    _random: random.Random = field(default_factory=random.Random)

    def initialize(self) -> None:
        """No-op for simulator."""

    def identify(self) -> str:
        """Return synthetic id string."""
        return "SIMULATED,SR830,0,1.0"

    def read_signal(self) -> float:
        """Generate a smooth oscillating signal with noise."""
        self._phase += 0.1
        base = math.sin(self._phase) + 0.5 * math.sin(self._phase * 0.3)
        return base + self._random.uniform(-self.noise_scale, self.noise_scale)

    def shutdown(self) -> None:
        """No-op for simulator."""
