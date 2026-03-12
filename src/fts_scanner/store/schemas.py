from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

import numpy as np

from fts_scanner.domain.models import STAGE_STEP_UM


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
    if hasattr(value, "tolist") and callable(value.tolist):  # numpy array-like fallback
        try:
            return to_json_compatible(value.tolist())
        except Exception:  # noqa: BLE001
            pass
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


def enrich_measure_data_for_export(data: dict[str, Any]) -> dict[str, Any]:
    """Add quick-plot arrays to normalized measurement data."""
    normalized = normalize_measure_data(measure_type=str(data.get("type", "")), data=data)
    points = normalized.get("points", [])
    settings = normalized.get("settings", {})

    quicklook = _build_quicklook(points=points, settings=settings)
    normalized["quicklook"] = quicklook
    return normalized


def _build_quicklook(points: Any, settings: Any) -> dict[str, Any]:
    if not isinstance(points, list):
        return {
            "points_steps": [],
            "raw_signal": [],
            "frequency_thz": [],
            "spectrum": [],
            "spectrum_raw": [],
            "source_repeat": 0,
        }

    by_repeat: dict[int, list[tuple[int, float]]] = {}
    all_positions: list[int] = []
    all_signals: list[float] = []

    for point in points:
        if not isinstance(point, dict):
            continue
        position_raw = point.get("position_steps")
        signal_raw = point.get("signal")
        repeat_raw = point.get("repeat", 0)

        try:
            position = int(position_raw)
            signal = float(signal_raw)
            repeat = int(repeat_raw)
        except (TypeError, ValueError):
            continue

        all_positions.append(position)
        all_signals.append(signal)
        by_repeat.setdefault(repeat, []).append((position, signal))

    if by_repeat:
        source_repeat = max(by_repeat.keys())
        repeat_points = by_repeat[source_repeat]
    else:
        source_repeat = 0
        repeat_points = []

    positions = [item[0] for item in repeat_points]
    raw_signal = [item[1] for item in repeat_points]
    frequency_thz, spectrum, spectrum_raw = _compute_spectrum(raw_signal=raw_signal, settings=settings)

    return {
        "points_steps": positions,
        "raw_signal": raw_signal,
        "frequency_thz": frequency_thz,
        "spectrum": spectrum,
        "spectrum_raw": spectrum_raw,
        "source_repeat": source_repeat,
        "all_points_steps": all_positions,
        "all_raw_signal": all_signals,
    }


def _compute_spectrum(raw_signal: list[float], settings: Any) -> tuple[list[float], list[float], list[float]]:
    if len(raw_signal) < 8:
        return [], [], []

    step_units = 0
    if isinstance(settings, dict):
        try:
            step_units = int(settings.get("step_units", 0))
        except (TypeError, ValueError):
            step_units = 0
    if step_units <= 0:
        return [], [], []

    # Michelson geometry: optical path difference is 2x mirror travel.
    sample_spacing_um = step_units * STAGE_STEP_UM * 2.0
    signal_np = np.asarray(raw_signal, dtype=float)
    if signal_np.size < 8:
        return [], [], []

    signal_np = signal_np - signal_np.mean()
    window = np.hanning(signal_np.size)
    spectrum_np = np.fft.rfft(signal_np * window)
    magnitude_raw_np = np.abs(spectrum_np)
    magnitude_np = np.sqrt(np.clip(magnitude_raw_np, 0.0, None))
    freq_per_um = np.fft.rfftfreq(signal_np.size, d=sample_spacing_um)
    freq_thz = freq_per_um * 299.792458

    return freq_thz.tolist(), magnitude_np.tolist(), magnitude_raw_np.tolist()
