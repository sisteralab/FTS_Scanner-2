import sys

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QGridLayout
)


from Lock_In_Stream_Wid import LockInWidget
from Lock_Time_Control import Lock_Time_Control
from Lock_Sens_Control import Lock_Sens_Control
from Lock_Grap_Control import Lock_Grap_Control

class Lock_In_830(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(LockInWidget(self), 0, 0)
        self.layout.addWidget(Lock_Time_Control(self), 1, 0)
        self.layout.addWidget(Lock_Sens_Control(self), 1, 1)
        self.layout.addWidget(Lock_Grap_Control(self), 0, 1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Lock_In_830()
    window.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        print("Closing Window...")
