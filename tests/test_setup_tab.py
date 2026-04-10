from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

_APP = QApplication.instance() or QApplication([])

from fts_scanner.presentation.widgets.setup_tab import SetupTab


class FakeConfig:
    use_simulation = True
    lock_in_adapter = "prologix_ethernet"
    lock_in_host = "127.0.0.1"
    lock_in_port = 1234
    lock_in_usb_port = "/dev/tty.usbserial"
    lock_in_gpib_address = 8
    lock_in_visa_resource = "GPIB1::8::INSTR"
    lock_in_visa_library = ""
    motor_name = "motor"
    ximc_root = "ximc"


class FakeController(QObject):
    setup_status = Signal(bool, bool, str)
    measurement_started = Signal()
    measurement_finished = Signal()
    measurement_failed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.config = FakeConfig()

    def initialize_devices(self, **kwargs) -> None:  # noqa: ANN003
        return None


class TestSetupTab(unittest.TestCase):
    def test_connection_controls_lock_during_measurement(self) -> None:
        controller = FakeController()
        tab = SetupTab(controller)

        self.assertTrue(tab.init_button.isEnabled())

        controller.measurement_started.emit()
        self.assertFalse(tab.init_button.isEnabled())
        self.assertFalse(tab.simulation_checkbox.isEnabled())

        controller.measurement_finished.emit()
        self.assertTrue(tab.init_button.isEnabled())
        self.assertTrue(tab.simulation_checkbox.isEnabled())


if __name__ == "__main__":
    unittest.main()
