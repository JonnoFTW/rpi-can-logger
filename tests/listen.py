#!/usr/bin/env python3
import can
import atexit

bus = can.interface.Bus(channel='can1', bustype='socketcan_native')
atexit.register(bus.shutdown)
while 1:
    try:
        print(bus.recv())
    except KeyboardInterrupt:
        print("Terminating")
        break
