import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
)


class Stream(QtCore.QObject):
    newText = QtCore.pyqtSignal(str)

    def write(self, text):
        self.newText.emit(str(text))

class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(50, 50, 500, 300)
        self.setWindowTitle("PyQT tuts!")
        self.setWindowIcon(QtGui.QIcon('pythonlogo.png'))
        self.home()

        sys.stdout = Stream(newText=self.onUpdateText)

    def onUpdateText(self, text):
        cursor = self.process.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.process.setTextCursor(cursor)
        self.process.ensureCursorVisible()

    def __del__(self):
        sys.stdout = sys.__stdout__

    def home(self):

        w = QWidget()
        self.setCentralWidget(w)
        lay = QtGui.QVBoxLayout(w)
        btn = QtGui.QPushButton("Generate")
        btn.clicked.connect(self.TextFSM)

        self.process  = QtGui.QTextEdit()
        self.process.moveCursor(QtGui.QTextCursor.Start)
        self.process.ensureCursorVisible()
        self.process.setLineWrapColumnOrWidth(500)
        self.process.setLineWrapMode(QtGui.QTextEdit.FixedPixelWidth)

        lay.addWidget(btn)
        lay.addWidget(self.process)

        self.show()



def run():
    app = QApplication(sys.argv)
    GUI = Window()
    sys.exit(app.exec())


run()