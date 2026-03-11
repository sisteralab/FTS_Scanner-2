from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime, time
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class MeasurePayload:
    """Serializable representation of a stored measurement."""

    id: int
    comment: str
    type: str
    measure: str
    started: datetime
    finished: datetime
    data: dict[str, Any]

    def to_json(self) -> dict[str, Any]:
        """Convert payload to JSON-compatible dictionary."""
        payload = asdict(self)
        payload["started"] = self.started.isoformat()
        payload["finished"] = self.finished.isoformat()
        return to_json_compatible(payload)


def to_json_compatible(value: Any) -> Any:
    """Recursively convert value into JSON-serializable representation."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return to_json_compatible(asdict(value))
    if isinstance(value, dict):
        return {str(key): to_json_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_json_compatible(item) for item in value]
    if hasattr(value, "item") and callable(value.item):  # numpy-like scalar fallback
        try:
            return to_json_compatible(value.item())
        except Exception:  # noqa: BLE001
            pass
    return str(value)


def normalize_measure_data(measure_type: str, data: Any) -> dict[str, Any]:
    """Normalize raw measurement data to stable JSON schema."""
    if not isinstance(data, dict):
        return {"type": measure_type, "settings": {}, "points": []}

    points = data.get("points", [])
    if not isinstance(points, list):
        points = []

    return {
        "type": measure_type,
        "settings": to_json_compatible(data.get("settings", {})),
        "points": to_json_compatible(points),
        "meta": to_json_compatible(data.get("meta", {})),
    }
