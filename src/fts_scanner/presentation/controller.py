from __future__ import annotations

import logging
from dataclasses import asdict
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QTimer, Signal

from fts_scanner.config import AppConfig
from fts_scanner.devices.lockin_types import LockInAdapterType
from fts_scanner.devices.simulated import SimulatedLockInDevice, SimulatedMotorDevice
from fts_scanner.devices.sr830_visa import SR830VisaLockIn
from fts_scanner.devices.thzdaqapi_lockin import SR830ThzdaqapiLockIn
from fts_scanner.devices.ximc_motor import XimcMotorDevice
from fts_scanner.domain.models import ScanSettings
from fts_scanner.presentation.device_workers import LockInIoWorker, MotorIoWorker
from fts_scanner.presentation.measurement_worker import MeasurementWorker
from fts_scanner.store.measure_store import MeasureManager, MeasureModel, MeasureType
from fts_scanner.use_cases.measure_spectrogram import MeasureSpectrogramUseCase

logger = logging.getLogger(__name__)


class MainController(QObject):
    """Coordinates UI actions, device adapters and use-cases."""

    status_changed = Signal(str)
    setup_status = Signal(bool, bool, str)
    monitoring_state_changed = Signal(bool)
    monitoring_signal = Signal(float)
    motor_position_signal = Signal(int)
    motor_motion_params_signal = Signal(int, int)
    measurement_point = Signal(dict)
    measurement_started = Signal()
    measurement_finished = Signal()
    measurement_failed = Signal(str)
    initialized = Signal(bool)

    motor_poll_requested = Signal()
    motor_move_by_requested = Signal(int, int)
    motor_move_to_requested = Signal(int, int)
    motor_set_zero_requested = Signal()
    motor_stop_requested = Signal()
    motor_start_jog_requested = Signal(int)
    motor_read_motion_requested = Signal()
    motor_write_motion_requested = Signal(int, int)

    lockin_poll_requested = Signal()

    def __init__(self, config: AppConfig, project_root: Path) -> None:
        super().__init__()
        self._config = config
        self._project_root = project_root

        self._motor = None
        self._lock_in = None
        self._measure_use_case: MeasureSpectrogramUseCase | None = None

        self._motor_ready = False
        self._lock_in_ready = False

        self._monitor_timer = QTimer(self)
        self._monitor_timer.setInterval(200)
        self._monitor_timer.timeout.connect(self._request_lockin_poll)

        self._motor_timer = QTimer(self)
        self._motor_timer.setInterval(200)
        self._motor_timer.timeout.connect(self._request_motor_poll)

        self._motor_thread: QThread | None = None
        self._motor_worker: MotorIoWorker | None = None
        self._lockin_thread: QThread | None = None
        self._lockin_worker: LockInIoWorker | None = None

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
        lock_in_visa_resource: str | None = None,
        lock_in_visa_library: str | None = None,
        motor_name: str | None = None,
        ximc_root: str | None = None,
    ) -> None:
        """Create device adapters and initialize hardware stack."""
        logger.info("Initialize devices requested. simulation=%s", use_simulation)
        self.shutdown()
        self._last_error = None

        self._config.use_simulation = bool(use_simulation)
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
        if lock_in_visa_resource is not None:
            self._config.lock_in_visa_resource = lock_in_visa_resource.strip()
        if lock_in_visa_library is not None:
            self._config.lock_in_visa_library = lock_in_visa_library.strip()
        if motor_name is not None:
            self._config.motor_name = motor_name.strip() or None
        if ximc_root is not None and ximc_root.strip():
            self._config.ximc_root = Path(ximc_root.strip())

        try:
            self._config.save_to_ini()
        except Exception:  # noqa: BLE001
            logger.exception("Failed to persist settings.ini")

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
            self._lock_in = self._build_lock_in_device()

        motor_message = "Motor not initialized"
        lockin_message = "Lock-In not initialized"

        try:
            self._motor.initialize()
            self._motor_ready = True
            pos = self._motor.get_position()
            self.motor_position_signal.emit(pos)
            self._start_motor_worker(self._motor)
            self.read_motor_motion_params()
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
            self._start_lockin_worker(self._lock_in)
            lockin_message = f"Lock-In connected: {lock_in_idn}"
        except Exception as exc:  # noqa: BLE001
            self._lock_in_ready = False
            self._last_error = str(exc)
            lockin_message = f"Lock-In init failed: {exc}"
            logger.exception("Lock-In initialization failed")

        self._measure_use_case = (
            MeasureSpectrogramUseCase(self._motor, self._lock_in)
            if self._motor_ready and self._lock_in_ready
            else None
        )

        if use_simulation:
            message = f"Simulation mode enabled. {motor_message}; {lockin_message}"
        else:
            message = f"{motor_message}; {lockin_message}"
        ok = self._motor_ready and self._lock_in_ready
        self.setup_status.emit(self._motor_ready, self._lock_in_ready, message)
        self.status_changed.emit(message)
        self.initialized.emit(ok)
        logger.info("Setup result. motor_ok=%s lockin_ok=%s", self._motor_ready, self._lock_in_ready)

    def start_monitoring(self) -> None:
        """Enable periodic lock-in and motor polling."""
        if self.is_monitoring():
            self.status_changed.emit("Monitoring already running")
            return
        if not self._motor_ready and not self._lock_in_ready:
            self.status_changed.emit("Monitoring is unavailable: initialize devices first")
            return

        if self._lock_in_ready and self._lockin_worker is not None:
            self._monitor_timer.start()
        if self._motor_ready and self._motor_worker is not None:
            self._motor_timer.start()

        logger.info("Monitoring started")
        self.status_changed.emit("Monitoring started")
        self.monitoring_state_changed.emit(True)

    def stop_monitoring(self) -> None:
        """Disable periodic lock-in and motor polling."""
        was_running = self.is_monitoring()
        self._monitor_timer.stop()
        self._motor_timer.stop()
        if was_running:
            logger.info("Monitoring stopped")
            self.status_changed.emit("Monitoring stopped")
            self.monitoring_state_changed.emit(False)

    def is_monitoring(self) -> bool:
        """Return True if monitor timers are active."""
        return self._monitor_timer.isActive() or self._motor_timer.isActive()

    def move_motor_by(self, delta_steps: int, wait_ms: int = 20) -> None:
        """Queue relative motor move in worker thread."""
        if self.is_measurement_running:
            self.status_changed.emit("Motor control is disabled while measurement is running")
            return
        if not self._motor_ready or self._motor_worker is None:
            self.status_changed.emit("Motor is not initialized")
            return
        self.motor_move_by_requested.emit(int(delta_steps), int(wait_ms))

    def move_motor_to(self, target_steps: int, wait_ms: int = 100) -> None:
        """Queue absolute motor move in worker thread."""
        if self.is_measurement_running:
            self.status_changed.emit("Motor control is disabled while measurement is running")
            return
        if not self._motor_ready or self._motor_worker is None:
            self.status_changed.emit("Motor is not initialized")
            return
        self.motor_move_to_requested.emit(int(target_steps), int(wait_ms))

    def set_motor_zero(self) -> None:
        """Queue set-zero motor command."""
        if self.is_measurement_running:
            self.status_changed.emit("Motor control is disabled while measurement is running")
            return
        if not self._motor_ready or self._motor_worker is None:
            self.status_changed.emit("Motor is not initialized")
            return
        self.motor_set_zero_requested.emit()

    def stop_motor_motion(self) -> None:
        """Stop motor immediately."""
        if not self._motor_ready or self._motor_worker is None:
            return
        self.motor_stop_requested.emit()

    def start_motor_jog(self, direction: int) -> None:
        """Start continuous motor jog while control is held."""
        if self.is_measurement_running:
            self.status_changed.emit("Motor control is disabled while measurement is running")
            return
        if not self._motor_ready or self._motor_worker is None:
            self.status_changed.emit("Motor is not initialized")
            return
        if direction == 0:
            return
        self.motor_start_jog_requested.emit(1 if direction > 0 else -1)

    def read_motor_motion_params(self) -> None:
        """Request current speed/acceleration from motor."""
        if not self._motor_ready or self._motor_worker is None:
            return
        self.motor_read_motion_requested.emit()

    def set_motor_motion_params(self, speed: int, acceleration: int) -> None:
        """Apply motor speed/acceleration in worker thread."""
        if self.is_measurement_running:
            self.status_changed.emit("Motor control is disabled while measurement is running")
            return
        if not self._motor_ready or self._motor_worker is None:
            self.status_changed.emit("Motor is not initialized")
            return
        self.motor_write_motion_requested.emit(int(speed), int(acceleration))

    def start_measurement(self, settings: ScanSettings) -> None:
        """Start spectrogram measurement in background thread."""
        if self._measure_use_case is None:
            self.status_changed.emit("Measurement requires initialized Motor and Lock-In")
            return
        if self.is_measurement_running:
            self.status_changed.emit("Measurement is already running")
            return

        if self.is_monitoring():
            self.stop_monitoring()

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

        self._stop_motor_worker()
        self._stop_lockin_worker()

        if self._motor is not None:
            logger.info("Shutting down motor backend")
            try:
                self._motor.shutdown()
            except Exception:  # noqa: BLE001
                logger.exception("Motor shutdown failed")
        if self._lock_in is not None:
            logger.info("Shutting down lock-in backend")
            try:
                self._lock_in.shutdown()
            except Exception:  # noqa: BLE001
                logger.exception("Lock-In shutdown failed")

        self._motor_ready = False
        self._lock_in_ready = False
        self._measure_use_case = None
        self._current_measure = None
        self._thread = None
        self._worker = None
        self._motor = None
        self._lock_in = None

    def _request_lockin_poll(self) -> None:
        if self._lockin_worker is not None:
            self.lockin_poll_requested.emit()

    def _request_motor_poll(self) -> None:
        if self._motor_worker is not None:
            self.motor_poll_requested.emit()

    def _build_lock_in_device(self):
        adapter = self._config.lock_in_adapter
        if adapter == LockInAdapterType.KEYSIGHT_VISA:
            if not self._config.lock_in_visa_resource:
                raise RuntimeError("VISA resource is empty")
            return SR830VisaLockIn(
                resource=self._config.lock_in_visa_resource,
                visa_library=self._config.lock_in_visa_library or None,
            )
        if adapter in (LockInAdapterType.PROLOGIX_ETHERNET, LockInAdapterType.PROLOGIX_USB):
            return SR830ThzdaqapiLockIn(
                adapter_type=adapter,
                gpib_address=self._config.lock_in_gpib_address,
                host=self._config.lock_in_host,
                ethernet_port=self._config.lock_in_port,
                usb_port=self._config.lock_in_usb_port,
            )
        raise RuntimeError(
            f"Unsupported Lock-In adapter '{adapter}'. "
            "Use keysight_visa, prologix_ethernet or prologix_usb."
        )

    def _start_motor_worker(self, motor: object) -> None:
        self._stop_motor_worker()

        self._motor_worker = MotorIoWorker(motor)
        self._motor_thread = QThread(self)
        self._motor_worker.moveToThread(self._motor_thread)
        self._motor_thread.finished.connect(self._motor_worker.deleteLater)

        self.motor_poll_requested.connect(self._motor_worker.poll_position)
        self.motor_move_by_requested.connect(self._motor_worker.move_by)
        self.motor_move_to_requested.connect(self._motor_worker.move_to)
        self.motor_set_zero_requested.connect(self._motor_worker.set_zero)
        self.motor_stop_requested.connect(self._motor_worker.stop_motion)
        self.motor_start_jog_requested.connect(self._motor_worker.start_jog)
        self.motor_read_motion_requested.connect(self._motor_worker.read_motion_params)
        self.motor_write_motion_requested.connect(self._motor_worker.set_motion_params)

        self._motor_worker.position_ready.connect(self.motor_position_signal.emit)
        self._motor_worker.command_error.connect(self._on_motor_worker_error)
        self._motor_worker.motion_params_ready.connect(self._on_motor_motion_params_ready)
        self._motor_worker.motion_params_applied.connect(self._on_motor_motion_params_applied)

        self._motor_thread.start()

    def _stop_motor_worker(self) -> None:
        if self._motor_worker is not None:
            for signal, slot in (
                (self.motor_poll_requested, self._motor_worker.poll_position),
                (self.motor_move_by_requested, self._motor_worker.move_by),
                (self.motor_move_to_requested, self._motor_worker.move_to),
                (self.motor_set_zero_requested, self._motor_worker.set_zero),
                (self.motor_stop_requested, self._motor_worker.stop_motion),
                (self.motor_start_jog_requested, self._motor_worker.start_jog),
                (self.motor_read_motion_requested, self._motor_worker.read_motion_params),
                (self.motor_write_motion_requested, self._motor_worker.set_motion_params),
            ):
                try:
                    signal.disconnect(slot)
                except Exception:  # noqa: BLE001
                    pass
            try:
                self._motor_worker.position_ready.disconnect(self.motor_position_signal.emit)
            except Exception:  # noqa: BLE001
                pass
            try:
                self._motor_worker.command_error.disconnect(self._on_motor_worker_error)
            except Exception:  # noqa: BLE001
                pass
            try:
                self._motor_worker.motion_params_ready.disconnect(self._on_motor_motion_params_ready)
            except Exception:  # noqa: BLE001
                pass
            try:
                self._motor_worker.motion_params_applied.disconnect(
                    self._on_motor_motion_params_applied
                )
            except Exception:  # noqa: BLE001
                pass

        if self._motor_thread is not None:
            self._motor_thread.quit()
            self._motor_thread.wait(1500)

        self._motor_thread = None
        self._motor_worker = None

    def _start_lockin_worker(self, lock_in: object) -> None:
        self._stop_lockin_worker()

        self._lockin_worker = LockInIoWorker(lock_in)
        self._lockin_thread = QThread(self)
        self._lockin_worker.moveToThread(self._lockin_thread)
        self._lockin_thread.finished.connect(self._lockin_worker.deleteLater)

        self.lockin_poll_requested.connect(self._lockin_worker.read_signal)
        self._lockin_worker.signal_ready.connect(self.monitoring_signal.emit)
        self._lockin_worker.poll_error.connect(self._on_lockin_worker_error)

        self._lockin_thread.start()

    def _stop_lockin_worker(self) -> None:
        if self._lockin_worker is not None:
            try:
                self.lockin_poll_requested.disconnect(self._lockin_worker.read_signal)
            except Exception:  # noqa: BLE001
                pass
            try:
                self._lockin_worker.signal_ready.disconnect(self.monitoring_signal.emit)
            except Exception:  # noqa: BLE001
                pass
            try:
                self._lockin_worker.poll_error.disconnect(self._on_lockin_worker_error)
            except Exception:  # noqa: BLE001
                pass

        if self._lockin_thread is not None:
            self._lockin_thread.quit()
            self._lockin_thread.wait(1500)

        self._lockin_thread = None
        self._lockin_worker = None

    def _on_motor_worker_error(self, error: str) -> None:
        self._last_error = error
        logger.error(error)
        self.status_changed.emit(error)
        self._motor_timer.stop()
        if not self._monitor_timer.isActive():
            self.monitoring_state_changed.emit(False)

    def _on_lockin_worker_error(self, error: str) -> None:
        self._last_error = error
        logger.error(error)
        self.status_changed.emit(error)
        self._monitor_timer.stop()
        if not self._motor_timer.isActive():
            self.monitoring_state_changed.emit(False)

    def _on_motor_motion_params_ready(self, speed: int, acceleration: int) -> None:
        self._config.motor_speed = int(speed)
        self._config.motor_acceleration = int(acceleration)
        try:
            self._config.save_to_ini()
        except Exception:  # noqa: BLE001
            logger.exception("Failed to persist motor motion params")
        self.motor_motion_params_signal.emit(int(speed), int(acceleration))

    def _on_motor_motion_params_applied(self, speed: int, acceleration: int) -> None:
        self.status_changed.emit(
            f"Motor params applied: speed={int(speed)} accel={int(acceleration)}"
        )

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
