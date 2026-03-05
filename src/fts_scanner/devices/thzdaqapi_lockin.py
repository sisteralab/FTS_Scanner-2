from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class LockInAdapterType:
    """Supported lock-in adapter backends via thzdaqapi."""

    PROLOGIX_ETHERNET = "prologix_ethernet"
    PROLOGIX_USB = "prologix_usb"


@dataclass(slots=True)
class SR830ThzdaqapiLockIn:
    """SR830 adapter implemented via thzdaqapi Prologix transports."""

    adapter_type: str
    gpib_address: int
    host: str = "169.254.156.103"
    ethernet_port: int = 1234
    usb_port: str = "/dev/tty.usbserial"
    thzdaqapi_src: Path | None = None
    _lockin: Any = None

    def initialize(self) -> None:
        """Initialize thzdaqapi lock-in instance and verify communication."""
        if self._lockin is not None:
            return

        self._ensure_thzdaqapi_import_path()

        try:
            from thzdaqapi import settings as thz_settings
            from thzdaqapi.SRS.LockIn_SR830 import LockIn
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "Cannot import thzdaqapi. Install it with 'uv pip install thzdaqapi' "
                "or from local repo 'uv pip install -e ~/Labs/scripts/thzdaqapi'."
            ) from exc

        logger.info(
            "Initializing SR830 via thzdaqapi adapter=%s gpib=%s host=%s",
            self.adapter_type,
            self.gpib_address,
            self.host,
        )

        if self.adapter_type == LockInAdapterType.PROLOGIX_ETHERNET:
            self._lockin = LockIn(
                host=self.host,
                gpib=self.gpib_address,
                adapter=thz_settings.PROLOGIX_ETHERNET,
                port=self.ethernet_port,
            )
        elif self.adapter_type == LockInAdapterType.PROLOGIX_USB:
            self._lockin = LockIn(
                host="",
                gpib=self.gpib_address,
                adapter=thz_settings.PROLOGIX_USB,
                port=self.usb_port,
            )
        else:
            raise RuntimeError(f"Unsupported lock-in adapter type: {self.adapter_type}")

        # Connectivity check.
        self._lockin.idn()

    def identify(self) -> str:
        """Read lock-in identification string."""
        if self._lockin is None:
            raise RuntimeError("Lock-In is not initialized")
        return str(self._lockin.idn()).strip()

    def read_signal(self) -> float:
        """Read R channel value from lock-in."""
        if self._lockin is None:
            raise RuntimeError("Lock-In is not initialized")
        return float(self._lockin.get_out3())

    def shutdown(self) -> None:
        """Close underlying adapter connection if available."""
        if self._lockin is None:
            return
        adapter = getattr(self._lockin, "adapter", None)
        if adapter is not None and hasattr(adapter, "close"):
            try:
                adapter.close()
            except Exception:  # noqa: BLE001
                logger.exception("Failed to close thzdaqapi adapter")
        self._lockin = None

    def _ensure_thzdaqapi_import_path(self) -> None:
        if self.thzdaqapi_src is None:
            return
        path = str(self.thzdaqapi_src.expanduser().resolve())
        if path not in sys.path:
            sys.path.append(path)
