from __future__ import annotations

import logging
from dataclasses import asdict

from PySide6.QtCore import QObject, Signal, Slot

from fts_scanner.domain.models import ScanSettings
from fts_scanner.use_cases.measure_spectrogram import MeasureSpectrogramUseCase

logger = logging.getLogger(__name__)


class MeasurementWorker(QObject):
    """Background worker that runs scan use-case in a QThread."""

    point_acquired = Signal(dict)
    completed = Signal()
    failed = Signal(str)

    def __init__(self, use_case: MeasureSpectrogramUseCase, settings: ScanSettings) -> None:
        super().__init__()
        self._use_case = use_case
        self._settings = settings
        self._is_stopped = False
        self._is_paused = False

    @Slot()
    def run(self) -> None:
        """Execute measurement loop and emit stream of points."""
        try:
            logger.info("Measurement worker started")
            for point in self._use_case.execute(
                settings=self._settings,
                should_stop=self._should_stop,
                should_pause=self._should_pause,
            ):
                self.point_acquired.emit(asdict(point))
            logger.info("Measurement worker completed")
            self.completed.emit()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Measurement worker failed")
            self.failed.emit(str(exc))

    def request_stop(self) -> None:
        """Request graceful stop."""
        self._is_stopped = True

    def pause(self) -> None:
        """Pause measurement."""
        self._is_paused = True

    def resume(self) -> None:
        """Resume paused measurement."""
        self._is_paused = False

    def _should_stop(self) -> bool:
        return self._is_stopped

    def _should_pause(self) -> bool:
        return self._is_paused
