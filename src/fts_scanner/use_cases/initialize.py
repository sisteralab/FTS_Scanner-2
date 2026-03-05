from __future__ import annotations

from dataclasses import dataclass

from fts_scanner.devices.interfaces import LockInDevice, MotorDevice


@dataclass(slots=True)
class InitializationReport:
    """Result of hardware initialization step."""

    lock_in_idn: str
    motor_position_steps: int


class InitializeHardwareUseCase:
    """Prepare all physical devices before monitor/measurement."""

    def __init__(self, motor: MotorDevice, lock_in: LockInDevice) -> None:
        self._motor = motor
        self._lock_in = lock_in

    def execute(self) -> InitializationReport:
        """Initialize motor and lock-in and return short status report."""
        self._motor.initialize()
        self._lock_in.initialize()
        return InitializationReport(
            lock_in_idn=self._lock_in.identify(),
            motor_position_steps=self._motor.get_position(),
        )
