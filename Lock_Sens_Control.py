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
from Com_List import SR_830
rm = pyvisa.ResourceManager()
SR830 = rm.open_resource(
    VARIABLES.Lock_In_GPIB, write_termination="\n", read_termination="\n"
)

class Lock_Sens_Control(QWidget):
    def __init__(self, *args, **kwargs):
        super(Lock_Sens_Control, self).__init__(*args, **kwargs)
        self.SensLabel = QLabel("Sens Constant: ")
        self.button_Up = QPushButton("⇑")
        self.button_Down = QPushButton("⇓")
        self.button_update = QPushButton("Update")
        self.SensVar = QLabel(self)
        self.SensVar.setText("None")
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.SensLabel, 0, 0)
        self.layout.addWidget(self.SensVar, 0, 1)
        self.layout.addWidget(self.button_Up, 1, 0)
        self.layout.addWidget(self.button_Down, 1, 1)
        self.layout.addWidget(self.button_update, 2, 0, 1, 2)
        self.button_Up.clicked.connect(self.the_button_Up_was_clicked)
        self.button_Down.clicked.connect(self.the_button_Down_was_clicked)
        self.button_update.clicked.connect(self.the_button_update_was_clicked)

    def the_button_update_was_clicked(self):
        VARIABLES.Sens_Const = SR830.query(SR_830.OPERATION_ASK_SENSITIVITY)
        self.SensVar.setText(SR_830.SENS_CONSTANTS_DIC[int(VARIABLES.Sens_Const)])
        # print(int(VARIABLES.Sens_Const))

    def the_button_Up_was_clicked(self):
        VARIABLES.Sens_Const = SR830.query(SR_830.OPERATION_ASK_SENSITIVITY)
        SR830.write(SR_830.OPERATION_SET_SENSITIVITY + " " + str(int(VARIABLES.Sens_Const)+1))
        VARIABLES.Sens_Const = SR830.query(SR_830.OPERATION_ASK_SENSITIVITY)
        self.SensVar.setText(SR_830.SENS_CONSTANTS_DIC[int(VARIABLES.Sens_Const)])

    def the_button_Down_was_clicked(self):
        VARIABLES.Sens_Const = SR830.query(SR_830.OPERATION_ASK_SENSITIVITY)
        SR830.write(SR_830.OPERATION_SET_SENSITIVITY + " " + str(int(VARIABLES.Sens_Const) - 1))
        VARIABLES.Sens_Const = SR830.query(SR_830.OPERATION_ASK_SENSITIVITY)
        self.SensVar.setText(SR_830.SENS_CONSTANTS_DIC[int(VARIABLES.Sens_Const)])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # app.setStyleSheet("""QWidget {font-size: 14px;}""")
    myApp = Lock_Sens_Control()
    myApp.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        print("Closing Window...")

