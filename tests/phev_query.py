#!/usr/bin/env python3
from .util import get_args
import can
import atexit
from rpi_can_logger.logger import outlander_pids

interface, channel = get_args()

bus = can.interface.Bus(channel=channel, bustype=interface)
atexit.register(bus.shutdown)
print("Querying PHEV battery on ", channel, interface)

for response_addr, pid_d in outlander_pids.items():
    msg = can.Message(arbitration_id=pid_d['request'],
                      data=[2, 0x21, 0x01, 0, 0, 0, 0, 0])
    # listen for responses on addrs[1]
    print("Requesting:\t", pid_d['request'])
    print(msg)
    bus.send(msg)
    buf = bytes()
    for i in range(100):
        recvd = bus.recv()
        if recvd.arbitration_id == response_addr:
            print(recvd)
            if response_addr == 0x762:
                sequence = recvd.data[0]
                if sequence == 0x10:
                    buf += recvd.data[4:]
                else:
                    buf += recvd.data[1:]
                if sequence == 0x27:
                    print(pid_d['parse'](recvd.data))
            else:
                print(pid_d['parse'](recvd.data))

