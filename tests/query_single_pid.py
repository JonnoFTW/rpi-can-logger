#!/usr/bin/env python3
import can
import atexit
import time
from rpi_can_logger.logger import obd_pids
from util import get_args
interface, channel = get_args()

bus = can.interface.Bus(channel=channel, bustype=interface)
atexit.register(bus.shutdown)
print("Querying PID on CAN:", bus)


while 1:
    try:
        pid = 0
        while pid <= 0xC4:
            time.sleep(0.1)
            if 0x100+pid in obd_pids:
                disp = obd_pids[0x100+pid]['name']
            else:
                disp = hex(pid)
            print("Requesting",disp)
            msg = can.Message(extended_id=0, data=[2, 1, pid, 0, 0, 0, 0, 0], arbitration_id=0x07DF)
#            print(msg)
            bus.send(msg)
            for i in range(100):
                msg = bus.recv()
                if msg.arbitration_id in [0x7df, 0x7e8]:
                    print("R>", msg)
            pid += 1
        break
    except KeyboardInterrupt:
        print("Terminating")
        break
