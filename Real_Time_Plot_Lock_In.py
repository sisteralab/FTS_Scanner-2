from PyQt5 import QtWidgets, QtCore
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import sys  # We need sys so that we can pass argv to QApplication
import os
from random import randint
import pyvisa
from Variable_data import VARIABLES
from Com_List import SR_830

rm = pyvisa.ResourceManager()

class GraphTimeWindow(QtWidgets.QMainWindow):

    def __init__(self, time_con = 100, points=100, *args, **kwargs):
        super(GraphTimeWindow, self).__init__(*args, **kwargs)
        self.points = points
        self.time_con = time_con
        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)

        self.SR830 = rm.open_resource(VARIABLES.Lock_In_GPIB, write_termination="\n", read_termination="\n")

        self.x = list(range(1))  # 100 time points
        self.y = [float(self.SR830.query(SR_830.READ_R)) for _ in range(1)]  # 100 data points
        self.graphWidget.setBackground('w')

        pen = pg.mkPen(color=(255, 0, 0))
        self.data_line = self.graphWidget.plot(self.x, self.y, pen=pen)
        self.graphWidget.setLabel("left", "Signal")
        self.graphWidget.setLabel("bottom", "Points")
        self.graphWidget.showGrid(x=True, y=True)
        self.timer = QtCore.QTimer()
        self.timer.setInterval(time_con)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()

        # Pause button in a toolbar. Pauses when checked
        self.toolbar = self.addToolBar("Pause")
        self.playScansAction = QtGui.QAction("Pause", self)
        self.playScansAction.triggered.connect(self.playScansPressed)
        self.playScansAction.setCheckable(True)
        self.toolbar.addAction(self.playScansAction)

    def playScansPressed(self):
        if self.playScansAction.isChecked():
            self.timer.stop()
        else:
            self.timer.start()



    def update_plot_data(self):

        if (max(self.x) - min(self.x)) < self.points - 1:
            self.x.append(self.x[-1] + 1)
            self.y.append(float(self.SR830.query(SR_830.READ_R)))
            self.data_line.setData(self.x, self.y)
        else:
            self.x = self.x[1:]  # Remove the first y element.
            self.x.append(self.x[-1] + 1)  # Add a new value 1 higher than the last.
            self.y = self.y[1:]  # Remove the first
            self.y.append(float(self.SR830.query(SR_830.READ_R)))  # Add a new random value.
            self.data_line.setData(self.x, self.y)  # Update the data.


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    # app.setStyleSheet("""QWidget {font-size: 14px;}""")
    myApp = GraphTimeWindow()
    myApp.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        print("Closing Window...")