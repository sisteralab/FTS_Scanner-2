from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


STAGE_STEP_UM = 2.5


@dataclass(slots=True)
class ScanSettings:
    """User-defined parameters for one spectrogram scan."""

    wait_time_ms: int
    positive_border_mm: float
    negative_border_mm: float
    step_units: int
    repeats: int = 1

    @property
    def start_steps(self) -> int:
        """Absolute start position in steps (negative border)."""
        return -round(self.negative_border_mm * 1000.0 / STAGE_STEP_UM)

    @property
    def total_span_steps(self) -> int:
        """Full scan distance in stage steps."""
        return round((self.positive_border_mm + self.negative_border_mm) * 1000.0 / STAGE_STEP_UM)

    @property
    def point_count(self) -> int:
        """How many points are collected in one pass."""
        return self.total_span_steps // self.step_units + 1

    @property
    def resolution_thz(self) -> float:
        """Rough spectral resolution estimate from legacy formula."""
        return round(30.0 / self.step_units, 2)


@dataclass(slots=True)
class SpectrumPoint:
    """One measured sample of spectrogram scan."""

    index: int
    repeat: int
    position_steps: int
    signal: float
    timestamp: datetime = field(default_factory=datetime.now)
