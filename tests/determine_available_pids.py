#!/usr/bin/env python3
import can
import atexit
import time
from rpi_can_logger.logger import obd_pids
from .util import get_args

interface, channel = get_args()

bus = can.interface.Bus(channel=channel, bustype=interface)
atexit.register(bus.shutdown)
print("Determining PIDs on CAN:", bus)


def parse_support_frame(msg):
    by = 0
    base = msg.data[2]
    for data in msg.data[3:7]:
        bits = format(data, '08b')
        for idx, v in enumerate(bits):
            if v == '1':
                pid = 0x0100 + base + idx + 1 + by * 8
                if pid in obd_pids:
                    print(obd_pids[pid]['name'])
        by += 1


rcvd = [0, 0x20, 0x40, 0x60, 0x80]
while 1:
    try:
        while len(rcvd):
            time.sleep(0.1)
            msg = can.Message(extended_id=0, data=[2, 1, rcvd[0], 0, 0, 0, 0, 0], arbitration_id=0x07DF)
            bus.send(msg)
#o            print("S>", msg)
            for i in range(100):
                msg = bus.recv()
                if msg.arbitration_id in [0x7df, 0x7e8]:
                    print("R>", msg)
                    if msg.data[2] in rcvd:
                        parse_support_frame(msg)
                        rcvd.remove(msg.data[2])

    except KeyboardInterrupt:
        print("Terminating")
        break
