import pyvisa
import sys
from Variable_data import VARIABLES
from Com_List import SR_830


def main():
    rm = pyvisa.ResourceManager()
    # print(rm.list_resources())
    SR830 = rm.open_resource(
        VARIABLES.Lock_In_GPIB, write_termination="\n", read_termination="\n"
    )
    print("Say name: " + SR830.query(SR_830.OPERATION_IDENTIFY))
    # SR830.query("SENS?")
    VARIABLES.Sens_Const = SR830.query(SR_830.OPERATION_ASK_SENSITIVITY)
    VARIABLES.Time_Const = SR830.query(SR_830.OPERATION_ASK_TIME_CONSTANT)
    # print(VARIABLES.Time_Const)
    # print(SR830)


if __name__ == "__main__":
    main()
