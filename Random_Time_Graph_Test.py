from PyQt5 import QtWidgets, QtCore
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
import os
from random import randint
import pyvisa
from Variable_data import VARIABLES
from Com_List import SR_830

rm = pyvisa.ResourceManager()
timer_const = 100
point_const = 100

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)

        self.SR830 = rm.open_resource(VARIABLES.Lock_In_GPIB, write_termination="\n", read_termination="\n")

        self.x = list(range(1))  # 100 time points
        self.y = [float(self.SR830.query(SR_830.READ_X)) for _ in range(1)]  # 100 data points

        self.graphWidget.setBackground('w')

        pen = pg.mkPen(color=(255, 0, 0))
        self.data_line = self.graphWidget.plot(self.x, self.y, pen=pen)
        self.graphWidget.setLabel("left", "Signal")
        self.graphWidget.setLabel("bottom", "Points")
        self.graphWidget.showGrid(x=True, y=True)
        self.timer = QtCore.QTimer()
        self.timer.setInterval(timer_const)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()

    def update_plot_data(self):
        if (max(self.x) - min(self.x)) < point_const - 1:
            self.x.append(self.x[-1] + 1)
            self.y.append(float(self.SR830.query(SR_830.READ_X)))
            self.data_line.setData(self.x, self.y)
        else:
            self.x = self.x[1:]  # Remove the first y element.
            self.x.append(self.x[-1] + 1)  # Add a new value 1 higher than the last.
            self.y = self.y[1:]  # Remove the first
            self.y.append(float(self.SR830.query(SR_830.READ_X)))  # Add a new random value.
            self.data_line.setData(self.x, self.y)  # Update the data.


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    # app.setStyleSheet("""QWidget {font-size: 14px;}""")
    myApp = MainWindow()
    myApp.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        print("Closing Window...")