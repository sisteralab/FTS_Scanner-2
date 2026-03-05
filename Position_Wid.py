import logging
import sys
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
from Connection_Test import Test_Window
from Motor_class import Motor

address, pyximc = Test_Window.ximc_check(VARIABLES.XIMC_Path)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
time_const = VARIABLES.Motor_Up_Const


class MonitorThread(QThread):
    values = pyqtSignal(tuple)

    def run(self):
        self.device = Motor(VARIABLES.Motor_name)
        while 1:
            steps, milisteps = self.device.get_position()
            self.values.emit((steps, milisteps))
            # print (type(steps))
            time.sleep(time_const)


    def terminate(self) -> None:
        super().terminate()
        logger.info(f"[{self.__class__.__name__}.terminate] Terminated")



class MonitorWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super(MonitorWidget, self).__init__(*args, **kwargs)
        self.steps = QLabel(self)
        self.steps.setText("None")
        self.mili_steps = QLabel(self)
        self.mili_steps.setText("None")
        self.btnStart = QPushButton("Start")
        self.btnStart.clicked.connect(self.startMonitor)
        self.btnStop = QPushButton("Stop")
        self.btnStop.setEnabled(False)
        self.btnStop.clicked.connect(self.stopMonitor)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.steps, 0, 0)
        self.layout.addWidget(self.mili_steps, 0, 1)
        self.layout.addWidget(self.btnStart, 1, 0)
        self.layout.addWidget(self.btnStop, 1, 1)


    def startMonitor(self):
        self.monitor_thread = MonitorThread()
        self.monitor_thread.values.connect(self.updateMonitor)
        self.monitor_thread.start()

        self.btnStop.setEnabled(True)
        self.btnStart.setEnabled(False)
        self.monitor_thread.finished.connect(lambda: self.btnStart.setEnabled(True))
        self.monitor_thread.finished.connect(lambda: self.btnStop.setEnabled(False))

    def stopMonitor(self):
        self.monitor_thread.terminate()


    def updateMonitor(self, values: tuple):
        steps, mili_steps = values
        self.steps.setText(f"{steps}")
        self.mili_steps.setText(f"{mili_steps}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # app.setStyleSheet("""QWidget {font-size: 14px;}""")
    myApp = MonitorWidget()
    myApp.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        print("Closing Window...")
