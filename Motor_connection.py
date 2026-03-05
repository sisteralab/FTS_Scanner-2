import os
import sys
from Connection_Test import Test_Window
from Variable_data import VARIABLES


address, pyximc = Test_Window.ximc_check(VARIABLES.XIMC_Path)

def info(lib, device_id):
    print("\nИнформация о моторах")
    x_device_information = device_information_t()
    result = lib.get_device_information(device_id, byref(x_device_information))
    print("Result: " + repr(result))
    if result == Result.Ok:
        print("Детали о моторах:")
        print(" Производитель: " +
              repr(string_at(x_device_information.Manufacturer).decode()))
        print(" Производитель Id: " +
              repr(string_at(x_device_information.ManufacturerId).decode()))
        print(" Описание продукта: " +
              repr(string_at(x_device_information.ProductDescription).decode()))
        print(" Major: " + repr(x_device_information.Major))
        print(" Minor: " + repr(x_device_information.Minor))
        print(" Release: " + repr(x_device_information.Release))

def motor_info(lib, device_id):
    print("\nGet motor info")
    x_motor = motor_information_t()
    result = lib.get_motor_information(device_id, byref(x_motor))
    print("Result: " + repr(result))
    if result == Result.Ok:
        print("Motor information:")
        print(" Motor: " +
              repr(string_at(x_motor.Manufacturer).decode()))

def serial(pyximc, device_id):
    print("\nСерийный номер")
    x_serial = pyximc.c_uint()
    # print (device_id, pyximc.byref(x_serial))
    result = pyximc.lib.get_serial_number(device_id, pyximc.byref(x_serial))
    # print (result)
    if result == pyximc.Result.Ok:
        print("Номер: " + repr(x_serial.value))

def status(pyximc, device_id):
    print("\nСтатус")
    x_status = pyximc.status_t()
    result = pyximc.lib.get_status(device_id, pyximc.byref(x_status))
    print("Result: " + repr(result))
    if result == pyximc.Result.Ok:
        print("Status.Ipwr: " + repr(x_status.Ipwr))
        print("Status.Upwr: " + repr(x_status.Upwr))
        print("Status.Iusb: " + repr(x_status.Iusb))
        print("Status.Flags: " + repr(hex(x_status.Flags)))
        x_status.GPIOFlags = pyximc.GPIOFlags.STATE_RIGHT_EDGE
        result = pyximc.lib.get_status(device_id, pyximc.byref(x_status))
        print("Status right edge: " + repr(result))
        x_status.GPIOFlags = pyximc.GPIOFlags.STATE_LEFT_EDGE
        result = pyximc.lib.get_status(device_id, pyximc.byref(x_status))
        print("Status left edge: " + repr(result))

def set_microstep_mode(lib, device_id):
    print("\nSet microstep mode to 256")
    # Create engine settings structure
    eng = engine_settings_t()
    # Get current engine settings from controller
    result = lib.get_engine_settings(device_id, byref(eng))
    # Print command return status. It will be 0 if all is OK
    print("Read command result: " + repr(result))
    # Change MicrostepMode parameter to MICROSTEP_MODE_FRAC_256
    # (use MICROSTEP_MODE_FRAC_128, MICROSTEP_MODE_FRAC_64 ... for other microstep modes)
    eng.MicrostepMode = MicrostepMode.MICROSTEP_MODE_FRAC_256
    # Write new engine settings to controller
    result = lib.set_engine_settings(device_id, byref(eng))
    # Print command return status. It will be 0 if all is OK
    print("Write command result: " + repr(result))

def get_position(pyximc, device_id):
    print("\nСчитать позицию")
    x_pos = pyximc.get_position_t()
    result = pyximc.lib.get_position(device_id, pyximc.byref(x_pos))
    print("Result: " + repr(result))
    if result == pyximc.Result.Ok:
        print("-------------------------------------------------")
        print("Текущая позиция: {0} шагов, {1} микрошагов".format(x_pos.Position, x_pos.uPosition))
        print("-------------------------------------------------")
    return x_pos.Position, x_pos.uPosition

