from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class MotorMotionStatus:
    """Current motor motion state snapshot."""

    is_moving: bool
    has_error: bool
    command: str
    command_code: int = 0


class MotorDevice(Protocol):
    """Abstract motor interface used by business use-cases."""

    def initialize(self) -> None:
        """Open and prepare motor device for commands."""

    def move_to(self, steps: int) -> None:
        """Move stage to absolute position in steps."""

    def move_by(self, delta_steps: int) -> None:
        """Move stage relative to current position in steps."""

    def wait_for_stop(self, timeout_ms: int) -> None:
        """Block until movement is complete or timeout is reached."""

    def get_position(self) -> int:
        """Read current stage position in steps."""

    def set_zero(self) -> None:
        """Set current stage position as logical zero."""

    def stop(self) -> None:
        """Emergency stop motion."""

    def start_jog(self, direction: int) -> None:
        """Start continuous movement in direction: -1 left, +1 right."""

    def get_motion_params(self) -> tuple[int, int]:
        """Return current (speed, acceleration) settings."""

    def set_motion_params(self, speed: int, acceleration: int) -> None:
        """Apply (speed, acceleration) settings."""

    def get_motion_status(self) -> MotorMotionStatus:
        """Return current movement status and active command."""

    def shutdown(self) -> None:
        """Release all resources."""


class LockInDevice(Protocol):
    """Abstract lock-in interface used by business use-cases."""

    def initialize(self) -> None:
        """Open connection and verify lock-in availability."""

    def identify(self) -> str:
        """Return lock-in identification string."""

    def read_signal(self) -> float:
        """Read signal value used for the spectrogram."""

    def shutdown(self) -> None:
        """Release all resources."""
