import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QFormLayout,
    QGridLayout,
    QTabWidget,
    QLineEdit,
    QDateEdit,
    QPushButton,
)
# from Test_Item import Test_Window
from Wid_connection import Ximc_app
from LockIn_Connection import Visa_lock_in_app
from Dialog_Widget import Example
from Motor_Wid import Motor_app
from Lock_In_Par_Control import Lock_In_830
from FTS_Main_Widget import FTS_Main


class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("FTS Scanner")
        self.main_layout = QGridLayout()
        self.setLayout(self.main_layout)
        self.tab = QTabWidget()

        # Tab connection
        self.data_page = QWidget()
        self.layout_data_page = QFormLayout()
        self.data_page.setLayout(self.layout_data_page)
        self.layout_data_page.addWidget(Example("GPIB Lock-In address", "Lock_In_GPIB"))
        self.layout_data_page.addWidget(Example("FTS XIMC Motor address", "Motor_name"))
        self.layout_data_page.addWidget(Example("Path to XIMC library", "XIMC_Path"))
        self.layout_data_page.addWidget(Example("IP Prologix address", "Prologix_IP"))


        self.connect_page = QWidget()
        self.layout_connect_page = QFormLayout()
        self.connect_page.setLayout(self.layout_connect_page)
        self.layout_connect_page.addWidget(Ximc_app(self))
        self.layout_connect_page.addWidget((Visa_lock_in_app(self)))

        self.main_page = QWidget()
        self.layout_main_page = QGridLayout()
        self.main_page.setLayout(self.layout_main_page)
        # Test_Window.plot_window(self)
        # self.layout_main_page.addWidget(self.plt, 0, 1)
        self.layout_main_page.addWidget(Motor_app(self), 0, 0)
        self.layout_main_page.addWidget(Lock_In_830(self), 0, 1)

        self.console_page = QWidget()
        self.layout_console_page = QFormLayout()
        self.console_page.setLayout(self.layout_console_page)

        self.FTS_page = QWidget()
        self.layout_FTS_page = QFormLayout()
        self.FTS_page.setLayout(self.layout_FTS_page)
        self.layout_FTS_page.addWidget(FTS_Main(self))

        self.tab.addTab(self.connect_page, "Connection")
        self.tab.addTab(self.main_page, "Device Control")
        self.tab.addTab(self.data_page, "Input Data")
        self.tab.addTab(self.console_page, "Console")
        self.tab.addTab(self.FTS_page, "FTS Measurement")

        self.main_layout.addWidget(self.tab, 0, 0, 2, 1)

    def closeEvent(self, event):
        for window in QApplication.topLevelWidgets():
            window.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        print("Closing Window...")
