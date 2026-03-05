from __future__ import annotations

from dataclasses import dataclass

import pyvisa


@dataclass(slots=True)
class SR830VisaLockIn:
    """SR830 adapter over VISA backend."""

    resource_name: str
    _resource_manager: pyvisa.ResourceManager | None = None
    _resource: pyvisa.resources.MessageBasedResource | None = None

    def initialize(self) -> None:
        """Open VISA session for SR830."""
        self._resource_manager = pyvisa.ResourceManager()
        self._resource = self._resource_manager.open_resource(
            self.resource_name,
            write_termination="\n",
            read_termination="\n",
        )

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
            self._resource.close()
            self._resource = None
        if self._resource_manager is not None:
            self._resource_manager.close()
            self._resource_manager = None
