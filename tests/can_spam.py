#!/usr/bin/env python3
import sys
import can
import atexit
import time
from util import get_args
interface, channel = get_args()
bus = can.interface.Bus(channel=channel, bustype=interface)
atexit.register(bus.shutdown)
print("Sending on ", channel, interface)

i = 0

while 1:
    msg = can.Message(data=[0x42,i,0,0,0,0,i,i], extended_id=0, arbitration_id=0x7e8)
    print(msg)
    bus.flush_tx_buffer()
    bus.send(msg)
    i += 1
    i %= 0xff
    time.sleep(0.5)