def set_position(lib, device_id):
    x_pos = get_position_t()
    result = lib.get_position(device_id, byref(x_pos))
    if result == Result.Ok:
        print("-------------------------------------------------")
        print("Ввести новую позицию Шагов")
        x_pos.Position = int(input())
        print("Ввести новую позицию Микрошагов")
        x_pos.uPosition = int(input())
        print("Новая позиция: {0} шагов, {1} микрошагов".format(x_pos.Position, x_pos.uPosition))
        print("-------------------------------------------------")
    return x_pos.Position, x_pos.uPosition

def get_speed(lib, device_id):
    print("\nСчитать скорость")
    # Create move settings structure
    mvst = move_settings_t()
    # Get current move settings from controller
    result = lib.get_move_settings(device_id, byref(mvst))
    # Print command return status. It will be 0 if all is OK
    print("Read command result: " + repr(result))
    print("-------------------------------------------------")
    print("Текущая скорость: ")
    print(mvst.Speed)
    print("-------------------------------------------------")
    return mvst.Speed

def set_speed(lib, device_id, speed):
    print("\nSet speed")
    # Create move settings structure
    mvst = move_settings_t()
    # Get current move settings from controller
    result = lib.get_move_settings(device_id, byref(mvst))
    # Print command return status. It will be 0 if all is OK
    print("Read command result: " + repr(result))
    print("-------------------------------------------------")
    print("Текущая скорость: ")
    print(speed)
    print("Установить новую скорость: ")
    speed = int(input())
    while (speed <= 0) or (speed >= 1001):
        print("Скорость не может быть меньше 0 или больше 1000, установите новую скорость: ")
        speed = int(input())
    print("-------------------------------------------------")
    print("The speed was equal to {0}. We will change it to {1}".format(mvst.Speed, speed))
    # Change current speed
    mvst.Speed = int(speed)
    # Write new move settings to controller
    result = lib.set_move_settings(device_id, byref(mvst))
    # Print command return status. It will be 0 if all is OK
    print("Write command result: " + repr(result))

def move(lib, device_id, distance, udistance):
    print("\nGoing to {0} steps, {1} microsteps".format(distance, udistance))
    result = lib.command_move(device_id, distance, udistance)
    print("Result: " + repr(result))

def move_left(lib, device_id):
    print("\nGoing to left edge")
    result = lib.command_left(device_id)
    print("Result: " + repr(result))

def move_right(lib, device_id):
    print("\nGoing to right edge")
    result = lib.command_right(device_id)
    print("Result: " + repr(result))

def delta_move(lib, device_id, distance, udistance):
    print("\nMove to {0} steps, {1} microsteps".format(distance, udistance))
    result = lib.command_movr(device_id, distance, udistance)
    print("Result: " + repr(result))

def s_delta_move(lib, device_id, distance, udistance):
    lib.command_movr(device_id, distance, udistance)

def wait_for_stop(lib, device_id, interval):
    print("\nWaiting for stop")
    result = lib.command_wait_for_stop(device_id, interval)
    print("Result: " + repr(result))

def s_wait_for_stop(lib, device_id, interval):
    lib.command_wait_for_stop(device_id, interval)

def get_home(lib, device_id):
    print("\nНайти домашнюю позицию")
    getme = home_settings_t()
    result = lib.get_home_settings(device_id, byref(getme))
    print("Read command result: " + repr(result))
    if result == Result.Ok:
        lib.command_homezero(device_id)
        get_position(lib, device_id)

def edges(lib, device_id):
    print("\nУстановить границы")
    egs = pyximc.edges_settings_t()
    result = lib.get_edges_settings(device_id, pyximc.byref(egs))
    print("Read command result: " + repr(result))
    egs.BorderFlags = pyximc.BorderFlags.BORDERS_SWAP_MISSET_DETECTION
    result = lib.set_edges_settings(device_id, pyximc.byref(egs))
    print("Write command result: " + repr(result))

