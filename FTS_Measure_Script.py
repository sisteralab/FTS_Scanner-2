import sys
import pyqtgraph as pg
from PyQt5.QtWidgets import QVBoxLayout
from pyqtgraph.Qt import QtCore, QtGui
from PyQt5 import QtWidgets, QtCore

import pyvisa
from Connection_Test import Test_Window
from Motor_class import Motor
from Variable_data import VARIABLES
from Com_List import SR_830

rm = pyvisa.ResourceManager()
open_name = VARIABLES.Motor_name
device = Motor(open_name)
address, pyximc = Test_Window.ximc_check(VARIABLES.XIMC_Path)

class GraphInterWindow(QtWidgets.QWidget):

    def __init__(self, wait_time = 500, pos_border = 0.5, neg_border = 0.5, step = 10, measures_count=1, *args, **kwargs):
        super(GraphInterWindow, self).__init__(*args, **kwargs)
        self.Update_Variables(wait_time, pos_border, neg_border, step, measures_count)
        self.graphWidget = pg.PlotWidget()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.graphWidget)
        self.graphWidget.setBackground('w')
        self.graphWidget.setLabel("left", "Signal")
        self.graphWidget.setLabel("bottom", "Points")
        self.graphWidget.showGrid(x=True, y=True)


    def Inter_Plot_Start(self):
        self.SR830 = rm.open_resource(VARIABLES.Lock_In_GPIB, write_termination="\n", read_termination="\n")
        self.x = list(range(1))
        self.y = [float(self.SR830.query(SR_830.READ_X)) for _ in range(1)]  # 100 data points
        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()


        pen = pg.mkPen(color=(255, 0, 0))
        self.data_line = self.graphWidget.plot(self.x, self.y, pen=pen)

    def update_plot_data(self):
        if (max(self.x) - min(self.x)) < self.step_points:
            self.y.append(float(self.SR830.query(SR_830.READ_R)))
            device.delta_move(self.step, 0)
            device.wait_for_stop(self.wait_time)
            self.x.append(self.x[-1] + 1)
            self.data_line.setData(self.x, self.y)
        else:
            self.timer.stop()


    def stop_plot_processing(self):
        self.timer.stop()

    def start_plot_processing(self):
        self.timer.start()

    def Update_Variables(self, wait_time = 100, pos_border = 1.0, neg_border = 1.0, step = 10, measures_count = 1):
        self.wait_time = wait_time
        self.pos_border = pos_border
        self.neg_border = neg_border
        self.step = step
        self.step_neg_border = round(self.pos_border * 1000 / 2.5)
        self.step_pos_border = round(self.neg_border * 1000 / 2.5)
        self.step_distance = self.step * 2.5
        self.step_points = round(((self.pos_border + self.neg_border) * 1000 / 2.5 // self.step))
        self.measures_count = measures_count


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet("""QWidget {font-size: 14px;}""")
    myApp = GraphInterWindow()
    myApp.Inter_Plot_Start()
    myApp.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        print("Closing Window...")