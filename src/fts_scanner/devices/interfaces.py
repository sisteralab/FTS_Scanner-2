from __future__ import annotations

from typing import Protocol


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
