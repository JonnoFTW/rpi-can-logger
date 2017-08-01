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
print("Sniffing CAN:", bus)
for i in [0, 32, 64, 96, 128]:
    msg = can.Message(extended_id=0, data=[2, 1, i, 0, 0, 0, 0, 0], arbitration_id=0x07DF)
    bus.send(msg)
    print("S>", msg)
while 1:
    try:
        msg = bus.recv()
        #        if msg.arbitration_id in [0x7df, 0x7e8]:
        print("R>", msg)
    except KeyboardInterrupt:
        print("Terminating")
        break
