from __future__ import annotations

import math
import random
from dataclasses import dataclass, field


@dataclass(slots=True)
class SimulatedMotorDevice:
    """In-memory motor emulator for development without hardware."""

    position_steps: int = 0

    def initialize(self) -> None:
        """No-op for simulator."""

    def move_to(self, steps: int) -> None:
        """Set absolute position."""
        self.position_steps = int(steps)

    def move_by(self, delta_steps: int) -> None:
        """Shift by delta steps."""
        self.position_steps += int(delta_steps)

    def wait_for_stop(self, timeout_ms: int) -> None:
        """No-op for simulator."""

    def get_position(self) -> int:
        """Return current position."""
        return self.position_steps

    def stop(self) -> None:
        """No-op for simulator."""

    def shutdown(self) -> None:
        """No-op for simulator."""


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
