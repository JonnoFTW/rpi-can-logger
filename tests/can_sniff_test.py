#!/usr/bin/env python3
import can
import atexit

from util import get_args

interface, channel = get_args()

bus = can.interface.Bus(channel=channel, bustype=interface)
atexit.register(bus.shutdown)
print("Sniffing on CAN:", interface, channel)

while True:
    msg = bus.recv()
    print(msg)
