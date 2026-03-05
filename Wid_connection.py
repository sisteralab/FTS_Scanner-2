import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QSlider,
    QLabel,
    QHBoxLayout,
    QTabWidget,
    QPushButton,
    QGridLayout,
)
from Connection_Test import Test_Window
from Variable_data import VARIABLES

from PyQt5.QtCore import Qt
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np


class Ximc_app(QWidget):
    # button_count = 0
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.button_label = QLabel("Checking the connection to XIMC")
        self.button = QPushButton("Connect Ximc lib")
        self.button.clicked.connect(self.the_button_was_clicked)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.button_label, 0, 0)
        self.layout.addWidget(self.button, 0, 1)

    def the_button_was_clicked(self):
        # MyApp.button_count += 1
        Test_Window.ximc_check(VARIABLES.XIMC_Path)
        if Test_Window.check_var == 1:
            self.button.setText("Connect!")
        else:
            self.button.setText("Disconnect!")

        # self.button.setText("Random! " + str(Ximc_app.button_count))


# class Ximc_app(QWidget):
#     # button_count = 0
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.title = "Ximc connection"
#         self.setWindowTitle(self.title)
#         self.layout = QGridLayout()
#         self.setLayout(self.layout)
#         self.button = QPushButton("Connect Ximc lib")
#         self.layout.addWidget(self.button)
#         self.layout.addWidget(self.Ximc_check)
#
#     def Ximc_check(self):
#
#         self.button.clicked.connect(self.the_button_was_clicked)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("""QWidget {font-size: 14px;}""")
    myApp = Ximc_app()
    myApp.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        print("Closing Window...")
