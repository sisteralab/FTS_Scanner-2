from __future__ import annotations

import os
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class XimcMotorDevice:
    """Standa XIMC motor adapter built on vendor pyximc wrapper."""

    ximc_root: Path
    motor_name: str | None = None
    _pyximc: Any = None
    _lib: Any = None
    _device_id: Any = None

    def initialize(self) -> None:
        """Load pyximc wrapper and open motor device."""
        if self._device_id is not None:
            return
        self._pyximc, self._lib = self._import_pyximc(self.ximc_root)
        self._device_id = self._open_device(self.motor_name)

    def move_to(self, steps: int) -> None:
        """Move to absolute position in steps."""
        self._ensure_open()
        self._lib.command_move(self._device_id, int(steps), 0)

    def move_by(self, delta_steps: int) -> None:
        """Move by relative amount in steps."""
        self._ensure_open()
        self._lib.command_movr(self._device_id, int(delta_steps), 0)

    def wait_for_stop(self, timeout_ms: int) -> None:
        """Wait until motor stops or timeout expires."""
        self._ensure_open()
        self._lib.command_wait_for_stop(self._device_id, int(timeout_ms))

    def get_position(self) -> int:
        """Read current stage position in steps."""
        self._ensure_open()
        position = self._pyximc.get_position_t()
        self._lib.get_position(self._device_id, self._pyximc.byref(position))
        return int(position.Position)

    def stop(self) -> None:
        """Stop movement immediately."""
        self._ensure_open()
        self._lib.command_stop(self._device_id)

    def shutdown(self) -> None:
        """Close device and clear loaded handles."""
        if self._device_id is None or self._pyximc is None:
            return
        self._lib.close_device(self._pyximc.byref(self._pyximc.cast(self._device_id, self._pyximc.POINTER(self._pyximc.c_int))))
        self._device_id = None

    def _open_device(self, name: str | None) -> Any:
        devenum = self._lib.enumerate_devices(self._pyximc.EnumerateFlags.ENUMERATE_PROBE, None)
        dev_count = self._lib.get_device_count(devenum)
        if name is None and dev_count == 0:
            raise RuntimeError("XIMC device is not found")

        open_name: bytes
        if name is not None:
            open_name = name.encode() if isinstance(name, str) else name
        else:
            open_name = self._lib.get_device_name(devenum, 0)

        return self._lib.open_device(open_name)

    def _ensure_open(self) -> None:
        if self._device_id is None:
            raise RuntimeError("XIMC motor is not initialized")

    @staticmethod
    def _import_pyximc(ximc_root: Path) -> tuple[Any, Any]:
        wrapper_dir = ximc_root / "crossplatform" / "wrappers" / "python"
        if not wrapper_dir.exists():
            raise RuntimeError(f"XIMC wrapper not found: {wrapper_dir}")

        wrapper_path = str(wrapper_dir.resolve())
        if wrapper_path not in sys.path:
            sys.path.append(wrapper_path)

        if platform.system() == "Windows":
            arch_dir = "win64" if "64" in platform.architecture()[0] else "win32"
            dll_dir = ximc_root / arch_dir
            if hasattr(os, "add_dll_directory") and dll_dir.exists():
                os.add_dll_directory(str(dll_dir.resolve()))
            else:
                os.environ["Path"] = f"{dll_dir};{os.environ.get('Path', '')}"

        try:
            import pyximc  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Cannot import pyximc from {wrapper_dir}: {exc}") from exc

        return pyximc, pyximc.lib
