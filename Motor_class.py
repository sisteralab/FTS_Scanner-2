import ctypes
from ctypes import *
import time
import os
import sys
import re
import tempfile
from Connection_Test import Test_Window
from Variable_data import VARIABLES

address, pyximc = Test_Window.ximc_check(VARIABLES.XIMC_Path)
# sys.path.append("./libximc")
# from libximc import pyximc

if sys.version_info >= (3,0):
    import urllib.parse
    try:
        from pyximc import *
    except ImportError as err:
        print ("Can't import pyximc module.\
               The most probable reason is that \
               you haven't copied pyximc.py to the working directory.\
               See developers' documentation for details.")
        exit()
    except OSError as err:
        print ("Can't load libximc library.\
               Please add all shared libraries to the appropriate places \
               (next to pyximc.py on Windows). \
               It is decribed in detailes in developers' documentation.")
        exit()

print("Library loaded")
sbuf = create_string_buffer(64)
lib.ximc_version(sbuf)
# print("Library version: " + sbuf.raw.decode())

DEBUG = False
def log(s):
    if DEBUG:
        print(s)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Motor(metaclass=Singleton):
    def __init__(self, device_name = None):
        self.lib = lib
        self.device_id = self.open_device(device_name)

    def motor_info(self):
        print("\nGet motor info")
        x_motor = motor_information_t()
        result = self.lib.get_motor_information(self.device_id, byref(x_motor))
        print("Result: " + repr(result))
        if result == Result.Ok:
            print("Motor information:")
            print(" Motor: " +
                  repr(string_at(x_motor.Manufacturer).decode()))

    def serial(self):
        print("\nСерийный номер")
        x_serial = c_uint()
        result = self.lib.get_serial_number(self.device_id, byref(x_serial))
        if result == Result.Ok:
            print("Номер: " + repr(x_serial.value))

    def home(self):
        log("\nMoving home")
        result = self.lib.command_homezero(self.device_id)
        log("Result: " + repr(result))

    def forward(self, distance):
        log("\nShifting")
        log(distance)
        dis = ctypes.c_int()
        dis.value = int(distance)
        result = self.lib.command_movr(self.device_id, dis, 0)
        log("Result: " + repr(result))

    def backward(self, distance):
        log("\nShifting")
        shift = ctypes.c_int()
        shift.value = 0 - int(distance) # in oppsite direction
        result = self.lib.command_movr(self.device_id, shift, 0)
        log("Result: " + repr(result))

    def moveforward(self):
        log("\nMoving forward")
        result = self.lib.command_right(self.device_id)
        log("Result: " + repr(result))

    def movebackward(self):
        log("\nMoving backward")
        result = self.lib.command_left(self.device_id)
        log("Result: " + repr(result))

    def set_zero(self):
        print("\nSet zero Position")
        result = self.lib.command_zero(self.device_id)
        print("Result: " + repr(result))

    def move(self, position, uposition):
        log("\nMoving position")
        pos = ctypes.c_int()
        pos.Position = int(position)
        pos.uPosition = int(uposition)
        result = self.lib.command_move(self.device_id, pos.Position, pos.uPosition)
        log("Result: " + repr(result))

    def move_left(self):
        print("\nGoing to left edge")
        result = self.lib.command_left(self.device_id)
        print("Result: " + repr(result))

    def move_right(self):
        print("\nGoing to right edge")
        result = self.lib.command_right(self.device_id)
        print("Result: " + repr(result))

    def delta_move(self, distance, udistance):
        spos = ctypes.c_int()
        spos.Position = int(distance)
        spos.uPosition = int(udistance)
        print("\nMove to {0} steps, {1} microsteps".format(distance, udistance))
        result = self.lib.command_movr(self.device_id, spos.Position, spos.uPosition)
        print("Result: " + repr(result))

    def stop(self):
        log("\nStopping")
        result = self.lib.command_stop(self.device_id)
        log("Result: " + repr(result))

    def get_position(self):
        print("\nRead position")
        pos = get_position_t()
        result = self.lib.get_position(self.device_id, byref(pos))
        print("Result: " + repr(result))
        if result == Result.Ok:
            print("-------------------------------------------------")
            print("Текущая позиция: {0} шагов, {1} микрошагов".format(pos.Position, pos.uPosition))
            print("-------------------------------------------------")
        return pos.Position, pos.uPosition

    def set_position(self, position, uposition):
        print("\nSet position")
        pos = set_position_t()
        pos.Position = position
        pos.uPosition = uposition
        result = self.lib.set_position(self.device_id, byref(pos))
        print("Result: " + repr(result))
        if result == Result.Ok:
            print("Setting Position Done")
        return pos.Position, pos.uPosition

    def get_status_position(self):
        log("\nGet status")
        status = status_t()
        result = self.lib.get_status(self.device_id, byref(status))
        log("Result: " + repr(result))
        if result == Result.Ok:
            log("Status.CurPosition: " + repr(status.CurPosition))
        return status.CurPosition

    def get_status(self):
        log("\nGet status")
        status = status_t()
        result = self.lib.get_status(self.device_id, byref(status))
        log("Result: " + repr(result))
        if result == Result.Ok:
            log("Status.CurPosition: " + repr(status.CurPosition))

    def wait_for_stop(self, interval):
        print("\nWaiting for stop")
        result = self.lib.command_wait_for_stop(self.device_id, interval)
        print("Result: " + repr(result))

    def s_wait_for_stop(lib, device_id, interval):
        lib.command_wait_for_stop(device_id, interval)

    def mkvirtual_device(self, device_name):
        if sys.version_info < (3,0):
            print("Using virtual device needs python3!")
            exit(1)

        # use URI for virtual device when there is new urllib python3 API
        tempdir = tempfile.gettempdir() + "/" + str(device_name)+ ".bin"
        print("\ntempdir: " + tempdir)
        # "\" <-> "/"
        if os.altsep:
            tempdir = tempdir.replace(os.sep, os.altsep)

        uri = urllib.parse.urlunparse(urllib.parse.ParseResult \
                                      (scheme="file",netloc=None, path=tempdir,\
                                       params=None, query=None, fragment=None))
        # converter address to b
        open_name = re.sub(r'^file', 'xi-emu', uri).encode()
        return open_name

    def enum_device(self):
        devenum = self.lib.enumerate_devices(EnumerateFlags.ENUMERATE_PROBE, None)
        print("Device enum handle: " + repr(devenum))
        print("Device enum handle type: " + repr(type(devenum)))

        dev_count = self.lib.get_device_count(devenum)
        print("Device count: " + repr(dev_count))

        controller_name = controller_name_t()
        for dev_ind in range(0, dev_count):
            enum_name = self.lib.get_device_name(devenum, dev_ind)
            result = self.lib.get_enumerate_device_controller_name(devenum, dev_ind,
                                                                   byref(controller_name))
            if result == Result.Ok:
                print("Enumerated device #{} name (port name): ".format(dev_ind) \
                      + repr(enum_name) \
                      + ". Friendly name: " \
                      + repr(controller_name.ControllerName) \
                      + ".")

        return devenum, dev_count

    def open_device(self, open_name = None):
        devenum, dev_count = self.enum_device()
        device_id = ctypes.c_int()
        if open_name is None:
            if dev_count >0:
                open_name = self.lib.get_device_name(devenum, 0)

            else:
                open_name = self.mkvirtual_device("testdevice1")

            if type(open_name) is str:
                open_name = open_name.encode()

            print("\nOpen device " + repr(open_name))
            device_id = self.lib.open_device(open_name)
            return device_id
        else:
            if dev_count >0:
                if type(open_name) is str:
                    open_name = open_name.encode()
                print("\nOpen device " + repr(open_name))
                device_id = self.lib.open_device(open_name)
            else:
                open_name = self.mkvirtual_device(open_name)
                print("\nOpen device " + repr(open_name))
                device_id = self.lib.open_device(open_name)
            return device_id

    def close_device(self):
        result = self.lib.close_device(byref(cast(self.device_id, POINTER(c_int))))
        if result == Result.Ok:
            print("Close device " + repr(self.device_id))

