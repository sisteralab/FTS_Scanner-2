from __future__ import annotations

import unittest
from unittest.mock import patch

import pyvisa

from fts_scanner.devices.sr830 import SR830VisaLockIn


class TestSR830VisaLockIn(unittest.TestCase):
    def test_format_initialize_error_for_missing_library(self) -> None:
        error = pyvisa.errors.VisaIOError(pyvisa.constants.StatusCode.error_library_not_found)
        message = SR830VisaLockIn._format_initialize_error(error)
        self.assertIn("VI_ERROR_LIBRARY_NOT_FOUND", message)
        self.assertIn("Simulation mode", message)

    def test_initialize_wraps_error(self) -> None:
        device = SR830VisaLockIn(resource_name="GPIB1::8::INSTR")
        error = pyvisa.errors.VisaIOError(pyvisa.constants.StatusCode.error_library_not_found)

        with patch("pyvisa.ResourceManager", side_effect=error):
            with self.assertRaises(RuntimeError) as ctx:
                device.initialize()

        self.assertIn("VISA backend library is not found", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
