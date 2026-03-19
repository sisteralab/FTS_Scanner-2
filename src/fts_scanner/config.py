from __future__ import annotations

from configparser import ConfigParser, SectionProxy
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QSettings

from fts_scanner.devices.lockin_types import LockInAdapterType

SETTINGS_GROUP = "connection"


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
    motor_speed: int = 1000
    motor_acceleration: int = 500

    default_wait_ms: int = 400
    default_pos_border_mm: float = 10.0
    default_neg_border_mm: float = 10.0
    default_step_units: int = 10
    default_repeats: int = 1

    settings_organization: str = "ASC"
    settings_application: str = "FTS Scanner"
    settings_file: Path = Path("settings.ini")

    @classmethod
    def from_project_root(cls, project_root: Path) -> "AppConfig":
        """Build config, read native settings and migrate legacy settings.ini if needed."""
        cfg = cls(
            ximc_root=project_root / "ximc",
            settings_file=project_root / "settings.ini",
        )
        cfg.load()
        return cfg

    def load(self) -> None:
        """Load persisted settings from native system store and migrate legacy ini."""
        if self._load_from_native_store():
            return
        if not self.settings_file.exists():
            return
        self._load_from_ini_file()
        self.save()

    def save(self) -> None:
        """Persist settings to native system store."""
        settings = self._native_settings()
        settings.beginGroup(SETTINGS_GROUP)
        settings.setValue("use_simulation", self.use_simulation)
        settings.setValue("lock_in_adapter", self.lock_in_adapter)
        settings.setValue("lock_in_host", self.lock_in_host)
        settings.setValue("lock_in_port", self.lock_in_port)
        settings.setValue("lock_in_usb_port", self.lock_in_usb_port)
        settings.setValue("lock_in_gpib_address", self.lock_in_gpib_address)
        settings.setValue("lock_in_visa_resource", self.lock_in_visa_resource)
        settings.setValue("lock_in_visa_library", self.lock_in_visa_library)
        settings.setValue("motor_name", self.motor_name or "")
        settings.setValue("ximc_root", str(self.ximc_root))
        settings.setValue("motor_speed", self.motor_speed)
        settings.setValue("motor_acceleration", self.motor_acceleration)
        settings.endGroup()
        settings.sync()

    def _load_from_native_store(self) -> bool:
        settings = self._native_settings()
        settings.beginGroup(SETTINGS_GROUP)
        if not settings.childKeys():
            settings.endGroup()
            return False

        self.use_simulation = self._coerce_bool(
            settings.value("use_simulation", self.use_simulation), self.use_simulation
        )
        self.lock_in_adapter = self._coerce_str(
            settings.value("lock_in_adapter", self.lock_in_adapter),
            self.lock_in_adapter,
        )
        self.lock_in_host = self._coerce_str(
            settings.value("lock_in_host", self.lock_in_host),
            self.lock_in_host,
        )
        self.lock_in_port = self._coerce_int(
            settings.value("lock_in_port", self.lock_in_port), self.lock_in_port
        )
        self.lock_in_usb_port = self._coerce_str(
            settings.value("lock_in_usb_port", self.lock_in_usb_port),
            self.lock_in_usb_port,
        )
        self.lock_in_gpib_address = self._coerce_int(
            settings.value("lock_in_gpib_address", self.lock_in_gpib_address),
            self.lock_in_gpib_address,
        )
        self.lock_in_visa_resource = self._coerce_str(
            settings.value("lock_in_visa_resource", self.lock_in_visa_resource),
            self.lock_in_visa_resource,
        )
        self.lock_in_visa_library = self._coerce_str(
            settings.value("lock_in_visa_library", self.lock_in_visa_library),
            self.lock_in_visa_library,
        )

        motor_name = self._coerce_str(
            settings.value("motor_name", self.motor_name or ""),
            self.motor_name or "",
        )
        self.motor_name = motor_name or None
        self.motor_speed = self._coerce_int(
            settings.value("motor_speed", self.motor_speed),
            self.motor_speed,
        )
        self.motor_acceleration = self._coerce_int(
            settings.value("motor_acceleration", self.motor_acceleration),
            self.motor_acceleration,
        )
        ximc_raw = self._coerce_str(
            settings.value("ximc_root", str(self.ximc_root)),
            str(self.ximc_root),
        )
        self.ximc_root = self._resolve_ximc_path(ximc_raw)
        settings.endGroup()
        return True

    def _load_from_ini_file(self) -> None:
        """Load persisted settings from legacy settings.ini."""
        parser = ConfigParser()
        parser.read(self.settings_file, encoding="utf-8")
        section: SectionProxy | dict[str, str] = (
            parser[SETTINGS_GROUP] if parser.has_section(SETTINGS_GROUP) else {}
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
        self.motor_speed = self._get_int(section, "motor_speed", self.motor_speed)
        self.motor_acceleration = self._get_int(
            section, "motor_acceleration", self.motor_acceleration
        )

        ximc_raw = section.get("ximc_root", str(self.ximc_root))
        self.ximc_root = self._resolve_ximc_path(ximc_raw)

    def save_to_ini(self) -> None:
        """Persist settings to legacy settings.ini (compatibility helper)."""
        parser = ConfigParser()
        parser[SETTINGS_GROUP] = {
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
            "motor_speed": str(self.motor_speed),
            "motor_acceleration": str(self.motor_acceleration),
        }
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        with self.settings_file.open("w", encoding="utf-8") as fh:
            parser.write(fh)

    def _native_settings(self) -> QSettings:
        return QSettings(
            QSettings.Format.NativeFormat,
            QSettings.Scope.UserScope,
            self.settings_organization,
            self.settings_application,
        )

    def _resolve_ximc_path(self, raw_value: str) -> Path:
        parsed_ximc = Path(raw_value).expanduser()
        if parsed_ximc.is_absolute():
            return parsed_ximc
        return self.settings_file.parent / parsed_ximc

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

    @staticmethod
    def _coerce_int(value: object, default: int) -> int:
        if value is None:
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _coerce_str(value: object, default: str) -> str:
        if value is None:
            return default
        return str(value)

    @staticmethod
    def _coerce_bool(value: object, default: bool) -> bool:
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}
