from __future__ import annotations

from configparser import ConfigParser, SectionProxy
from dataclasses import dataclass
from pathlib import Path

from fts_scanner.devices.lockin_types import LockInAdapterType


@dataclass(slots=True)
class AppConfig:
    """Runtime configuration for hardware backends and defaults."""

    use_simulation: bool = False

    lock_in_adapter: str = LockInAdapterType.PROLOGIX_ETHERNET
    lock_in_host: str = "169.254.156.103"
    lock_in_port: int = 1234
    lock_in_usb_port: str = "/dev/tty.usbserial"
    lock_in_gpib_address: int = 8
    lock_in_visa_resource: str = "GPIB1::8::INSTR"
    lock_in_visa_library: str = ""

    motor_name: str | None = "xi-com:\\\\.\\COM4"
    ximc_root: Path = Path("ximc")

    default_wait_ms: int = 400
    default_pos_border_mm: float = 10.0
    default_neg_border_mm: float = 10.0
    default_step_units: int = 10
    default_repeats: int = 1

    settings_file: Path = Path("settings.ini")

    @classmethod
    def from_project_root(cls, project_root: Path) -> "AppConfig":
        """Build config and load persisted settings from project root."""
        cfg = cls(
            ximc_root=project_root / "ximc",
            settings_file=project_root / "settings.ini",
        )
        cfg.load_from_ini()
        return cfg

    def load_from_ini(self) -> None:
        """Load persisted settings from settings.ini if it exists."""
        if not self.settings_file.exists():
            return

        parser = ConfigParser()
        parser.read(self.settings_file, encoding="utf-8")
        section: SectionProxy | dict[str, str] = (
            parser["connection"] if parser.has_section("connection") else {}
        )

        self.use_simulation = self._get_bool(section, "use_simulation", self.use_simulation)
        self.lock_in_adapter = section.get("lock_in_adapter", self.lock_in_adapter)
        self.lock_in_host = section.get("lock_in_host", self.lock_in_host)
        self.lock_in_port = self._get_int(section, "lock_in_port", self.lock_in_port)
        self.lock_in_usb_port = section.get("lock_in_usb_port", self.lock_in_usb_port)
        self.lock_in_gpib_address = self._get_int(
            section, "lock_in_gpib_address", self.lock_in_gpib_address
        )
        self.lock_in_visa_resource = section.get("lock_in_visa_resource", self.lock_in_visa_resource)
        self.lock_in_visa_library = section.get("lock_in_visa_library", self.lock_in_visa_library)

        motor_name = section.get("motor_name", self.motor_name or "")
        self.motor_name = motor_name or None

        ximc_raw = section.get("ximc_root", str(self.ximc_root))
        parsed_ximc = Path(ximc_raw).expanduser()
        self.ximc_root = (
            parsed_ximc
            if parsed_ximc.is_absolute()
            else (self.settings_file.parent / parsed_ximc)
        )

    def save_to_ini(self) -> None:
        """Persist settings to settings.ini."""
        parser = ConfigParser()
        parser["connection"] = {
            "use_simulation": str(self.use_simulation),
            "lock_in_adapter": self.lock_in_adapter,
            "lock_in_host": self.lock_in_host,
            "lock_in_port": str(self.lock_in_port),
            "lock_in_usb_port": self.lock_in_usb_port,
            "lock_in_gpib_address": str(self.lock_in_gpib_address),
            "lock_in_visa_resource": self.lock_in_visa_resource,
            "lock_in_visa_library": self.lock_in_visa_library,
            "motor_name": self.motor_name or "",
            "ximc_root": str(self.ximc_root),
        }
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        with self.settings_file.open("w", encoding="utf-8") as fh:
            parser.write(fh)

    @staticmethod
    def _get_int(section: SectionProxy | dict[str, str], key: str, default: int) -> int:
        value = section.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _get_bool(section: SectionProxy | dict[str, str], key: str, default: bool) -> bool:
        value = section.get(key)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}