def test_motor():

    # open_name = "testdevice2"
    # open_name = "xi-com:\\\\.\\COM4"
    device = Motor()
    print("---------------")
    print("Device id: " + repr(device.device_id))
    # device.open_device()
    # device.motor_info()
    # device.serial()
    # device.get_position()
    # device.set_position(100, 0)
    device.get_position()
    device.delta_move(10, 0)
    # device.delta_move(-8000, 0)
    # device.set_zero()
    device.wait_for_stop(100)
    device.get_position()

def test_singlemotor():

    # open_name = "testdevice2"
    open_name = "xi-com:\\\\.\\COM4"
    device_pytct = Motor(open_name)


    print("---------------")
    print("Device id: " + repr(device_pytct.device_id))

    # device_pytct.home()
    time.sleep(1)
    print("position: " + str(device_pytct.get_position()))

    device_pytct.set_position(1000)
    time.sleep(1)
    print("position: " + str(device_pytct.get_position()))

    device_pytct.move(1000)
    time.sleep(2)
    print("position: " + str(device_pytct.get_position()))

    device_pytct.forward(1000)
    time.sleep(1)
    print("position: " + str(device_pytct.get_position()))
    print("position: " + str(device_pytct.get_status_position()))

    print("---------------")
    device_pytct.backward(2000)
    print("position: " + str(device_pytct.get_position()))
    time.sleep(1)
    print("position: " + str(device_pytct.get_status_position()))

    device_pytct.close_device()
    print("Done")



if __name__ == '__main__':
    # Motor.motor_info(pyximc)
    test_motor()
    # test_multimotor()