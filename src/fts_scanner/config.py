from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AppConfig:
    """Runtime configuration for hardware backends and defaults."""

    lock_in_adapter: str = "prologix_ethernet"
    lock_in_resource: str = "GPIB1::8::INSTR"
    lock_in_host: str = "169.254.156.103"
    lock_in_port: int = 1234
    lock_in_usb_port: str = "/dev/tty.usbserial"
    lock_in_gpib_address: int = 8
    thzdaqapi_src: Path = Path.home() / "Labs/scripts/thzdaqapi/src"
    motor_name: str | None = "xi-com:\\\\.\\COM4"
    ximc_root: Path = Path("ximc")
    default_wait_ms: int = 400
    default_pos_border_mm: float = 10.0
    default_neg_border_mm: float = 10.0
    default_step_units: int = 10
    default_repeats: int = 1

    @classmethod
    def from_project_root(cls, project_root: Path) -> "AppConfig":
        """Build config with paths anchored to current project."""
        return cls(ximc_root=project_root / "ximc")
