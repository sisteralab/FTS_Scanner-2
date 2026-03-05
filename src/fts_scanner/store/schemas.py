from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
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
        return payload


def normalize_measure_data(measure_type: str, data: Any) -> dict[str, Any]:
    """Normalize raw measurement data to stable JSON schema."""
    if not isinstance(data, dict):
        return {"type": measure_type, "settings": {}, "points": []}

    points = data.get("points", [])
    if not isinstance(points, list):
        points = []

    return {
        "type": measure_type,
        "settings": data.get("settings", {}),
        "points": points,
        "meta": data.get("meta", {}),
    }
