from __future__ import annotations

import logging
from dataclasses import dataclass

import pyvisa

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SR830VisaLockIn:
    """SR830 adapter over VISA backend."""

    resource_name: str
    _resource_manager: pyvisa.ResourceManager | None = None
    _resource: pyvisa.resources.MessageBasedResource | None = None

    def initialize(self) -> None:
        """Open VISA session for SR830."""
        logger.info("Initializing SR830 over VISA resource: %s", self.resource_name)
        try:
            self._resource_manager = pyvisa.ResourceManager()
            self._resource = self._resource_manager.open_resource(
                self.resource_name,
                write_termination="\n",
                read_termination="\n",
            )
        except Exception as exc:  # noqa: BLE001
            message = self._format_initialize_error(exc)
            logger.exception("Failed to initialize SR830: %s", message)
            raise RuntimeError(message) from exc

    def identify(self) -> str:
        """Read lock-in *IDN? response."""
        if self._resource is None:
            raise RuntimeError("SR830 is not initialized")
        return self._resource.query("*IDN?").strip()

    def read_signal(self) -> float:
        """Read R channel amplitude for scan point."""
        if self._resource is None:
            raise RuntimeError("SR830 is not initialized")
        return float(self._resource.query("OUTP? 3"))

    def shutdown(self) -> None:
        """Close VISA handles."""
        if self._resource is not None:
            logger.info("Closing SR830 VISA resource")
            self._resource.close()
            self._resource = None
        if self._resource_manager is not None:
            logger.info("Closing VISA resource manager")
            self._resource_manager.close()
            self._resource_manager = None

    @staticmethod
    def _format_initialize_error(exc: Exception) -> str:
        """Build user-facing error text for VISA initialization failures."""
        if isinstance(exc, pyvisa.errors.VisaIOError):
            if exc.error_code == pyvisa.constants.StatusCode.error_library_not_found:
                return (
                    "VISA backend library is not found (VI_ERROR_LIBRARY_NOT_FOUND). "
                    "Install NI-VISA/Keysight VISA or use Simulation mode."
                )
            return f"VISA IO error: {exc}"
        return f"Unexpected VISA initialization error: {exc}"
