from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from fts_scanner.config import AppConfig
from fts_scanner.presentation.controller import MainController
from fts_scanner.presentation.widgets.main_window import MainWindow


def run() -> int:
    """Launch desktop application."""
    app = QApplication(sys.argv)
    project_root = _resolve_runtime_root()
    icon_path = project_root / "assets" / "app_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    config = AppConfig.from_project_root(project_root)
    controller = MainController(config=config, project_root=project_root)
    window = MainWindow(controller)
    window.show()
    return app.exec()


def _resolve_runtime_root() -> Path:
    """Resolve project/bundle root for source and frozen execution."""
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]
