#!/usr/bin/env python3
import can
import atexit
import sys
import time
if len(sys.argv) > 1:
    arg = sys.argv[1].lower()
    if arg == 'pcan':
        # PCAN
        interface = 'pcan'
        channel = 'PCAN_USBBUS1'
    elif arg in ['can1', 'can0']:
        # pican
        channel = arg
        interface = 'socketcan_native'
    else:
        exit("Invalid CAN bus specified")

bus = can.interface.Bus(channel=channel, bustype=interface)
atexit.register(bus.shutdown)
print("Sniffing CAN:", bus)

while 1:
    print(bus.recv())

rcvd = [0,0x20,0x40]
while 1:
    try:
        while len(rcvd):
            time.sleep(0.1)
            msg = can.Message(extended_id=0, data=[2, 1, rcvd[0], 0, 0, 0, 0, 0], arbitration_id=0x07DF)
            bus.send(msg)
            print("S>", msg)
            for i in range(100):
                msg = bus.recv()
                if msg.arbitration_id in [0x7df, 0x7e8]:
                    print("R>", msg)
                    rcvd.remove(msg.data[2])
                    break
    except KeyboardInterrupt:
        print("Terminating")
        break
