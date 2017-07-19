#!/usr/bin/env python3
import can
import atexit
import sys


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

bus = can.interface.Bus(channel=channel, bustype=interface)
atexit.register(bus.shutdown)
while 1:
    try:
        print(bus.recv())
    except KeyboardInterrupt:
        print("Terminating")
        break
