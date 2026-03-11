from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Signal, Slot

logger = logging.getLogger(__name__)


class MotorIoWorker(QObject):
    """Runs motor I/O calls in a dedicated thread."""

    position_ready = Signal(int)
    command_error = Signal(str)
    motion_params_ready = Signal(int, int)
    motion_params_applied = Signal(int, int)

    def __init__(self, motor: object) -> None:
        super().__init__()
        self._motor = motor
        self._busy = False
        self._is_jogging = False

    @Slot()
    def poll_position(self) -> None:
        """Read position if worker is idle."""
        if self._busy:
            return
        try:
            position = int(self._motor.get_position())
            self.position_ready.emit(position)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Motor position polling failed")
            self.command_error.emit(f"Motor polling error: {exc}")

    @Slot(int, int)
    def move_by(self, delta_steps: int, wait_ms: int) -> None:
        """Execute relative motor move."""
        if self._busy:
            return
        self._busy = True
        try:
            if self._is_jogging:
                self._motor.stop()
                self._is_jogging = False
            self._motor.move_by(int(delta_steps))
            self._motor.wait_for_stop(int(wait_ms))
            self.position_ready.emit(int(self._motor.get_position()))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Relative motor move failed")
            self.command_error.emit(f"Motor move failed: {exc}")
        finally:
            self._busy = False

    @Slot(int, int)
    def move_to(self, target_steps: int, wait_ms: int) -> None:
        """Execute absolute motor move."""
        if self._busy:
            return
        self._busy = True
        try:
            if self._is_jogging:
                self._motor.stop()
                self._is_jogging = False
            self._motor.move_to(int(target_steps))
            self._motor.wait_for_stop(int(wait_ms))
            self.position_ready.emit(int(self._motor.get_position()))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Absolute motor move failed")
            self.command_error.emit(f"Motor move failed: {exc}")
        finally:
            self._busy = False

    @Slot()
    def set_zero(self) -> None:
        """Set motor logical zero and emit updated position."""
        if self._busy:
            return
        self._busy = True
        try:
            if self._is_jogging:
                self._motor.stop()
                self._is_jogging = False
            self._motor.set_zero()
            self.position_ready.emit(int(self._motor.get_position()))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Set zero failed")
            self.command_error.emit(f"Set zero failed: {exc}")
        finally:
            self._busy = False

    @Slot(int)
    def start_jog(self, direction: int) -> None:
        """Start continuous jog for as long as button is held."""
        if self._busy:
            return
        if direction == 0:
            return
        try:
            if self._is_jogging:
                self._motor.stop()
            self._motor.start_jog(int(direction))
            self._is_jogging = True
        except Exception as exc:  # noqa: BLE001
            logger.exception("Start jog failed")
            self.command_error.emit(f"Start jog failed: {exc}")

    @Slot()
    def stop_motion(self) -> None:
        """Stop current motor motion."""
        try:
            self._motor.stop()
            self._is_jogging = False
            self.position_ready.emit(int(self._motor.get_position()))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Stop motor failed")
            self.command_error.emit(f"Stop motor failed: {exc}")

    @Slot()
    def read_motion_params(self) -> None:
        """Read speed/acceleration parameters from motor."""
        if self._busy:
            return
        try:
            speed, acceleration = self._motor.get_motion_params()
            self.motion_params_ready.emit(int(speed), int(acceleration))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Read motion params failed")
            self.command_error.emit(f"Read motion params failed: {exc}")

    @Slot(int, int)
    def set_motion_params(self, speed: int, acceleration: int) -> None:
        """Apply speed/acceleration parameters to motor."""
        if self._busy:
            return
        self._busy = True
        try:
            self._motor.set_motion_params(int(speed), int(acceleration))
            applied_speed, applied_accel = self._motor.get_motion_params()
            self.motion_params_applied.emit(int(applied_speed), int(applied_accel))
            self.motion_params_ready.emit(int(applied_speed), int(applied_accel))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Set motion params failed")
            self.command_error.emit(f"Set motion params failed: {exc}")
        finally:
            self._busy = False


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
