from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot

logger = logging.getLogger(__name__)


class MotorIoWorker(QObject):
    """Runs motor I/O calls in a dedicated thread."""

    position_ready = Signal(int)
    command_error = Signal(str)
    motion_params_ready = Signal(int, int)
    motion_params_applied = Signal(int, int)
    motion_state_ready = Signal(str)

    def __init__(self, motor: object) -> None:
        super().__init__()
        self._motor = motor
        self._is_jogging = False
        self._target_position: Optional[int] = None
        self._last_state_text = ""

    @Slot()
    def poll_position(self) -> None:
        """Read current position and active movement state."""
        try:
            position = int(self._motor.get_position())
            self.position_ready.emit(position)

            status = self._motor.get_motion_status()
            state_text = self._format_state_text(
                is_moving=bool(status.is_moving),
                has_error=bool(status.has_error),
                command=str(status.command),
                command_code=int(status.command_code),
                position=position,
            )
            self._emit_state(state_text)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Motor position polling failed")
            self.command_error.emit(f"Motor polling error: {exc}")

    @Slot(int, int)
    def move_by(self, delta_steps: int, wait_ms: int) -> None:
        """Execute non-blocking relative move and keep polling alive."""
        try:
            if self._is_jogging:
                self._motor.stop()
                self._is_jogging = False
            current = int(self._motor.get_position())
            delta = int(delta_steps)
            self._target_position = current + delta
            self._motor.move_by(delta)
            self._emit_state(f"Moving by {delta} steps to {self._target_position}")
        except Exception as exc:  # noqa: BLE001
            logger.exception("Relative motor move failed")
            self.command_error.emit(f"Motor move failed: {exc}")

    @Slot(int, int)
    def move_to(self, target_steps: int, wait_ms: int) -> None:
        """Execute non-blocking absolute move and keep polling alive."""
        try:
            if self._is_jogging:
                self._motor.stop()
                self._is_jogging = False
            self._target_position = int(target_steps)
            self._motor.move_to(self._target_position)
            self._emit_state(f"Moving to {self._target_position} steps")
        except Exception as exc:  # noqa: BLE001
            logger.exception("Absolute motor move failed")
            self.command_error.emit(f"Motor move failed: {exc}")

    @Slot()
    def set_zero(self) -> None:
        """Set motor logical zero and emit updated position."""
        try:
            if self._is_jogging:
                self._motor.stop()
                self._is_jogging = False
            self._motor.set_zero()
            self._target_position = None
            position = int(self._motor.get_position())
            self.position_ready.emit(position)
            self._emit_state("Zero set")
        except Exception as exc:  # noqa: BLE001
            logger.exception("Set zero failed")
            self.command_error.emit(f"Set zero failed: {exc}")

    @Slot(int)
    def start_jog(self, direction: int) -> None:
        """Start continuous jog for as long as button is held."""
        if direction == 0:
            return
        try:
            if self._is_jogging:
                self._motor.stop()
            self._motor.start_jog(int(direction))
            self._is_jogging = True
            self._target_position = None
            self._emit_state("Jogging right" if direction > 0 else "Jogging left")
        except Exception as exc:  # noqa: BLE001
            logger.exception("Start jog failed")
            self.command_error.emit(f"Start jog failed: {exc}")

    @Slot()
    def stop_motion(self) -> None:
        """Stop current motor motion."""
        try:
            self._motor.stop()
            self._is_jogging = False
            self._target_position = None
            position = int(self._motor.get_position())
            self.position_ready.emit(position)
            self._emit_state("Stopped")
        except Exception as exc:  # noqa: BLE001
            logger.exception("Stop motor failed")
            self.command_error.emit(f"Stop motor failed: {exc}")

    @Slot()
    def read_motion_params(self) -> None:
        """Read speed/acceleration parameters from motor."""
        try:
            speed, acceleration = self._motor.get_motion_params()
            self.motion_params_ready.emit(int(speed), int(acceleration))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Read motion params failed")
            self.command_error.emit(f"Read motion params failed: {exc}")

    @Slot(int, int)
    def set_motion_params(self, speed: int, acceleration: int) -> None:
        """Apply speed/acceleration parameters to motor."""
        try:
            self._motor.set_motion_params(int(speed), int(acceleration))
            applied_speed, applied_accel = self._motor.get_motion_params()
            self.motion_params_applied.emit(int(applied_speed), int(applied_accel))
            self.motion_params_ready.emit(int(applied_speed), int(applied_accel))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Set motion params failed")
            self.command_error.emit(f"Set motion params failed: {exc}")

    def _format_state_text(
        self,
        is_moving: bool,
        has_error: bool,
        command: str,
        command_code: int,
        position: int,
    ) -> str:
        if has_error:
            return f"Error in command '{command}' (code={command_code})"
        if is_moving:
            if self._target_position is not None:
                return (
                    f"Moving: cmd={command}, position={position}, "
                    f"target={self._target_position}"
                )
            return f"Moving: cmd={command}, position={position}"
        if self._target_position is not None:
            target = self._target_position
            self._target_position = None
            return f"Idle at {position} (target reached {target})"
        return f"Idle at {position}"

    def _emit_state(self, text: str) -> None:
        if text == self._last_state_text:
            return
        self._last_state_text = text
        self.motion_state_ready.emit(text)


class LockInIoWorker(QObject):
    """Runs lock-in signal reads in a dedicated thread."""

    signal_ready = Signal(float)
    poll_error = Signal(str)

    def __init__(self, lock_in: object) -> None:
        super().__init__()
        self._lock_in = lock_in
        self._busy = False

    @Slot()
    def read_signal(self) -> None:
        """Read signal from lock-in backend."""
        if self._busy:
            return
        self._busy = True
        try:
            value = float(self._lock_in.read_signal())
            self.signal_ready.emit(value)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Monitoring failed")
            self.poll_error.emit(f"Monitoring error: {exc}")
        finally:
            self._busy = False
