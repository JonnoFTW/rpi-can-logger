#!/usr/bin/env python3
import sys
import can
import atexit
import time

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
print("Sending on ", channel, interface)

i = 0

while 1:
    msg = can.Message(data=[0x42,0,0,0,0,0,i,i], extended_id=0, arbitration_id=0x7e8)
    print(msg)
    bus.flush_tx_buffer()
    bus.send(msg)
    i += 1
    i %= 0xff
    time.sleep(0.5)
