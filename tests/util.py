import sys


def get_args():
    print(sys.argv)
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == 'pcan':
            # PCAN
            interface = 'pcan'
            channel = 'PCAN_USBBUS1'
        elif arg in ['can1', 'can0']:
            # pican
            channel = arg
            interface = 'socketcan_native'
        else:
            exit("Invalid CAN bus specified")
    else:
        channel = 'can0'
        interface = 'socketcan_native'
    return interface, channel
