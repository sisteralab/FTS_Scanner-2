class SR_830:
    """
    ####################################################################################################################
    List of device specific commands and parameters based on
    the programming section (5) of the manual (Starting at page 85)
    ####################################################################################################################
    """

    # general operations
    OPERATION_IDENTIFY = "*IDN?"
    OPERATION_RESET = "*RST"
    OPERATION_CLEAR = "*CLS"

    # operations concerning communication with the computer
    OPERATION_SEND_RESPONSE_TO_RS232 = "OUTX 0"
    OPERATION_SEND_RESPONSE_TO_GPIB = "OUTX 1"

    # operations / parameters for controlling the oscillator
    OPERATION_SET_TO_INTERNAL_REFERENCE = "FMOD 1"
    OPERATION_SET_TO_EXTERNAL_REFERENCE = "FMOD 0"
    OPERATION_SET_INTERNAL_REFERENCE_FREQUENCY = "FREQ"
    UPPER_FREQ_LIMIT = 102000  # Limit in Hz based on the specifications of the SR830
    LOWER_FREQ_LIMIT = 0.001

    OPERATION_SINE_OUTPUT_LEVEL = "SLVL"
    LOWER_SINE_OUTPUT_LEVEL = (
        0.004  # Limit in Volts based on the specifications of the SR830
    )
    UPPER_SINE_OUTPUT_LEVEL = 5

    # operations that define the input characteristics
    OPERATION_SET_INPUT_TO_A = "ISRC 0"
    OPERATION_SET_INPUT_TO_A_MINUS_B = "ISRC 1"
    OPERATION_SET_INPUT_SHIELD_TO_FLOATING = "IGND 0"
    OPERATION_SET_INPUT_SHIELD_TO_GROUND = "IGND 1"
    OPERATION_SET_INPUT_COUPLING_AC = "ICPL 0"
    OPERATION_SET_INPUT_COUPLING_DC = "ICPL 1"

    OPERATION_DISABLE_LINE_FILTER = "ILIN 0"
    OPERATION_ENABLE_LINE_FILTER = "ILIN 3"

    # sensitivity commands
    OPERATION_SET_SENSITIVITY = "SENS"
    OPERATION_ASK_SENSITIVITY = "SENS?"
    # Available sensitivity ranges in volts
    SENSITIVITY_RANGES = (
        2e-9,
        5e-9,
        10e-9,
        20e-9,
        50e-9,
        100e-9,
        200e-9,
        500e-9,
        1000e-9,
        2e-6,
        5e-6,
        10e-6,
        20e-6,
        50e-6,
        100e-6,
        200e-6,
        500e-6,
        1000e-6,
        2e-3,
        5e-3,
        10e-3,
        20e-3,
        50e-3,
        100e-3,
        200e-3,
        500e-3,
        1000e-3,
    )

    OPERATION_SET_RESERVE_MODE_HIGH_RESERVE = "RMOD 0"
    OPERATION_SET_RESERVE_MODE_NORMAL = "RMOD 1"
    OPERATION_SET_RESERVE_MODE_LOW_NOISE = "RMOD 2"

    OPERATION_SET_TIME_CONSTANT = "OFLT"
    OPERATION_ASK_TIME_CONSTANT = "OFLT?"
    # Available time constants in seconds
    TIME_CONSTANTS = (
        10e-6,
        30e-6,
        100e-6,
        300e-6,
        1e-3,
        3e-3,
        10e-3,
        30e-3,
        100e-3,
        300e-3,
        1,
        3,
        10,
        30,
        100,
        300,
        1e3,
        3e3,
        10e3,
        30e3,
    )

    TIME_CONSTANTS_DIC = {
        0: "10 us",
        1: "30 us",
        2: "100 us",
        3: "300 us",
        4: "1 ms",
        5: "3 ms",
        6: "10 ms",
        7: "30 ms",
        8: "100 ms",
        9: "300 ms",
        10: "1 s",
        11: "3 s",
        12: "10 s",
        13: "30 s",
        14: "100 s",
        15: "300 s",
        16: "1 ks",
        17: "3 ks",
        18: "10 ks",
        19: "30 ks",
    }

    SENS_CONSTANTS_DIC = {
        0: "2 nV/fA",
        1: "5 nV/fA",
        2: "10 nV/fA",
        3: "20 nV/fA",
        4: "50 nV/fA",
        5: "100 nV/fA",
        6: "200 nV/fA",
        7: "500 nV/fA",
        8: "1 μV/pA",
        9: "2 μV/pA",
        10: "5 μV/pA",
        11: "10 μV/pA",
        12: "20 μV/pA",
        13: "50 μV/pA",
        14: "100 μV/pA",
        15: "200 μV/pA",
        16: "500 μV/pA",
        17: "1 mV/nA",
        18: "2 mV/nA",
        19: "5 mV/nA",
        20: "10 mV/nA",
        21: "20 mV/nA",
        22: "50 mV/nA",
        23: "100 mV/nA",
        24: "200 mV/nA",
        25: "500 mV/nA",
        26: "1 V/μA",
    }

    OPERATION_LOW_PASS_FILTER_SLOPE = "OFSL"
    # Available filters slopes in dB/oct
    FILTER_SLOPES = (6, 12, 18, 24)

    # display commands
    OPERATION_SET_DISPLAY_CH1_TO_X = "DDEF 1, 0, 0"
    OPERATION_SET_DISPLAY_CH1_TO_R = "DDEF 1, 1, 0"
    OPERATION_SET_DISPLAY_CH2_TO_Y = "DDEF 2, 0, 0"
    OPERATION_SET_DISPLAY_CH2_TO_PHI = "DDEF 2, 1, 0"

    # auto functions
    OPERATION_AUTO_GAIN = "AGAN"
    OPERATION_AUTO_RESERVE = "ARSV"
    OPERATION_AUTO_PHASE = "APHS"
    OPERATION_AUTO_OFFSET_X = "AOFF 1"
    OPERATION_AUTO_OFFSET_Y = "AOFF 2"
    OPERATION_AUTO_OFFSET_R = "AOFF 3"

    # data transfer commands
    READ_X = "OUTP? 1"
    READ_Y = "OUTP? 2"
    READ_R = "OUTP? 3"
    READ_PHI = "OUTP? 4"

    # snap commands read data synchronously (important if time constant is very short)
    READ_SNAP_X_Y_R_PHI = "SNAP? 1, 2, 3, 4"
