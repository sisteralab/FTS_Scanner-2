from __future__ import annotations

from dataclasses import dataclass, field
from itertools import count
from threading import Event, Lock
import time
from typing import Any

from PySide6.QtCore import QObject, Qt, Signal, Slot

from fts_scanner.devices.interfaces import MotorDevice, MotorMotionStatus


@dataclass(slots=True)
class _PendingRequest:
    event: Event = field(default_factory=Event)
    result: Any = None
    error: str | None = None


class MotorCommandClient(QObject):
    """Synchronous command client that routes all motor calls through MotorIoWorker."""

    request_move_to = Signal(int, int)
    request_move_by = Signal(int, int)
    request_get_position = Signal(int)
    request_set_zero = Signal(int)
    request_stop = Signal(int)
    request_start_jog = Signal(int, int)
    request_get_motion_params = Signal(int)
    request_set_motion_params = Signal(int, int, int)
    request_get_motion_status = Signal(int)

    def __init__(self, worker: QObject, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._worker = worker
        self._id_counter = count(1)
        self._pending_lock = Lock()
        self._pending: dict[int, _PendingRequest] = {}

        self.request_move_to.connect(worker.sync_move_to, Qt.ConnectionType.QueuedConnection)
        self.request_move_by.connect(worker.sync_move_by, Qt.ConnectionType.QueuedConnection)
        self.request_get_position.connect(
            worker.sync_get_position,
            Qt.ConnectionType.QueuedConnection,
        )
        self.request_set_zero.connect(worker.sync_set_zero, Qt.ConnectionType.QueuedConnection)
        self.request_stop.connect(worker.sync_stop, Qt.ConnectionType.QueuedConnection)
        self.request_start_jog.connect(worker.sync_start_jog, Qt.ConnectionType.QueuedConnection)
        self.request_get_motion_params.connect(
            worker.sync_get_motion_params,
            Qt.ConnectionType.QueuedConnection,
        )
        self.request_set_motion_params.connect(
            worker.sync_set_motion_params,
            Qt.ConnectionType.QueuedConnection,
        )
        self.request_get_motion_status.connect(
            worker.sync_get_motion_status,
            Qt.ConnectionType.QueuedConnection,
        )

        worker.sync_command_completed.connect(
            self._on_command_completed,
            Qt.ConnectionType.DirectConnection,
        )
        worker.sync_command_failed.connect(
            self._on_command_failed,
            Qt.ConnectionType.DirectConnection,
        )

    def move_to(self, steps: int) -> None:
        self._dispatch_no_result(self.request_move_to, int(steps), timeout_s=30.0)

    def move_by(self, delta_steps: int) -> None:
        self._dispatch_no_result(self.request_move_by, int(delta_steps), timeout_s=30.0)

    def wait_for_stop(self, timeout_ms: int) -> None:
        poll_interval_s = max(0.01, min(float(timeout_ms) / 1000.0, 0.2))
        while True:
            status = self.get_motion_status()
            position = self.get_position()
            if not bool(status.is_moving):
                return
            time.sleep(poll_interval_s)

    def get_position(self) -> int:
        result = self._dispatch_with_result(self.request_get_position, timeout_s=5.0)
        return int(result)

    def set_zero(self) -> None:
        self._dispatch_no_result(self.request_set_zero, timeout_s=5.0)

    def stop(self) -> None:
        self._dispatch_no_result(self.request_stop, timeout_s=5.0)

    def start_jog(self, direction: int) -> None:
        self._dispatch_no_result(self.request_start_jog, int(direction), timeout_s=5.0)

    def get_motion_params(self) -> tuple[int, int]:
        result = self._dispatch_with_result(self.request_get_motion_params, timeout_s=5.0)
        speed, acceleration = result
        return int(speed), int(acceleration)

    def set_motion_params(self, speed: int, acceleration: int) -> tuple[int, int]:
        result = self._dispatch_with_result(
            self.request_set_motion_params,
            int(speed),
            int(acceleration),
            timeout_s=5.0,
        )
        applied_speed, applied_acceleration = result
        return int(applied_speed), int(applied_acceleration)

    def get_motion_status(self) -> MotorMotionStatus:
        result = self._dispatch_with_result(self.request_get_motion_status, timeout_s=5.0)
        if isinstance(result, MotorMotionStatus):
            return result
        raise RuntimeError("Invalid motion status response")

    def _dispatch_no_result(self, signal: Signal, *args: Any, timeout_s: float) -> None:
        self._dispatch(signal, *args, timeout_s=timeout_s)

    def _dispatch_with_result(self, signal: Signal, *args: Any, timeout_s: float) -> Any:
        return self._dispatch(signal, *args, timeout_s=timeout_s)

    def _dispatch(self, signal: Signal, *args: Any, timeout_s: float) -> Any:
        request_id = next(self._id_counter)
        pending = _PendingRequest()
        with self._pending_lock:
            self._pending[request_id] = pending

        signal.emit(request_id, *args)
        if not pending.event.wait(timeout_s):
            with self._pending_lock:
                self._pending.pop(request_id, None)
            raise TimeoutError(f"Motor command timed out after {timeout_s:.1f}s")
        if pending.error is not None:
            raise RuntimeError(pending.error)
        return pending.result

    @Slot(int, object)
    def _on_command_completed(self, request_id: int, result: Any) -> None:
        with self._pending_lock:
            pending = self._pending.pop(int(request_id), None)
        if pending is None:
            return
        pending.result = result
        pending.event.set()

    @Slot(int, str)
    def _on_command_failed(self, request_id: int, error: str) -> None:
        with self._pending_lock:
            pending = self._pending.pop(int(request_id), None)
        if pending is None:
            return
        pending.error = str(error)
        pending.event.set()


@dataclass(slots=True)
class WorkerMotorDevice(MotorDevice):
    """MotorDevice adapter that delegates all calls to MotorCommandClient."""

    client: MotorCommandClient

    def initialize(self) -> None:
        raise RuntimeError("WorkerMotorDevice does not support initialize()")

    def move_to(self, steps: int) -> None:
        self.client.move_to(steps)

    def move_by(self, delta_steps: int) -> None:
        self.client.move_by(delta_steps)

    def wait_for_stop(self, timeout_ms: int) -> None:
        self.client.wait_for_stop(timeout_ms)

    def get_position(self) -> int:
        return self.client.get_position()

    def set_zero(self) -> None:
        self.client.set_zero()

    def stop(self) -> None:
        self.client.stop()

    def start_jog(self, direction: int) -> None:
        self.client.start_jog(direction)

    def get_motion_params(self) -> tuple[int, int]:
        return self.client.get_motion_params()

    def set_motion_params(self, speed: int, acceleration: int) -> None:
        self.client.set_motion_params(speed, acceleration)

    def get_motion_status(self) -> MotorMotionStatus:
        return self.client.get_motion_status()

    def shutdown(self) -> None:
        raise RuntimeError("WorkerMotorDevice does not support shutdown()")
