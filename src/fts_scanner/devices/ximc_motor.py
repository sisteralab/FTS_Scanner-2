from __future__ import annotations

import logging
import os
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fts_scanner.devices.interfaces import MotorMotionStatus

logger = logging.getLogger(__name__)


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
        logger.info("Initializing XIMC motor from: %s", self.ximc_root)
        self._pyximc, self._lib = self._import_pyximc(self.ximc_root)
        self._device_id = self._open_device(self.motor_name)
        # Validation read to fail fast on invalid/opened-but-unusable handles.
        _ = self.get_position()

    def move_to(self, steps: int) -> None:
        """Move to absolute position in steps."""
        self._ensure_open()
        result = self._lib.command_move(self._device_id, int(steps), 0)
        self._expect_ok(result, "command_move")

    def move_by(self, delta_steps: int) -> None:
        """Move by relative amount in steps."""
        self._ensure_open()
        result = self._lib.command_movr(self._device_id, int(delta_steps), 0)
        self._expect_ok(result, "command_movr")

    def wait_for_stop(self, timeout_ms: int) -> None:
        """Wait until motor stops or timeout expires."""
        self._ensure_open()
        result = self._lib.command_wait_for_stop(self._device_id, int(timeout_ms))
        self._expect_ok(result, "command_wait_for_stop")

    def get_position(self) -> int:
        """Read current stage position in steps."""
        self._ensure_open()
        position = self._pyximc.get_position_t()
        result = self._lib.get_position(self._device_id, self._pyximc.byref(position))
        self._expect_ok(result, "get_position")
        return int(position.Position)

    def set_zero(self) -> None:
        """Set current hardware position as logical zero."""
        self._ensure_open()
        result = self._lib.command_zero(self._device_id)
        self._expect_ok(result, "command_zero")

    def stop(self) -> None:
        """Stop movement immediately."""
        self._ensure_open()
        result = self._lib.command_stop(self._device_id)
        self._expect_ok(result, "command_stop")

    def start_jog(self, direction: int) -> None:
        """Start continuous move: `-1` to left, `+1` to right."""
        self._ensure_open()
        if direction == 0:
            return
        if direction > 0:
            result = self._lib.command_right(self._device_id)
            self._expect_ok(result, "command_right")
            return
        result = self._lib.command_left(self._device_id)
        self._expect_ok(result, "command_left")

    def get_motion_params(self) -> tuple[int, int]:
        """Read current speed and acceleration from controller."""
        self._ensure_open()
        move_settings = self._pyximc.move_settings_t()
        result = self._lib.get_move_settings(self._device_id, self._pyximc.byref(move_settings))
        self._expect_ok(result, "get_move_settings")
        return int(move_settings.Speed), int(move_settings.Accel)

    def set_motion_params(self, speed: int, acceleration: int) -> None:
        """Set speed and acceleration (deceleration follows acceleration)."""
        self._ensure_open()
        move_settings = self._pyximc.move_settings_t()
        read_result = self._lib.get_move_settings(self._device_id, self._pyximc.byref(move_settings))
        self._expect_ok(read_result, "get_move_settings")

        safe_speed = max(1, int(speed))
        safe_accel = max(1, int(acceleration))
        move_settings.Speed = safe_speed
        move_settings.Accel = safe_accel
        if hasattr(move_settings, "Decel"):
            move_settings.Decel = safe_accel

        write_result = self._lib.set_move_settings(self._device_id, self._pyximc.byref(move_settings))
        self._expect_ok(write_result, "set_move_settings")

    def get_motion_status(self) -> MotorMotionStatus:
        """Read active move command status from controller."""
        self._ensure_open()
        status = self._pyximc.status_t()
        result = self._lib.get_status(self._device_id, self._pyximc.byref(status))
        self._expect_ok(result, "get_status")

        mv_cmd_sts = int(status.MvCmdSts)
        running_flag = int(getattr(self._pyximc.MvcmdStatus, "MVCMD_RUNNING", 0x80))
        error_flag = int(getattr(self._pyximc.MvcmdStatus, "MVCMD_ERROR", 0x40))
        name_mask = int(getattr(self._pyximc.MvcmdStatus, "MVCMD_NAME_BITS", 0x3F))
        command_code = mv_cmd_sts & name_mask
        command = self._command_name(command_code)
        return MotorMotionStatus(
            is_moving=bool(mv_cmd_sts & running_flag),
            has_error=bool(mv_cmd_sts & error_flag),
            command=command,
            command_code=command_code,
        )

    def shutdown(self) -> None:
        """Close device and clear loaded handles."""
        if self._device_id is None or self._pyximc is None:
            return
        logger.info("Closing XIMC motor device")
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

        logger.info("Opening XIMC device: %s", open_name)
        return self._lib.open_device(open_name)

    def _ensure_open(self) -> None:
        if self._device_id is None:
            raise RuntimeError("XIMC motor is not initialized")

    def _expect_ok(self, result: int, operation: str) -> None:
        ok_code = int(getattr(self._pyximc.Result, "Ok", 0))
        if int(result) != ok_code:
            message = f"XIMC {operation} failed with code={result}"
            logger.error(message)
            raise RuntimeError(message)

    def _command_name(self, command_code: int) -> str:
        mv = self._pyximc.MvcmdStatus
        mapping = {
            int(getattr(mv, "MVCMD_MOVE", 0x01)): "move_to",
            int(getattr(mv, "MVCMD_MOVR", 0x02)): "move_by",
            int(getattr(mv, "MVCMD_LEFT", 0x03)): "left",
            int(getattr(mv, "MVCMD_RIGHT", 0x04)): "right",
            int(getattr(mv, "MVCMD_STOP", 0x05)): "stop",
            int(getattr(mv, "MVCMD_HOME", 0x06)): "home",
            int(getattr(mv, "MVCMD_LOFT", 0x07)): "loft",
            int(getattr(mv, "MVCMD_SSTP", 0x08)): "soft_stop",
            int(getattr(mv, "MVCMD_UKNWN", 0x00)): "idle",
        }
        return mapping.get(int(command_code), f"cmd_{int(command_code)}")

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
