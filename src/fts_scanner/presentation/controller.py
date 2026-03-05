from __future__ import annotations

import logging
from dataclasses import asdict
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QTimer, Signal

from fts_scanner.config import AppConfig
from fts_scanner.devices.simulated import SimulatedLockInDevice, SimulatedMotorDevice
from fts_scanner.devices.sr830 import SR830VisaLockIn
from fts_scanner.devices.thzdaqapi_lockin import LockInAdapterType, SR830ThzdaqapiLockIn
from fts_scanner.devices.ximc_motor import XimcMotorDevice
from fts_scanner.domain.models import ScanSettings
from fts_scanner.presentation.measurement_worker import MeasurementWorker
from fts_scanner.store.measure_store import MeasureManager, MeasureModel, MeasureType
from fts_scanner.use_cases.measure_spectrogram import MeasureSpectrogramUseCase
from fts_scanner.use_cases.monitor import ReadSignalUseCase

logger = logging.getLogger(__name__)


class MainController(QObject):
    """Coordinates UI actions, device adapters and use-cases."""

    status_changed = Signal(str)
    setup_status = Signal(bool, bool, str)
    monitoring_signal = Signal(float)
    motor_position_signal = Signal(int)
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
        self._monitor_use_case: ReadSignalUseCase | None = None
        self._measure_use_case: MeasureSpectrogramUseCase | None = None

        self._motor_ready = False
        self._lock_in_ready = False

        self._monitor_timer = QTimer(self)
        self._monitor_timer.setInterval(200)
        self._monitor_timer.timeout.connect(self._poll_monitor)

        self._motor_timer = QTimer(self)
        self._motor_timer.setInterval(200)
        self._motor_timer.timeout.connect(self._poll_motor_position)

        self._thread: QThread | None = None
        self._worker: MeasurementWorker | None = None
        self._current_measure: MeasureModel | None = None
        self._last_error: str | None = None

    @property
    def is_measurement_running(self) -> bool:
        """Check whether background measurement thread is active."""
        return self._thread is not None and self._thread.isRunning()

    @property
    def last_error(self) -> str | None:
        """Return latest handled controller error."""
        return self._last_error

    @property
    def config(self) -> AppConfig:
        """Expose mutable runtime config for UI defaults."""
        return self._config

    def initialize_devices(
        self,
        use_simulation: bool,
        lock_in_adapter: str | None = None,
        lock_in_host: str | None = None,
        lock_in_port: int | None = None,
        lock_in_usb_port: str | None = None,
        lock_in_gpib_address: int | None = None,
        thzdaqapi_src: str | None = None,
        lock_in_resource: str | None = None,
        motor_name: str | None = None,
        ximc_root: str | None = None,
    ) -> None:
        """Create device adapters and initialize hardware stack."""
        logger.info("Initialize devices requested. simulation=%s", use_simulation)
        self.shutdown()
        self._last_error = None

        if lock_in_resource is not None:
            self._config.lock_in_resource = lock_in_resource.strip()
        if lock_in_adapter is not None:
            self._config.lock_in_adapter = lock_in_adapter
        if lock_in_host is not None:
            self._config.lock_in_host = lock_in_host.strip()
        if lock_in_port is not None:
            self._config.lock_in_port = int(lock_in_port)
        if lock_in_usb_port is not None:
            self._config.lock_in_usb_port = lock_in_usb_port.strip()
        if lock_in_gpib_address is not None:
            self._config.lock_in_gpib_address = int(lock_in_gpib_address)
        if thzdaqapi_src is not None and thzdaqapi_src.strip():
            self._config.thzdaqapi_src = Path(thzdaqapi_src.strip())
        if motor_name is not None:
            self._config.motor_name = motor_name.strip() or None
        if ximc_root is not None and ximc_root.strip():
            self._config.ximc_root = Path(ximc_root.strip())

        if use_simulation:
            self._motor = SimulatedMotorDevice()
            self._lock_in = SimulatedLockInDevice()
        else:
            resolved_ximc = (
                self._config.ximc_root
                if self._config.ximc_root.is_absolute()
                else self._project_root / self._config.ximc_root
            )
            self._motor = XimcMotorDevice(
                ximc_root=resolved_ximc,
                motor_name=self._config.motor_name,
            )
            if self._config.lock_in_adapter in (
                LockInAdapterType.PROLOGIX_ETHERNET,
                LockInAdapterType.PROLOGIX_USB,
            ):
                self._lock_in = SR830ThzdaqapiLockIn(
                    adapter_type=self._config.lock_in_adapter,
                    gpib_address=self._config.lock_in_gpib_address,
                    host=self._config.lock_in_host,
                    ethernet_port=self._config.lock_in_port,
                    usb_port=self._config.lock_in_usb_port,
                    thzdaqapi_src=self._config.thzdaqapi_src,
                )
            else:
                self._lock_in = SR830VisaLockIn(resource_name=self._config.lock_in_resource)

        motor_message = "Motor not initialized"
        lockin_message = "Lock-In not initialized"

        try:
            self._motor.initialize()
            self._motor_ready = True
            pos = self._motor.get_position()
            self.motor_position_signal.emit(pos)
            motor_message = f"Motor connected at position {pos} steps"
        except Exception as exc:  # noqa: BLE001
            self._motor_ready = False
            self._last_error = str(exc)
            motor_message = f"Motor init failed: {exc}"
            logger.exception("Motor initialization failed")

        try:
            self._lock_in.initialize()
            lock_in_idn = self._lock_in.identify()
            self._lock_in_ready = True
            lockin_message = f"Lock-In connected: {lock_in_idn}"
        except Exception as exc:  # noqa: BLE001
            self._lock_in_ready = False
            self._last_error = str(exc)
            lockin_message = f"Lock-In init failed: {exc}"
            logger.exception("Lock-In initialization failed")

        self._monitor_use_case = ReadSignalUseCase(self._lock_in) if self._lock_in_ready else None
        self._measure_use_case = (
            MeasureSpectrogramUseCase(self._motor, self._lock_in)
            if self._motor_ready and self._lock_in_ready
            else None
        )

        message = f"{motor_message}; {lockin_message}"
        ok = self._motor_ready and self._lock_in_ready
        self.setup_status.emit(self._motor_ready, self._lock_in_ready, message)
        self.status_changed.emit(message)
        self.initialized.emit(ok)
        logger.info("Setup result. motor_ok=%s lockin_ok=%s", self._motor_ready, self._lock_in_ready)

    def start_monitoring(self) -> None:
        """Enable periodic lock-in and motor polling."""
        if not self._motor_ready and not self._lock_in_ready:
            self.status_changed.emit("Monitoring is unavailable: initialize devices first")
            return

        if self._lock_in_ready and self._monitor_use_case is not None:
            self._monitor_timer.start()
        if self._motor_ready:
            self._motor_timer.start()

        logger.info("Monitoring started")
        self.status_changed.emit("Monitoring started")

    def stop_monitoring(self) -> None:
        """Disable periodic lock-in and motor polling."""
        self._monitor_timer.stop()
        self._motor_timer.stop()
        logger.info("Monitoring stopped")
        self.status_changed.emit("Monitoring stopped")

    def move_motor_by(self, delta_steps: int, wait_ms: int = 20) -> None:
        """Move motor by relative steps and emit updated position."""
        if not self._motor_ready:
            self.status_changed.emit("Motor is not initialized")
            return
        try:
            self._motor.move_by(delta_steps)
            self._motor.wait_for_stop(wait_ms)
            pos = self._motor.get_position()
            self.motor_position_signal.emit(pos)
        except Exception as exc:  # noqa: BLE001
            self._last_error = str(exc)
            logger.exception("Relative motor move failed")
            self.status_changed.emit(f"Motor move failed: {exc}")

    def move_motor_to(self, target_steps: int, wait_ms: int = 100) -> None:
        """Move motor to absolute position and emit updated position."""
        if not self._motor_ready:
            self.status_changed.emit("Motor is not initialized")
            return
        try:
            self._motor.move_to(target_steps)
            self._motor.wait_for_stop(wait_ms)
            pos = self._motor.get_position()
            self.motor_position_signal.emit(pos)
        except Exception as exc:  # noqa: BLE001
            self._last_error = str(exc)
            logger.exception("Absolute motor move failed")
            self.status_changed.emit(f"Motor move failed: {exc}")

    def set_motor_zero(self) -> None:
        """Set current motor position as zero."""
        if not self._motor_ready:
            self.status_changed.emit("Motor is not initialized")
            return
        try:
            self._motor.set_zero()
            pos = self._motor.get_position()
            self.motor_position_signal.emit(pos)
            self.status_changed.emit("Motor zero position set")
        except Exception as exc:  # noqa: BLE001
            self._last_error = str(exc)
            logger.exception("Set zero failed")
            self.status_changed.emit(f"Set zero failed: {exc}")

    def stop_motor_motion(self) -> None:
        """Stop motor immediately."""
        if not self._motor_ready:
            return
        try:
            self._motor.stop()
        except Exception as exc:  # noqa: BLE001
            self._last_error = str(exc)
            logger.exception("Stop motor failed")
            self.status_changed.emit(f"Stop motor failed: {exc}")

    def start_measurement(self, settings: ScanSettings) -> None:
        """Start spectrogram measurement in background thread."""
        if self._measure_use_case is None:
            self.status_changed.emit("Measurement requires initialized Motor and Lock-In")
            return
        if self.is_measurement_running:
            self.status_changed.emit("Measurement is already running")
            return
        logger.info("Starting measurement with settings: %s", settings)

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
        logger.info("Measurement paused")
        self.status_changed.emit("Measurement paused")

    def resume_measurement(self) -> None:
        """Resume paused measurement."""
        if self._worker is None:
            return
        self._worker.resume()
        logger.info("Measurement resumed")
        self.status_changed.emit("Measurement resumed")

    def stop_measurement(self) -> None:
        """Request graceful stop of background measurement."""
        if self._worker is None:
            return
        self._worker.request_stop()
        logger.info("Stop requested for measurement")
        self.status_changed.emit("Stopping measurement...")

    def shutdown(self) -> None:
        """Stop active tasks and release device connections."""
        self.stop_monitoring()
        if self._worker is not None:
            self._worker.request_stop()
        if self._thread is not None and self._thread.isRunning():
            logger.info("Waiting active measurement thread shutdown")
            self._thread.quit()
            self._thread.wait(2000)

        if self._motor is not None:
            logger.info("Shutting down motor backend")
            self._motor.shutdown()
        if self._lock_in is not None:
            logger.info("Shutting down lock-in backend")
            self._lock_in.shutdown()

        self._motor_ready = False
        self._lock_in_ready = False
        self._monitor_use_case = None
        self._measure_use_case = None
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
            self._last_error = str(exc)
            logger.exception("Monitoring failed")
            self.status_changed.emit(f"Monitoring error: {exc}")
            self._monitor_timer.stop()

    def _poll_motor_position(self) -> None:
        if not self._motor_ready:
            return
        try:
            pos = self._motor.get_position()
            self.motor_position_signal.emit(pos)
        except Exception as exc:  # noqa: BLE001
            self._last_error = str(exc)
            logger.exception("Motor position polling failed")
            self.status_changed.emit(f"Motor polling error: {exc}")
            self._motor_timer.stop()

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
        logger.info("Measurement completed")
        self.status_changed.emit("Measurement completed")
        self.measurement_finished.emit()

    def _on_measurement_failed(self, error: str) -> None:
        if self._current_measure is not None:
            self._current_measure.data.setdefault("meta", {})["status"] = "failed"
            self._current_measure.data.setdefault("meta", {})["error"] = error
            self._current_measure.save(finish=True)
        self._last_error = error
        logger.error("Measurement failed: %s", error)
        self.status_changed.emit(f"Measurement failed: {error}")
        self.measurement_failed.emit(error)

    def _cleanup_thread_objects(self) -> None:
        logger.info("Measurement thread cleanup")
        self._thread = None
        self._worker = None
