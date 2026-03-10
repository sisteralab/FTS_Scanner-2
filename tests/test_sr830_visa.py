from __future__ import annotations

import types
import unittest
from unittest.mock import patch

from fts_scanner.devices.sr830_visa import SR830VisaLockIn


class _FakeInstrument:
    def __init__(self) -> None:
        self.timeout = 0
        self.write_termination = ""
        self.read_termination = ""
        self.closed = False
        self.queries: list[str] = []

    def query(self, cmd: str) -> str:
        self.queries.append(cmd)
        if cmd == "*IDN?":
            return "FAKE,SR830,0,1.0"
        if cmd == "OUTP?3":
            return "0.1234"
        return ""

    def close(self) -> None:
        self.closed = True


class _FakeResourceManager:
    def __init__(self, library: str = "") -> None:
        self.library = library
        self.closed = False
        self.last_resource = ""
        self.instrument = _FakeInstrument()

    def open_resource(self, resource: str):  # noqa: ANN001
        self.last_resource = resource
        return self.instrument

    def close(self) -> None:
        self.closed = True


class TestSr830Visa(unittest.TestCase):
    def test_initialize_identify_read_shutdown(self) -> None:
        managers: list[_FakeResourceManager] = []

        def _factory(library: str = "") -> _FakeResourceManager:
            manager = _FakeResourceManager(library)
            managers.append(manager)
            return manager

        fake_pyvisa = types.SimpleNamespace(ResourceManager=_factory)

        device = SR830VisaLockIn(
            resource="TCPIP0::192.168.0.10::5025::SOCKET",
            visa_library="/opt/libvisa.so",
        )

        with patch.dict("sys.modules", {"pyvisa": fake_pyvisa}, clear=False):
            device.initialize()
            self.assertEqual(device.identify(), "FAKE,SR830,0,1.0")
            self.assertAlmostEqual(device.read_signal(), 0.1234, places=6)
            device.shutdown()

        self.assertEqual(len(managers), 1)
        manager = managers[0]
        self.assertEqual(manager.library, "/opt/libvisa.so")
        self.assertEqual(manager.last_resource, "TCPIP0::192.168.0.10::5025::SOCKET")
        self.assertTrue(manager.instrument.closed)
        self.assertTrue(manager.closed)


if __name__ == "__main__":
    unittest.main()