def get_edge(lib, device_id):
    print("\nGet edges info")
    print(device_id)
    x_edge = pyximc.edges_settings_t()
    result = pyximc.lib.get_edges_settings(device_id, pyximc.byref(x_edge))
    print("Result: " + repr(result))
    if result == pyximc.Result.Ok:
        print("Right Edge: " + repr(x_edge.RightBorder))
        print("uRight Edge: " + repr(x_edge.uRightBorder))
        print("Left Edge: " + repr(x_edge.LeftBorder))
        print("uLeft Edge: " + repr(x_edge.uLeftBorder))

def stop(lib, device_id):
    print("\nStart Stop")
    result = lib.command_stop(device_id)
    print("Result: " + repr(result))

def set_zero(lib, device_id):
    print("\nSet zero Position")
    result = lib.command_zero(device_id)
    print("Result: " + repr(result))

def start_p(lib, device_id):
    info(lib, device_id)
    motor_info(lib, device_id)
    serial(lib, device_id)
    status(lib, device_id)
    set_microstep_mode(lib, device_id)
    get_edge(lib, device_id)
    get_position(lib, device_id)
    get_speed(lib, device_id)

def Connect_test (pyximc):
    pyximc.lib.set_bindy_key(os.path.join(address, "win32", "keyfile.sqlite").encode("utf-8"))
    probe_flags = pyximc.EnumerateFlags.ENUMERATE_PROBE + pyximc.EnumerateFlags.ENUMERATE_NETWORK
    # enum_hints = b"addr=192.168.0.1,172.16.2.3"
    devenum = pyximc.lib.enumerate_devices(probe_flags)
    # print (devenum)
    print('\nПроверка мотора')
    # print("Motor device enum handle: " + repr(devenum))
    # print("Motor device enum handle type: " + repr(type(devenum)))
    dev_count = pyximc.lib.get_device_count(devenum)
    # print (dev_count)
    if dev_count == 0:
        print("\nClosing, not found Motors")
        sys.exit([dev_count])
        print("Done")
    print("Device count: " + repr(dev_count))

    controller_name = pyximc.controller_name_t()
    for dev_ind in range(0, dev_count):
        enum_name = pyximc.lib.get_device_name(devenum, dev_ind)
        result = pyximc.lib.get_enumerate_device_controller_name(devenum, dev_ind, pyximc.byref(controller_name))
        if result == pyximc.Result.Ok:
            print("Enumerated device #{} name (port name): ".format(dev_ind) + repr(enum_name) + ". Friendly name: " + repr(
                controller_name.ControllerName) + ".")

    open_name = None
    if len(sys.argv) > 1:
        open_name = sys.argv[1]
    elif dev_count > 0:
        open_name = pyximc.lib.get_device_name(devenum, 0)
    elif sys.version_info >= (3, 0):
        tempdir = tempfile.gettempdir() + "/testdevice.bin"
        if os.altsep:
            tempdir = tempdir.replace(os.sep, os.altsep)
        uri = urllib.parse.urlunparse(urllib.parse.ParseResult(scheme="file", \
                                                               netloc=None, path=tempdir, params=None, query=None,
                                                               fragment=None))
        open_name = re.sub(r'^file', 'xi-emu', uri).encode()

    if not open_name:
        exit(1)

    if type(open_name) is str:
        open_name = open_name.encode()

    print("\nOpen device " + repr(open_name))
    device_id = pyximc.lib.open_device(open_name)
    print("Device id: " + repr(device_id))
    # print(device_id)
    return device_id

device_id = Connect_test(pyximc)
# serial(pyximc, device_id)
# status(pyximc, device_id)
get_position(pyximc, device_id)
# get_position(pyximc, device_id)