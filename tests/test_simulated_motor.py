from __future__ import annotations

import time
import unittest

from fts_scanner.devices.simulated import SimulatedMotorDevice


class TestSimulatedMotor(unittest.TestCase):
    def test_motion_params_roundtrip(self) -> None:
        motor = SimulatedMotorDevice()
        motor.set_motion_params(1500, 800)
        speed, accel = motor.get_motion_params()
        self.assertEqual(speed, 1500)
        self.assertEqual(accel, 800)

    def test_jog_moves_until_stop(self) -> None:
        motor = SimulatedMotorDevice(motion_speed=500)
        motor.initialize()
        start = motor.get_position()

        motor.start_jog(1)
        time.sleep(0.03)
        pos_during_jog = motor.get_position()
        self.assertGreater(pos_during_jog, start)

        motor.stop()
        stopped = motor.get_position()
        time.sleep(0.03)
        self.assertEqual(motor.get_position(), stopped)


if __name__ == "__main__":
    unittest.main()
