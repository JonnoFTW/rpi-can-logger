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
# print("Querying PHEV on ", channel, interface)
for request_arb_id, p in cycle([list(outlander_pids.items())[0]]):
    pid = p['pid']
    msg = can.Message(arbitration_id=request_arb_id, extended_id=0,
                      data=[2, 0x21, pid, 0, 0, 0, 0, 0])
    ctl_msg = can.Message(arbitration_id=request_arb_id, extended_id=0,
                      data=[0x30, 0x0, 0x0, 0, 0, 0, 0, 0])

    # listen for responses on addrs[1]
    #    print("Requesting:\t", pid_d['request'], pid_d['name'])
#    print("S>", msg)
    bus.send(msg)
#    bus.send(ctl_msg)
    buf = bytes()
    num_bytes = 0
    multiline = True
    for i in range(500):
        recvd = bus.recv()
        if recvd.arbitration_id == p['response']:
#            print("R>", i, recvd)
            sequence = recvd.data[0]
            if sequence == 0x10:
                buf += recvd.data[4:]
                multiline = True
                num_bytes = recvd.data[1] - 2
                # print("Multiline bytes expected", num_bytes)

#                bus.send(msg)
                bus.send(ctl_msg)
#                print("S>", ctl_msg)
            elif multiline:
                buf += recvd.data[1:]
                #                print(len(buf), buf)
                if len(buf) >= num_bytes:
                    if fst:
                        print('time', ','.join(p['parse'](buf).keys()), sep=',')
                        fst = 0
                    print(datetime.now(), ','.join(map(str, p['parse'](buf).values())), sep=',')

                    buf = bytes()
                    num_bytes = 0
                    multiline = False
                    break
            else:
                print(p['parse'](recvd.data))
