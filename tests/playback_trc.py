import sys
import time
import can
import atexit

can.rc['interface'] = 'pcan'
can.rc['channel'] = 'PCAN_USBBUS1'

bus = can.interface.Bus()
atexit.register(bus.shutdown)

import re

if len(sys.argv) != 2:
    exit("Please provide a pcan trace file to play back")
t = None
with open(sys.argv[1], 'r') as infile:
    print("Playing back", infile.name)
    [infile.readline() for _ in range(16)]
    for row in infile:
        row = re.split(r'\s+', row.strip())
        delay = float(row[1])
        if t is None:
            t = delay
        if delay != 0:
            time.sleep(delay / 1000.0)

        msg = can.Message(data=list(map(lambda x: int(x, 16), row[5:])),
                          timestamp=delay,
                          arbitration_id=int(row[3], 16),
                          extended_id=0)
        start = time.time()
        bus.send(msg)
        end = time.time()
        t -= start - end
        print("S>", msg)
