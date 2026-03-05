from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QStatusBar, QTabWidget

from fts_scanner.presentation.controller import MainController
from fts_scanner.presentation.widgets.measure_tab import MeasureTab
from fts_scanner.presentation.widgets.monitor_tab import MonitorTab
from fts_scanner.presentation.widgets.setup_tab import SetupTab


class MainWindow(QMainWindow):
    """Main app window with SetUp, Monitor and Measure tabs."""

    def __init__(self, controller: MainController) -> None:
        super().__init__()
        self._controller = controller

        self.setWindowTitle("FTS Scanner")
        self.resize(1400, 900)

        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        self.setup_tab = SetupTab(controller, self)
        self.monitor_tab = MonitorTab(controller, self)
        self.measure_tab = MeasureTab(controller, self)

        self.tabs.addTab(self.setup_tab, "SetUp")
        self.tabs.addTab(self.monitor_tab, "Monitor")
        self.tabs.addTab(self.measure_tab, "Measure")

        self.setStatusBar(QStatusBar(self))
        self._controller.status_changed.connect(self.statusBar().showMessage)

    def closeEvent(self, event) -> None:  # noqa: N802
        self._controller.shutdown()
        event.accept()
