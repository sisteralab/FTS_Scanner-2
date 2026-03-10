from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SR830VisaLockIn:
    """SR830 lock-in adapter implemented through VISA (Keysight/NI)."""

    resource: str
    visa_library: str | None = None
    timeout_ms: int = 3000
    _resource_manager: Any = None
    _instrument: Any = None

    def initialize(self) -> None:
        """Open VISA session and verify communication."""
        if self._instrument is not None:
            return

        try:
            import pyvisa  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "Cannot import pyvisa. Install with 'uv pip install pyvisa pyvisa-py'."
            ) from exc

        logger.info("Initializing SR830 via VISA resource=%s", self.resource)
        try:
            self._resource_manager = pyvisa.ResourceManager(self.visa_library or "")
            self._instrument = self._resource_manager.open_resource(self.resource)
            self._instrument.timeout = int(self.timeout_ms)
            self._instrument.write_termination = "\n"
            self._instrument.read_termination = "\n"
            _ = self.identify()
        except Exception as exc:  # noqa: BLE001
            self.shutdown()
            raise RuntimeError(f"VISA initialization failed: {exc}") from exc

    def identify(self) -> str:
        """Read lock-in identification string."""
        if self._instrument is None:
            raise RuntimeError("Lock-In is not initialized")
        return str(self._instrument.query("*IDN?")).strip()

    def read_signal(self) -> float:
        """Read R channel value from lock-in."""
        if self._instrument is None:
            raise RuntimeError("Lock-In is not initialized")
        raw = str(self._instrument.query("OUTP?3")).strip()
        return float(raw)

    def shutdown(self) -> None:
        """Close VISA resources."""
        if self._instrument is not None:
            try:
                self._instrument.close()
            except Exception:  # noqa: BLE001
                logger.exception("Failed to close VISA instrument")
            finally:
                self._instrument = None

        if self._resource_manager is not None:
            try:
                self._resource_manager.close()
            except Exception:  # noqa: BLE001
                logger.exception("Failed to close VISA resource manager")
            finally:
                self._resource_manager = None
