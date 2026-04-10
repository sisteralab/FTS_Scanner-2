from __future__ import annotations

import threading
import time
import unittest

from fts_scanner.devices.interfaces import MotorMotionStatus
from fts_scanner.devices.serialized_motor import SerializedMotorDevice


class ConcurrencyDetectingMotor:
    def __init__(self) -> None:
        self.position = 0
        self.active_calls = 0
        self.max_active_calls = 0
        self._counter_lock = threading.Lock()

    def initialize(self) -> None:
        self._enter()
        self._exit()

    def move_to(self, steps: int) -> None:
        self._enter()
        self.position = int(steps)
        time.sleep(0.02)
        self._exit()

    def move_by(self, delta_steps: int) -> None:
        self._enter()
        self.position += int(delta_steps)
        time.sleep(0.01)
        self._exit()

    def wait_for_stop(self, timeout_ms: int) -> None:
        self._enter()
        time.sleep(0.005)
        self._exit()

    def get_position(self) -> int:
        self._enter()
        time.sleep(0.01)
        result = self.position
        self._exit()
        return result

    def set_zero(self) -> None:
        self._enter()
        self.position = 0
        self._exit()

    def stop(self) -> None:
        self._enter()
        self._exit()

    def start_jog(self, direction: int) -> None:
        self._enter()
        self._exit()

    def get_motion_params(self) -> tuple[int, int]:
        self._enter()
        self._exit()
        return 1000, 500

    def set_motion_params(self, speed: int, acceleration: int) -> None:
        self._enter()
        self._exit()

    def get_motion_status(self) -> MotorMotionStatus:
        self._enter()
        self._exit()
        return MotorMotionStatus(is_moving=False, has_error=False, command="idle")

    def shutdown(self) -> None:
        self._enter()
        self._exit()

    def _enter(self) -> None:
        with self._counter_lock:
            self.active_calls += 1
            self.max_active_calls = max(self.max_active_calls, self.active_calls)

    def _exit(self) -> None:
        with self._counter_lock:
            self.active_calls -= 1


class TestSerializedMotor(unittest.TestCase):
    def test_serializes_concurrent_motor_calls(self) -> None:
        raw_motor = ConcurrencyDetectingMotor()
        motor = SerializedMotorDevice(raw_motor)
        barrier = threading.Barrier(3)

        def move_task() -> None:
            barrier.wait()
            motor.move_to(100)

        def read_task() -> None:
            barrier.wait()
            motor.get_position()

        thread_one = threading.Thread(target=move_task)
        thread_two = threading.Thread(target=read_task)
        thread_one.start()
        thread_two.start()
        barrier.wait()
        thread_one.join()
        thread_two.join()

        self.assertEqual(raw_motor.max_active_calls, 1)


if __name__ == "__main__":
    unittest.main()
