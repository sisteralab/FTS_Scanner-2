from __future__ import annotations

from fts_scanner.devices.interfaces import LockInDevice


class ReadSignalUseCase:
    """Read one lock-in signal value for monitoring."""

    def __init__(self, lock_in: LockInDevice) -> None:
        self._lock_in = lock_in

    def execute(self) -> float:
        """Return current signal value from lock-in."""
        return self._lock_in.read_signal()
