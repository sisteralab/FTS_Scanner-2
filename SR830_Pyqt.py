import logging
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
    QInputDialog,
)

from Variable_data import VARIABLES
from SR830_Con_Test import main
from Com_List import SR_830

rm = pyvisa.ResourceManager()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class LockInWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super(LockInWidget, self).__init__(*args, **kwargs)
        self.powers = QLabel(self)
        self.powers.setText("None")
        self.btnStart = QPushButton("Start")
        self.btnStart.clicked.connect(self.startMonitor)
        self.btnStop = QPushButton("Stop")
        # self.btnStop.setEnabled(False)
        self.btnStop.clicked.connect(self.stopMonitor)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.powers, 0, 0)
        self.layout.addWidget(self.btnStart, 1, 0)
        self.layout.addWidget(self.btnStop, 1, 1)

    def startMonitor(self):
        self.SR830 = rm.open_resource(VARIABLES.Lock_In_GPIB, write_termination="\n", read_termination="\n")
        power = self.SR830.query(SR_830.READ_X)
        values = pyqtSignal(tuple)
        print (values)
        print (float(power))

    def stopMonitor(self):
        print (0)

    def updateMonitor(self, values: tuple):
        power = values
        self.powers.setText(f"{power}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # app.setStyleSheet("""QWidget {font-size: 14px;}""")
    myApp = LockInWidget()
    myApp.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        print("Closing Window...")