from __future__ import annotations

import types
import unittest
from unittest.mock import patch

from fts_scanner.devices.lockin_types import LockInAdapterType
from fts_scanner.devices.thzdaqapi_lockin import SR830ThzdaqapiLockIn


class _FakeAdapter:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class _FakeLockIn:
    last_kwargs = {}

    def __init__(self, host: str, gpib: int, adapter: str, port=None, *args, **kwargs) -> None:  # noqa: ANN001
        _FakeLockIn.last_kwargs = {
            "host": host,
            "gpib": gpib,
            "adapter": adapter,
            "port": port,
        }
        self.adapter = _FakeAdapter()

    def idn(self) -> str:
        return "FAKE,SR830,0,1.0"

    def get_out3(self) -> float:
        return 1.234


class _TrackableAdapter:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class _TrackablePrologix:
    _instances = {}


class TestThzdaqapiLockIn(unittest.TestCase):
    def test_initialize_identify_read_shutdown_ethernet(self) -> None:
        fake_settings = types.SimpleNamespace(
            PROLOGIX_ETHERNET="PROLOGIX ETHERNET",
            PROLOGIX_USB="PROLOGIX USB",
        )
        fake_lockin_module = types.SimpleNamespace(LockIn=_FakeLockIn)

        modules = {
            "thzdaqapi": types.SimpleNamespace(settings=fake_settings),
            "thzdaqapi.settings": fake_settings,
            "thzdaqapi.SRS": types.SimpleNamespace(),
            "thzdaqapi.SRS.LockIn_SR830": fake_lockin_module,
            "thzdaqapi.adapters": types.SimpleNamespace(),
            "thzdaqapi.adapters.prologix": types.SimpleNamespace(Prologix=_TrackablePrologix),
        }

        device = SR830ThzdaqapiLockIn(
            adapter_type=LockInAdapterType.PROLOGIX_ETHERNET,
            gpib_address=8,
            host="169.254.1.1",
            ethernet_port=1234,
        )

        with patch.dict("sys.modules", modules, clear=False):
            device.initialize()
            self.assertIn("FAKE", device.identify())
            self.assertAlmostEqual(device.read_signal(), 1.234, places=3)
            lockin_obj = device._lockin
            device.shutdown()
            self.assertTrue(lockin_obj.adapter.closed)

        self.assertEqual(_FakeLockIn.last_kwargs["host"], "169.254.1.1")
        self.assertEqual(_FakeLockIn.last_kwargs["gpib"], 8)

    def test_initialize_resets_existing_prologix_singleton(self) -> None:
        fake_settings = types.SimpleNamespace(
            PROLOGIX_ETHERNET="PROLOGIX ETHERNET",
            PROLOGIX_USB="PROLOGIX USB",
        )
        fake_lockin_module = types.SimpleNamespace(LockIn=_FakeLockIn)
        stale = _TrackableAdapter()
        _TrackablePrologix._instances = {"169.254.1.1": stale}

        modules = {
            "thzdaqapi": types.SimpleNamespace(settings=fake_settings),
            "thzdaqapi.settings": fake_settings,
            "thzdaqapi.SRS": types.SimpleNamespace(),
            "thzdaqapi.SRS.LockIn_SR830": fake_lockin_module,
            "thzdaqapi.adapters": types.SimpleNamespace(),
            "thzdaqapi.adapters.prologix": types.SimpleNamespace(Prologix=_TrackablePrologix),
        }

        device = SR830ThzdaqapiLockIn(
            adapter_type=LockInAdapterType.PROLOGIX_ETHERNET,
            gpib_address=8,
            host="169.254.1.1",
            ethernet_port=1234,
        )

        with patch.dict("sys.modules", modules, clear=False):
            device.initialize()

        self.assertTrue(stale.closed)
        self.assertNotIn("169.254.1.1", _TrackablePrologix._instances)

    def test_initialize_unsupported_adapter(self) -> None:
        device = SR830ThzdaqapiLockIn(
            adapter_type="unknown",
            gpib_address=8,
        )

        fake_settings = types.SimpleNamespace(
            PROLOGIX_ETHERNET="PROLOGIX ETHERNET",
            PROLOGIX_USB="PROLOGIX USB",
        )
        fake_lockin_module = types.SimpleNamespace(LockIn=_FakeLockIn)
        modules = {
            "thzdaqapi": types.SimpleNamespace(settings=fake_settings),
            "thzdaqapi.settings": fake_settings,
            "thzdaqapi.SRS": types.SimpleNamespace(),
            "thzdaqapi.SRS.LockIn_SR830": fake_lockin_module,
        }

        with patch.dict("sys.modules", modules, clear=False):
            with self.assertRaises(RuntimeError):
                device.initialize()


if __name__ == "__main__":
    unittest.main()
