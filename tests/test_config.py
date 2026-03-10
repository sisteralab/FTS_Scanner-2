from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fts_scanner.config import AppConfig
from fts_scanner.devices.lockin_types import LockInAdapterType


class TestConfig(unittest.TestCase):
    def test_save_and_load_ini_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = AppConfig.from_project_root(root)
            cfg.use_simulation = True
            cfg.lock_in_adapter = LockInAdapterType.KEYSIGHT_VISA
            cfg.lock_in_visa_resource = "TCPIP0::192.168.0.2::5025::SOCKET"
            cfg.lock_in_visa_library = "/opt/keysight/visa/libvisa.so"
            cfg.lock_in_host = "10.0.0.1"
            cfg.lock_in_port = 4555
            cfg.lock_in_usb_port = "/dev/ttyUSB0"
            cfg.lock_in_gpib_address = 12
            cfg.motor_name = "xi-com:\\\\.\\COM8"
            cfg.ximc_root = Path("./vendor/ximc")
            cfg.save_to_ini()

            loaded = AppConfig.from_project_root(root)
            self.assertTrue(loaded.use_simulation)
            self.assertEqual(loaded.lock_in_adapter, LockInAdapterType.KEYSIGHT_VISA)
            self.assertEqual(loaded.lock_in_visa_resource, "TCPIP0::192.168.0.2::5025::SOCKET")
            self.assertEqual(loaded.lock_in_visa_library, "/opt/keysight/visa/libvisa.so")
            self.assertEqual(loaded.lock_in_host, "10.0.0.1")
            self.assertEqual(loaded.lock_in_port, 4555)
            self.assertEqual(loaded.lock_in_usb_port, "/dev/ttyUSB0")
            self.assertEqual(loaded.lock_in_gpib_address, 12)
            self.assertEqual(loaded.motor_name, "xi-com:\\\\.\\COM8")
            self.assertEqual(loaded.ximc_root, root / "vendor" / "ximc")


if __name__ == "__main__":
    unittest.main()
