import sys
import pyvisa
import time

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QSlider,
    QLabel,
    QGridLayout,
    QPushButton,
    QLineEdit,
    QInputDialog, QSpinBox,
)

from Real_Time_Plot_Lock_In import GraphTimeWindow


class Lock_Grap_Control( QWidget):
    def __init__(self, *args, **kwargs):
        super(Lock_Grap_Control, self).__init__(*args, **kwargs)
        self.button_start = QPushButton("Real Time Plot")
        self.label_time = QLabel("Set Time Const, ms")
        self.label_point = QLabel("Set Point Const")
        self.input_time = QSpinBox(self)
        self.input_point = QSpinBox(self)
        self.input_time.setRange(1, 2000)
        self.input_point.setRange(1, 100000)
        self.input_time.setValue(100)
        self.input_point.setValue(100)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.button_start, 0, 0, 1, 2)
        self.layout.addWidget(self.label_time, 1, 0, 1, 1)
        self.layout.addWidget(self.label_point, 2, 0, 1, 1)
        self.layout.addWidget(self.input_time, 1, 1, 1, 1)
        self.layout.addWidget(self.input_point, 2, 1, 1, 1)
        self.button_start.clicked.connect(self.the_button_was_clicked)


    def the_button_was_clicked(self):
        self.myGraph = GraphTimeWindow(time_con=self.input_time.value() ,points=self.input_point.value())
        self.myGraph.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # app.setStyleSheet("""QWidget {font-size: 14px;}""")
    myApp = Lock_Grap_Control()
    myApp.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        print("Closing Window...")