from __future__ import annotations

import tempfile
import unittest
from uuid import uuid4
from pathlib import Path

from PySide6.QtCore import QSettings

from fts_scanner.config import AppConfig
from fts_scanner.devices.lockin_types import LockInAdapterType


class TestConfig(unittest.TestCase):
    def test_save_and_load_native_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            org = f"ASC_TEST_{uuid4().hex}"
            app = f"FTS Scanner TEST {uuid4().hex}"
            self._clear_native(org, app)

            cfg = AppConfig(
                ximc_root=root / "ximc",
                settings_file=root / "settings.ini",
                settings_organization=org,
                settings_application=app,
            )
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
            cfg.motor_speed = 2222
            cfg.motor_acceleration = 3333
            cfg.save()

            loaded = AppConfig(
                ximc_root=root / "ximc",
                settings_file=root / "settings.ini",
                settings_organization=org,
                settings_application=app,
            )
            loaded.load()
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
            self.assertEqual(loaded.motor_speed, 2222)
            self.assertEqual(loaded.motor_acceleration, 3333)
            self._clear_native(org, app)

    def test_migrates_legacy_ini_to_native_settings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            org = f"ASC_TEST_{uuid4().hex}"
            app = f"FTS Scanner TEST {uuid4().hex}"
            self._clear_native(org, app)

            legacy = AppConfig(
                ximc_root=root / "ximc",
                settings_file=root / "settings.ini",
                settings_organization=org,
                settings_application=app,
            )
            legacy.use_simulation = True
            legacy.motor_name = "xi-com:\\\\.\\COM11"
            legacy.ximc_root = Path("./legacy/ximc")
            legacy.motor_speed = 1500
            legacy.motor_acceleration = 700
            legacy.save_to_ini()

            migrated = AppConfig(
                ximc_root=root / "ximc",
                settings_file=root / "settings.ini",
                settings_organization=org,
                settings_application=app,
            )
            migrated.load()
            self.assertEqual(migrated.motor_name, "xi-com:\\\\.\\COM11")
            self.assertEqual(migrated.ximc_root, root / "legacy" / "ximc")
            self.assertEqual(migrated.motor_speed, 1500)
            self.assertEqual(migrated.motor_acceleration, 700)

            migrated.settings_file.unlink()
            loaded_from_native = AppConfig(
                ximc_root=root / "ximc",
                settings_file=root / "settings.ini",
                settings_organization=org,
                settings_application=app,
            )
            loaded_from_native.load()
            self.assertEqual(loaded_from_native.motor_name, "xi-com:\\\\.\\COM11")
            self.assertEqual(loaded_from_native.motor_speed, 1500)
            self.assertEqual(loaded_from_native.motor_acceleration, 700)
            self._clear_native(org, app)

    @staticmethod
    def _clear_native(organization: str, application: str) -> None:
        settings = QSettings(
            QSettings.Format.NativeFormat,
            QSettings.Scope.UserScope,
            organization,
            application,
        )
        settings.clear()
        settings.sync()


if __name__ == "__main__":
    unittest.main()
