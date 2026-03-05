from __future__ import annotations

import math
import shutil
import subprocess
import tempfile
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPainterPath, QPen


def draw_icon(size: int = 1024) -> QImage:
    """Render branded FTS icon as a square image."""
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0.0, QColor("#0B1F3A"))
    gradient.setColorAt(0.55, QColor("#1A4D7A"))
    gradient.setColorAt(1.0, QColor("#2F8F9D"))

    border = QPainterPath()
    border.addRoundedRect(QRectF(40, 40, size - 80, size - 80), 200, 200)
    painter.fillPath(border, gradient)

    wave_pen = QPen(QColor("#FFFFFF"))
    wave_pen.setWidth(max(8, size // 56))
    wave_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(wave_pen)

    center_y = size * 0.56
    amplitude = size * 0.15
    period = size * 0.18

    wave = QPainterPath(QPointF(size * 0.12, center_y))
    x = size * 0.12
    end = size * 0.88
    while x <= end:
        y = center_y + amplitude * math.sin((x - size * 0.12) / period)
        wave.lineTo(QPointF(x, y))
        x += size * 0.01

    painter.drawPath(wave)

    scan_pen = QPen(QColor("#7EE6FF"))
    scan_pen.setWidth(max(4, size // 110))
    painter.setPen(scan_pen)
    for step in range(4):
        x_line = size * (0.2 + step * 0.2)
        painter.drawLine(QPointF(x_line, size * 0.22), QPointF(x_line, size * 0.82))

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#F7FBFF"))
    painter.drawEllipse(QPointF(size * 0.78, size * 0.28), size * 0.06, size * 0.06)

    painter.end()
    return image


def main() -> None:
    """Generate PNG and ICO icon assets for the application."""
    assets_dir = Path(__file__).resolve().parents[1] / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    png_path = assets_dir / "app_icon.png"
    ico_path = assets_dir / "app_icon.ico"
    icns_path = assets_dir / "app_icon.icns"

    image = draw_icon(size=1024)
    if not image.save(str(png_path), "PNG"):
        raise RuntimeError(f"Failed to save PNG icon: {png_path}")

    # Windows executable icon.
    if not image.scaled(256, 256, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation).save(str(ico_path), "ICO"):
        raise RuntimeError(f"Failed to save ICO icon: {ico_path}")

    _generate_icns_if_possible(png_path, icns_path)

    print(f"Generated: {png_path}")
    print(f"Generated: {ico_path}")
    if icns_path.exists():
        print(f"Generated: {icns_path}")


def _generate_icns_if_possible(png_path: Path, icns_path: Path) -> None:
    """Generate macOS ICNS icon using iconutil when available."""
    if shutil.which("iconutil") is None or shutil.which("sips") is None:
        return

    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / "app.iconset"
        iconset.mkdir(parents=True, exist_ok=True)

        size_pairs = [
            (16, "icon_16x16.png"),
            (32, "icon_16x16@2x.png"),
            (32, "icon_32x32.png"),
            (64, "icon_32x32@2x.png"),
            (128, "icon_128x128.png"),
            (256, "icon_128x128@2x.png"),
            (256, "icon_256x256.png"),
            (512, "icon_256x256@2x.png"),
            (512, "icon_512x512.png"),
            (1024, "icon_512x512@2x.png"),
        ]

        for size, filename in size_pairs:
            target = iconset / filename
            subprocess.run(
                ["sips", "-z", str(size), str(size), str(png_path), "--out", str(target)],
                check=True,
                capture_output=True,
                text=True,
            )

        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset), "-o", str(icns_path)],
            check=True,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    main()
