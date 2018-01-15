#!/usr/bin/env python3
from util import get_args
import can
import atexit
from rpi_can_logger.logger import bustech_pids
print(bustech_pids)
interface, channel = get_args()
bus = can.interface.Bus(channel=channel, bustype=interface)
atexit.register(bus.shutdown)
fst = 1
while 1:
#    bus.set_filters([{'can_id': p['response'], 'can_mask': 0xffff}])
    recvd = bus.recv()
#    print(recvd)
    if recvd.arbitration_id in bustech_pids:
        out = bustech_pids[recvd.arbitration_id]['parse'](recvd.data)
        print(out)
