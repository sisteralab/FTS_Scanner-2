from __future__ import annotations

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QStatusBar, QStyle, QTabWidget

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
        self._apply_ui_theme()

        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        self.setup_tab = SetupTab(controller, self)
        self.monitor_tab = MonitorTab(controller, self)
        self.measure_tab = MeasureTab(controller, self)

        self.tabs.addTab(self.setup_tab, self._std_icon("SP_ComputerIcon"), "SetUp")
        self.tabs.addTab(self.monitor_tab, self._std_icon("SP_FileDialogDetailedView"), "Monitor")
        self.tabs.addTab(self.measure_tab, self._std_icon("SP_DriveHDIcon"), "Measure")

        self.setStatusBar(QStatusBar(self))
        self._controller.status_changed.connect(self.statusBar().showMessage)

    def closeEvent(self, event) -> None:  # noqa: N802
        self._controller.shutdown()
        event.accept()

    def _std_icon(self, name: str) -> QIcon:
        enum_item = getattr(QStyle.StandardPixmap, name, None)
        if enum_item is None:
            return QIcon()
        return self.style().standardIcon(enum_item)

    def _apply_ui_theme(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background: #f4f7fb;
                color: #1f2a3a;
                font-size: 13px;
            }
            QTabWidget::pane {
                border: 1px solid #d6dce6;
                border-radius: 10px;
                background: #f9fbff;
                top: -1px;
            }
            QTabBar::tab {
                background: #e8eef8;
                border: 1px solid #d6dce6;
                border-bottom: none;
                padding: 8px 16px;
                margin-right: 6px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: #f9fbff;
                color: #0f254a;
                font-weight: 600;
            }
            QGroupBox {
                background: #ffffff;
                border: 1px solid #dbe2ed;
                border-radius: 10px;
                margin-top: 12px;
                padding: 12px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
                color: #253a5a;
            }
            QPushButton {
                background: #2f76d2;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 7px 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #2867bb;
            }
            QPushButton:disabled {
                background: #a6b6cf;
                color: #eef2f8;
            }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background: #fefefe;
                border: 1px solid #ccd6e5;
                border-radius: 7px;
                padding: 5px 8px;
                min-height: 26px;
            }
            QLabel {
                background: transparent;
            }
            QStatusBar {
                background: #e9eef6;
                border-top: 1px solid #d4dce8;
            }
            """
        )
