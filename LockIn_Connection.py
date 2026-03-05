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
    QComboBox,
)

from Variable_data import VARIABLES
from SR830_Con_Test import main


def con_ethe():
    VARIABLES.Connection_Type_Var = 1
    # print(connect_var)


def con_visa():
    VARIABLES.Connection_Type_Var = 0
    # print(connect_var)


func_map = {"Keysight Visa": con_visa, "Prologix Ethernet": con_ethe}


class Visa_lock_in_app(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cbox_label = QLabel("Checking the connection to Lock-In")
        self.button = QPushButton("Connect Lock-In")
        self.button.clicked.connect(self.the_button_was_clicked)
        self.cbox = QComboBox()
        self.cbox.addItem("Keysight Visa")
        self.cbox.addItem("Prologix Ethernet")
        self.cbox.activated.connect(self.update)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.cbox_label, 0, 0)
        self.layout.addWidget(self.cbox, 0, 1)
        self.layout.addWidget(self.button, 0, 2)
        self.result_label = QLabel("", self)
        self.layout.addWidget(self.result_label)

    def update(self):
        func_map[self.cbox.currentText()]()
        self.result_label.setText(f"You selected {self.cbox.currentText()}")

    def the_button_was_clicked(self):
        if VARIABLES.Connection_Type_Var == 0:
            # print('x')
            main()
            # print(VARIABLES.Time_Const)
        else:
            print("y")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myApp = Visa_lock_in_app()
    myApp.show()
    try:
        sys.exit(app.exec())
    except SystemExit:
        print("Closing Window...")
