#!/usr/bin/env python3
import can
import atexit
import sys
from itertools import cycle

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
to_query = cycle([0xc, 0xb, 0xd])
print("Querying OBD")
while 1:
    try:
        msg = can.Message(arbitration_id=0x7df, data=[2, 1, next(to_query), 0,0,0,0,0], extended_id=0)
        print("S>", msg)
        bus.send(msg)
        print("R>", bus.recv())
    except KeyboardInterrupt:
        print("Terminating")
        break
