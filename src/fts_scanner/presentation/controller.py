from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QTimer, Signal

from fts_scanner.config import AppConfig
from fts_scanner.devices.simulated import SimulatedLockInDevice, SimulatedMotorDevice
from fts_scanner.devices.sr830 import SR830VisaLockIn
from fts_scanner.devices.ximc_motor import XimcMotorDevice
from fts_scanner.domain.models import ScanSettings
from fts_scanner.presentation.measurement_worker import MeasurementWorker
from fts_scanner.store.measure_store import MeasureManager, MeasureModel, MeasureType
from fts_scanner.use_cases.initialize import InitializeHardwareUseCase
from fts_scanner.use_cases.measure_spectrogram import MeasureSpectrogramUseCase
from fts_scanner.use_cases.monitor import ReadSignalUseCase


class MainController(QObject):
    """Coordinates UI actions, device adapters and use-cases."""

    status_changed = Signal(str)
    monitoring_signal = Signal(float)
    measurement_point = Signal(dict)
    measurement_started = Signal()
    measurement_finished = Signal()
    measurement_failed = Signal(str)
    initialized = Signal(bool)

    def __init__(self, config: AppConfig, project_root: Path) -> None:
        super().__init__()
        self._config = config
        self._project_root = project_root

        self._motor = None
        self._lock_in = None
        self._initialize_use_case: InitializeHardwareUseCase | None = None
        self._monitor_use_case: ReadSignalUseCase | None = None
        self._measure_use_case: MeasureSpectrogramUseCase | None = None

        self._monitor_timer = QTimer(self)
        self._monitor_timer.setInterval(200)
        self._monitor_timer.timeout.connect(self._poll_monitor)

        self._thread: QThread | None = None
        self._worker: MeasurementWorker | None = None
        self._current_measure: MeasureModel | None = None

    @property
    def is_measurement_running(self) -> bool:
        """Check whether background measurement thread is active."""
        return self._thread is not None and self._thread.isRunning()

    def initialize_devices(self, use_simulation: bool) -> None:
        """Create device adapters and initialize hardware stack."""
        self.shutdown()

        if use_simulation:
            self._motor = SimulatedMotorDevice()
            self._lock_in = SimulatedLockInDevice()
        else:
            self._motor = XimcMotorDevice(
                ximc_root=self._config.ximc_root if self._config.ximc_root.is_absolute() else self._project_root / self._config.ximc_root,
                motor_name=self._config.motor_name,
            )
            self._lock_in = SR830VisaLockIn(resource_name=self._config.lock_in_resource)

        self._initialize_use_case = InitializeHardwareUseCase(self._motor, self._lock_in)
        self._monitor_use_case = ReadSignalUseCase(self._lock_in)
        self._measure_use_case = MeasureSpectrogramUseCase(self._motor, self._lock_in)

        try:
            report = self._initialize_use_case.execute()
            self.status_changed.emit(
                f"Initialized. Lock-In: {report.lock_in_idn}; Motor pos: {report.motor_position_steps} steps"
            )
            self.initialized.emit(True)
        except Exception as exc:  # noqa: BLE001
            self.status_changed.emit(f"Initialization failed: {exc}")
            self.initialized.emit(False)

    def start_monitoring(self) -> None:
        """Enable periodic lock-in polling."""
        if self._monitor_use_case is None:
            self.status_changed.emit("Monitoring is unavailable: initialize devices first")
            return
        self._monitor_timer.start()
        self.status_changed.emit("Monitoring started")

    def stop_monitoring(self) -> None:
        """Disable periodic lock-in polling."""
        self._monitor_timer.stop()
        self.status_changed.emit("Monitoring stopped")

    def start_measurement(self, settings: ScanSettings) -> None:
        """Start spectrogram measurement in background thread."""
        if self._measure_use_case is None:
            self.status_changed.emit("Measurement is unavailable: initialize devices first")
            return
        if self.is_measurement_running:
            self.status_changed.emit("Measurement is already running")
            return

        self._current_measure = MeasureManager.create(
            measure_type=MeasureType.SPECTROGRAM,
            data={
                "settings": asdict(settings),
                "points": [],
                "meta": {"status": "running"},
            },
        )

        self._thread = QThread(self)
        self._worker = MeasurementWorker(self._measure_use_case, settings)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.point_acquired.connect(self._on_measurement_point)
        self._worker.completed.connect(self._on_measurement_completed)
        self._worker.failed.connect(self._on_measurement_failed)

        self._worker.completed.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._cleanup_thread_objects)

        self.measurement_started.emit()
        self.status_changed.emit("Measurement started")
        self._thread.start()

    def pause_measurement(self) -> None:
        """Pause running measurement."""
        if self._worker is None:
            return
        self._worker.pause()
        self.status_changed.emit("Measurement paused")

    def resume_measurement(self) -> None:
        """Resume paused measurement."""
        if self._worker is None:
            return
        self._worker.resume()
        self.status_changed.emit("Measurement resumed")

    def stop_measurement(self) -> None:
        """Request graceful stop of background measurement."""
        if self._worker is None:
            return
        self._worker.request_stop()
        self.status_changed.emit("Stopping measurement...")

    def shutdown(self) -> None:
        """Stop active tasks and release device connections."""
        self.stop_monitoring()
        if self._worker is not None:
            self._worker.request_stop()
        if self._thread is not None and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)

        if self._motor is not None:
            self._motor.shutdown()
        if self._lock_in is not None:
            self._lock_in.shutdown()

        self._current_measure = None
        self._thread = None
        self._worker = None

    def _poll_monitor(self) -> None:
        if self._monitor_use_case is None:
            return
        try:
            value = self._monitor_use_case.execute()
            self.monitoring_signal.emit(value)
        except Exception as exc:  # noqa: BLE001
            self.status_changed.emit(f"Monitoring error: {exc}")
            self.stop_monitoring()

    def _on_measurement_point(self, point: dict) -> None:
        if self._current_measure is None:
            return

        points = self._current_measure.data.setdefault("points", [])
        if isinstance(points, list):
            points.append(point)

        if len(points) % 10 == 0:
            self._current_measure.save(finish=False)

        self.measurement_point.emit(point)

    def _on_measurement_completed(self) -> None:
        if self._current_measure is not None:
            self._current_measure.data.setdefault("meta", {})["status"] = "completed"
            self._current_measure.save(finish=True)
        self.status_changed.emit("Measurement completed")
        self.measurement_finished.emit()

    def _on_measurement_failed(self, error: str) -> None:
        if self._current_measure is not None:
            self._current_measure.data.setdefault("meta", {})["status"] = "failed"
            self._current_measure.data.setdefault("meta", {})["error"] = error
            self._current_measure.save(finish=True)
        self.status_changed.emit(f"Measurement failed: {error}")
        self.measurement_failed.emit(error)

    def _cleanup_thread_objects(self) -> None:
        self._thread = None
        self._worker = None
        self._thread = None
        self._worker = None
