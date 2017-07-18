#!/usr/bin/env python3
import can
import atexit

# PCAN
interface = 'pcan'
channel = 'PCAN_USBBUS1'

# pican
# interface = 'can1'
# channel = 'socketcan_native'

bus = can.interface.Bus(channel=channel, bustype=interface)
atexit.register(bus.shutdown)
while 1:
    try:
        print(bus.recv())
    except KeyboardInterrupt:
        print("Terminating")
        break
