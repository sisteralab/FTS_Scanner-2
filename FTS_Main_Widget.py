import sys
import datetime
import pyqtgraph as pg

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QSlider,
    QLabel,
    QGridLayout,
    QPushButton,
    QLineEdit,
    QInputDialog, QSpinBox, QDoubleSpinBox, QVBoxLayout, QHBoxLayout
)

from Variable_data import VARIABLES
from FTS_Measure_Script import GraphInterWindow
from Motor_class import Motor
open_name = VARIABLES.Motor_name
device = Motor(open_name)

class FTS_Main (QWidget):
    def __init__(self, *args, **kwargs):
        super(FTS_Main, self).__init__(*args, **kwargs)

        # self.plt = pg.plot()

        self.button_start = QPushButton("Start")
        self.button_pause = QPushButton("Pause")
        self.button_stop = QPushButton("Stop")
        self.button_continue = QPushButton("Continue")
        self.input_time = QSpinBox(self)
        self.input_pos_pos = QDoubleSpinBox(self)
        self.input_neg_pos = QDoubleSpinBox(self)
        self.input_step = QSpinBox(self)
        self.label_time = QLabel("Wait Time (ms)")
        self.label_pos_pos = QLabel("+ Border Position (mm)")
        self.label_neg_pos = QLabel("- Border Position (mm)")
        self.label_step = QLabel("Step (*2.5um)")
        self.res_label_time = QLabel("None")
        self.res_label_pos_pos = QLabel("None")
        self.res_label_neg_pos = QLabel("None")
        self.res_label_step = QLabel("None")
        self.input_time.setRange(1, 400000)
        self.input_time.setValue(400)
        self.input_pos_pos.setRange(0.01, 200)
        self.input_pos_pos.setValue(10)
        self.input_neg_pos.setRange(0.01, 200)
        self.input_neg_pos.setValue(10)
        self.input_step.setRange(1, 1000)
        self.input_step.setValue(10)
        self.input_time.valueChanged.connect(self.update_time_label)
        self.input_pos_pos.valueChanged.connect(self.update_pos_label)
        self.input_neg_pos.valueChanged.connect(self.update_neg_label)
        self.input_step.valueChanged.connect(self.update_step_label)
        self.measures_count_label = QLabel("Measures count", self)
        self.measures_count = QSpinBox(self)
        self.measures_count.setRange(1, 20)
        self.measures_count.setValue(1)
        self.layout = QHBoxLayout()
        self.grid_layout = QGridLayout()
        self.setLayout(self.layout)
        self.myGraph = GraphInterWindow(wait_time=self.input_time.value(), pos_border=self.input_pos_pos.value(),
                                        neg_border=self.input_neg_pos.value(), step=self.input_step.value(), measures_count=self.measures_count.value())
        self.layout.addWidget(self.myGraph)
        self.layout.addLayout(self.grid_layout)
        self.grid_layout.addWidget(self.label_time, 0, 2)
        self.grid_layout.addWidget(self.input_time, 0, 3)
        self.grid_layout.addWidget(self.res_label_time, 0, 4)
        self.grid_layout.addWidget(self.label_pos_pos, 1, 2)
        self.grid_layout.addWidget(self.input_pos_pos, 1, 3)
        self.grid_layout.addWidget(self.res_label_pos_pos, 1, 4)
        self.grid_layout.addWidget(self.label_neg_pos, 2, 2)
        self.grid_layout.addWidget(self.input_neg_pos, 2, 3)
        self.grid_layout.addWidget(self.res_label_neg_pos, 2, 4)
        self.grid_layout.addWidget(self.label_step, 3, 2)
        self.grid_layout.addWidget(self.input_step, 3, 3)
        self.grid_layout.addWidget(self.res_label_step, 3, 4)

        self.grid_layout.addWidget(self.measures_count_label, 4, 2)
        self.grid_layout.addWidget(self.measures_count, 4, 3)

        self.grid_layout.addWidget(self.button_start, 5, 2)
        self.grid_layout.addWidget(self.button_continue, 5, 3, 1, 2)
        self.grid_layout.addWidget(self.button_stop, 6, 2)
        self.grid_layout.addWidget(self.button_pause, 6, 3, 1, 2)

        self.button_start.setEnabled(True)
        self.button_stop.setEnabled(False)
        self.button_pause.setEnabled(False)
        self.button_continue.setEnabled(False)
        self.def_label_time()
        self.def_label_pos_pos()
        self.def_label_neg_pos()
        self.def_label_step()
        self.button_start.clicked.connect(self.button_start_was_clicked)
        self.button_stop.clicked.connect(self.button_stop_was_clicked)
        self.button_pause.clicked.connect(self.button_pause_was_clicked)
        self.button_continue.clicked.connect(self.button_continue_was_clicked)


    def def_label_time(self):
        self.res_label_time.setText(f"≈ {datetime.timedelta(seconds=((self.input_time.value() +100)* 1.5 * round((self.input_pos_pos.value() + self.input_neg_pos.value()) * 1000 / 2.5 // self.input_step.value()) // 1000))}")

    def def_label_pos_pos(self):
        self.res_label_pos_pos.setText(f"{round(self.input_pos_pos.value() * 1000 / 2.5)} steps ")

    def def_label_neg_pos(self):
        self.res_label_neg_pos.setText(f"{round(self.input_neg_pos.value() * 1000 / 2.5)} steps ")

    def def_label_step(self):
        self.res_label_step.setText(f"{self.input_step.value() * 2.5} um {round((self.input_pos_pos.value() + self.input_neg_pos.value()) * 1000 / 2.5 // self.input_step.value()) + 1} point ≈ {round(30 / self.input_step.value(), 2)} THz")

    def update_time_label(self):
        self.def_label_time()

    def update_pos_label(self):
        self.def_label_pos_pos()
        self.def_label_step()
        self.def_label_time()

    def update_neg_label(self):
        self.def_label_neg_pos()
        self.def_label_step()
        self.def_label_time()

    def update_step_label (self):
        self.def_label_step()
        self.def_label_time()

    def button_start_was_clicked(self):
        self.button_start.setEnabled(False)
        self.button_stop.setEnabled(True)
        self.button_pause.setEnabled(True)
        self.button_continue.setEnabled(False)
        device.move(-round(self.input_neg_pos.value() * 1000 / 2.5), 0)
        device.wait_for_stop(100)
        self.myGraph.Update_Variables(wait_time=self.input_time.value(), pos_border=self.input_pos_pos.value(),
                                        neg_border=self.input_neg_pos.value(), step=self.input_step.value())
        self.myGraph.Inter_Plot_Start()

    def button_stop_was_clicked(self):
        self.myGraph.stop_plot_processing()
        self.button_start.setEnabled(True)
        self.button_stop.setEnabled(False)
        self.button_pause.setEnabled(False)
        self.button_continue.setEnabled(False)
        return

    def button_pause_was_clicked(self):
        self.myGraph.stop_plot_processing()
        self.button_start.setEnabled(False)
        self.button_stop.setEnabled(True)
        self.button_pause.setEnabled(False)
        self.button_continue.setEnabled(True)
        # self.grid_layout.removeWidget(self.button_pause)
        # self.grid_layout.addWidget(self.button_continue, 4, 3, 2, 2)
        # print('x')

    def button_continue_was_clicked(self):
        self.myGraph.start_plot_processing()
        self.button_start.setEnabled(False)
        self.button_stop.setEnabled(True)
        self.button_pause.setEnabled(True)
        self.button_continue.setEnabled(False)
        # self.grid_layout.removeWidget(self.button_continue)
        # self.grid_layout.addWidget(self.button_pause, 4, 3, 2, 2)
        # print('y')




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FTS_Main()
    window.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        print("Closing Window...")

