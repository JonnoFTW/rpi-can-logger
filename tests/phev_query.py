#!/usr/bin/env python3
from .util import get_args
import can
import atexit
from rpi_can_logger.logger import outlander_pids

interface, channel = get_args()

bus = can.interface.Bus(channel=channel, bustype=interface)
atexit.register(bus.shutdown)
print("Querying PHEV battery on ", channel, interface)

pids = {
    'Battery Health': [0x761, 0x762],
    'Charges': [0x765, 766],
    'Front RPM': [0x753, 0x754],
    'Rear RPM': [0x755, 0x756]

}
for response_addr, pid_d in outlander_pids.items():
    msg = can.Message(arbitration_id=pid_d['request'],
                      data=[2, 0x21, 0x01, 0, 0, 0, 0, 0])
    # listen for responses on addrs[1]
    print("Requesting:\t", pid_d['request'])
    print(msg)
    bus.send(msg)
    for i in range(100):
        recvd = bus.recv()
        if recvd.arbitration_id == response_addr:
            print(recvd)
            print(pid_d['parse'](recvd.data))
