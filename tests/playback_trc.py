import sys
import time
import can
import atexit
import re

can.rc['interface'] = 'pcan'
can.rc['channel'] = 'PCAN_USBBUS1'

bus = can.interface.Bus()
atexit.register(bus.shutdown)

if len(sys.argv) != 2:
    exit("Please provide a pcan trace file to play back")
old_ts = None
with open(sys.argv[1], 'r') as infile:
    print("Playing back", infile.name)
    [infile.readline() for _ in range(16)]
    for row in infile:
        row = re.split(r'\s+', row.strip())
        ts = float(row[1])
        if old_ts is None:
            old_ts = ts
        actual_sleep = (ts - old_ts) / 1000.0
        # print("sleeping for ", actual_sleep)
        time.sleep(max(actual_sleep, 0))

        msg = can.Message(data=list(map(lambda x: int(x, 16), row[5:])),
                          timestamp=ts,
                          arbitration_id=int(row[3], 16),
                          extended_id=1)
        start = time.time()
        bus.send(msg)
        end = time.time()
        old_ts = ts - (start - end)
        print("S>", msg)
