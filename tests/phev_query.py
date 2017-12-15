#!/usr/bin/env python3
from util import get_args
import can
import atexit
from rpi_can_logger.logger import outlander_pids
from itertools import cycle
from datetime import datetime

interface, channel = get_args()
bus = can.interface.Bus(channel=channel, bustype=interface)
atexit.register(bus.shutdown)
fst = 1
print("Querying PHEV on ", channel, interface)
for request_arb_id, p in cycle([list(outlander_pids.items())[0]]):
    pid = p['pid']
    req_msg = can.Message(arbitration_id=request_arb_id, extended_id=0,
                          data=[2, 0x21, pid, 0, 0, 0, 0, 0])
    ctl_msg = can.Message(arbitration_id=request_arb_id, extended_id=0,
                          data=[0x30, 0, 0, 0, 0, 0, 0, 0])

    print("Requesting:\t",  p['name'])
    bus.send(req_msg)
    bus.set_filters([{'can_id': p['response'], 'can_mask': 0xffff}])
    buf = bytes()
    num_bytes = 0
    multiline = True
    for i in range(500):
        recvd = bus.recv()
        if recvd.arbitration_id == p['response']:
            sequence = recvd.data[0]
            if sequence == 0x10:
                bus.send(ctl_msg)
                bus.send(req_msg)
                buf = recvd.data[4:]
                multiline = True
                num_bytes = recvd.data[1] - 2

            elif multiline:
                buf += recvd.data[1:]
                if len(buf) >= num_bytes:
                    print(p['parse'](buf))
                    buf = bytes()
                    num_bytes = 0
                    multiline = False
                    break

