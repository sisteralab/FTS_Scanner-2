import sys
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

data = 0


class Example(QWidget):
    def __init__(self, arg_input, arg_variable_name):
        super().__init__()
        self.arg_input = arg_input
        self.arg_variable_name = arg_variable_name
        self.initUI()

    @property
    def arg_variable(self):
        return getattr(VARIABLES, self.arg_variable_name)

    def initUI(self):
        self.label = self.arg_input
        self.data = self.arg_variable
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.button_label = QLabel(self.label)
        self.btn = QPushButton("Edit", self)
        # self.btn.move(20, 20)
        self.btn.clicked.connect(self.EditDialog)
        self.le = QLineEdit(self)
        # self.le.move(130, 22)
        self.le.setText(self.data)
        # self.setGeometry(300, 300, 290, 150)
        self.setWindowTitle("Input dialog")
        self.layout.addWidget(self.btn, 0, 2)
        self.layout.addWidget(self.le, 0, 1)
        self.layout.addWidget(self.button_label, 0, 0)
        # self.show()

    def EditDialog(self):
        print("Set address: " + self.le.text())
        setattr(VARIABLES, self.arg_variable_name, self.le.text())



if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = Example("Path to XIMC library", "XIMC_Path")
    Example.show()
    sys.exit(app.exec())
