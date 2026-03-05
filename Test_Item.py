import sys


from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.uic import loadUi

# from PyQt5 import QtCore, QtGui, QtWidgets
# from PyQt5.uic import loadUi
# from PyQt5.Qt import *


# class New(QThread):
class New(QWidget):  # !!! QWidget
    def __init__(self, parent=None):
        super(New, self).__init__(parent)
        self.parent = parent

    def foo(self):
        ''' Функция получает значение из spinBox,
        прибавляет единичку и результат выводит в окно label '''
        value = self.parent.spinBox.value()
        value = value + 1
        self.parent.label.setText(f"{value}")


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi("q1510511_Test.ui", self)

        self.label.setText("Привет")
        self.spinBox.valueChanged.connect(self.getValue)

        # +++ vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        self.new = New(self)

    def getValue(self, value):
        self.new.foo()


# +++ ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
