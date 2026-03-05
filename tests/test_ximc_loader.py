from __future__ import annotations

import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from fts_scanner.devices.ximc_motor import XimcMotorDevice


class TestXimcLoader(unittest.TestCase):
    def test_import_pyximc_raises_when_wrapper_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "ximc"
            with self.assertRaises(RuntimeError):
                XimcMotorDevice._import_pyximc(root)

    def test_import_pyximc_success_with_mocked_module(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "ximc"
            wrapper = root / "crossplatform" / "wrappers" / "python"
            wrapper.mkdir(parents=True, exist_ok=True)

            fake_module = types.SimpleNamespace(lib=object())
            start_len = len(sys.path)

            with patch.dict(sys.modules, {"pyximc": fake_module}, clear=False):
                with patch("platform.system", return_value="Linux"):
                    pyximc, lib = XimcMotorDevice._import_pyximc(root)

            self.assertIs(pyximc, fake_module)
            self.assertIs(lib, fake_module.lib)
            self.assertGreaterEqual(len(sys.path), start_len)
            self.assertIn(str(wrapper.resolve()), sys.path)


if __name__ == "__main__":
    unittest.main()
