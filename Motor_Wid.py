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
from Connection_Test import Test_Window
from Motor_class import Motor
from Position_Wid import MonitorWidget

address, pyximc = Test_Window.ximc_check(VARIABLES.XIMC_Path)

open_name = VARIABLES.Motor_name
device = Motor(open_name)



class Motor_app(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.button_Check_l = QLabel("Checking Motor Position")
        self.button_Plus_l = QLabel("+100 Motor Position")
        self.button_Minus_l = QLabel("-100 Motor Position")

        self.button_Check = QPushButton("Check!")
        self.button_Plus = QPushButton("+100!")
        self.button_Minus = QPushButton("-100!")
        self.button_stop = QPushButton("STOP")
        self.button_right = QPushButton("Go to Right")
        self.button_left = QPushButton("Go to Left")
        self.button_Zero = QPushButton("Set Zero")
        self.button_Home = QPushButton("Find Home")
        self.button_Move_to = QPushButton("Move to")
        self.button_Shift_to = QPushButton("Shift to")
        self.Input_L_Move_To = QLineEdit(self)
        self.Input_S_Move_To = QLineEdit(self)
        self.Input_L_Shift_To = QLineEdit(self)
        self.Input_S_Shift_To = QLineEdit(self)

        self.button_Check.clicked.connect(self.the_button_was_clicked)
        self.button_Plus.clicked.connect(self.the_button_was_clicked_p)
        self.button_Minus.clicked.connect(self.the_button_was_clicked_m)
        self.button_stop.clicked.connect(self.the_button_was_clicked_s)
        self.button_right.clicked.connect(self.the_button_was_clicked_r)
        self.button_left.clicked.connect(self.the_button_was_clicked_l)
        self.button_Zero.clicked.connect(self.the_button_was_clicked_z)
        self.button_Home.clicked.connect(self.the_button_was_clicked_h)
        self.button_Move_to.clicked.connect(self.the_button_was_clicked_mto)
        self.button_Shift_to.clicked.connect(self.the_button_was_clicked_sto)

        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.Input_L_Move_To.setText('0')
        self.Input_S_Move_To.setText('0')
        self.Input_L_Shift_To.setText('0')
        self.Input_S_Shift_To.setText('0')
        self.layout.addWidget(MonitorWidget(self), 8, 0, 2, 2)
        self.layout.addWidget(self.button_Check_l, 0, 0, 1, 4)
        self.layout.addWidget(self.button_Check, 0, 4, 1, 2)
        self.layout.addWidget(self.button_Plus_l, 1, 0, 1, 4)
        self.layout.addWidget(self.button_Plus, 1, 4, 1, 2)
        self.layout.addWidget(self.button_Minus_l, 2, 0, 1, 4)
        self.layout.addWidget(self.button_Minus, 2, 4, 1, 2)
        self.layout.addWidget(self.Input_L_Move_To, 3, 0, 1, 2)
        self.layout.addWidget(self.Input_S_Move_To, 3, 2, 1, 2)
        self.layout.addWidget(self.button_Move_to, 3, 4, 1, 2)
        self.layout.addWidget(self.Input_L_Shift_To, 4, 0, 1, 2)
        self.layout.addWidget(self.Input_S_Shift_To, 4, 2, 1, 2)
        self.layout.addWidget(self.button_Shift_to, 4, 4, 1, 2)
        self.layout.addWidget(self.button_left, 5, 0, 1, 2)
        self.layout.addWidget(self.button_stop, 5, 2, 1, 2)
        self.layout.addWidget(self.button_right, 5, 4, 1, 2)
        self.layout.addWidget(self.button_Zero, 6, 0, 1, 6)
        self.layout.addWidget(self.button_Home, 7, 0, 1, 6)

    def the_button_was_clicked(self):
        # MyApp.button_count += 1
        print("---------------")
        print("Device id: " + repr(device.device_id))
        device.get_position()
        # Motor_connection.get_position(pyximc, device_id)
        self.button_Check.setText(str(device.get_position()))

    def the_button_was_clicked_p(self):
        # MyApp.button_count += 1
        # open_name = "xi-com:\\\\.\\COM4"
        # device = Motor()
        print("---------------")
        print("Device id: " + repr(device.device_id))
        device.delta_move(+100, 0)
        device.wait_for_stop(100)
        device.get_position()
        self.button_Check.setText(str(device.get_position()))
        # Motor_connection.get_position(pyximc, device_id)
        # self.button.setText(str(device.get_position()))

    def the_button_was_clicked_m(self):
        # open_name = "xi-com:\\\\.\\COM4"
        # device = Motor()
        print("---------------")
        print("Device id: " + repr(device.device_id))
        device.delta_move(-100, 0)
        device.wait_for_stop(100)
        self.button_Check.setText(str(device.get_position()))


    def the_button_was_clicked_s(self):
        print("\nStart Stop")
        device.stop()
        device.wait_for_stop(100)
        self.button_Check.setText(str(device.get_position()))


    def the_button_was_clicked_r(self):
        print("\nStart Stop")
        device.move_right()
        # device.wait_for_stop(100)
        # device.get_position()

    def the_button_was_clicked_l(self):
        print("\nStart Stop")
        device.move_left()
        # device.wait_for_stop(100)
        # device.get_position()

    def the_button_was_clicked_z(self):
        device.set_zero()
        self.button_Check.setText(str(device.get_position()))


    def the_button_was_clicked_h(self):
        device.home()
        self.button_Check.setText(str(device.get_position()))

    def the_button_was_clicked_mto(self):
        TextMPos = self.Input_L_Move_To.text()
        TextuMPos = self.Input_S_Move_To.text()
        if TextMPos is '' or TextuMPos is '':
            self.button_Check.setText(str(device.get_position()))
            # print (1)
        else:
            device.move(TextMPos, TextuMPos)
            # print (0)

    def the_button_was_clicked_sto(self):
        TextSPos = self.Input_L_Shift_To.text()
        TextuSPos = self.Input_S_Shift_To.text()
        if TextSPos is '' or TextuSPos is '':
            self.button_Check.setText(str(device.get_position()))
            # print (1)
        else:
            device.delta_move(TextSPos, TextuSPos)
            # print(TextSPos, TextuSPos)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("""QWidget {font-size: 14px;}""")
    myApp = Motor_app()
    myApp.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        print("Closing Window...")