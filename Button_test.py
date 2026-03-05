import sys

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget


class Window(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Button with a parent widget
        topBtn = QPushButton(parent=self)
        topBtn.setFixedSize(100, 60)
        # Button with a text and parent widget
        centerBtn = QPushButton(text="Center", parent=self)
        centerBtn.setFixedSize(100, 60)
        # Button with an icon, a text, and a parent widget
        bottomBtn = QPushButton(
            icon=QIcon("./icons/logo.svg"), text="Bottom", parent=self
        )
        bottomBtn.setFixedSize(100, 60)
        bottomBtn.setIconSize(QSize(40, 40))
        layout = QVBoxLayout()
        layout.addWidget(topBtn)
        layout.addWidget(centerBtn)
        layout.addWidget(bottomBtn)
        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
