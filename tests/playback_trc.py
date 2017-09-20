#!/usr/bin/env python3
import sys
import time
import can
import atexit
import re
from util import get_args

interface, channel = get_args()
bus = can.interface.Bus(channel=channel, bustype=interface)
atexit.register(bus.shutdown)
print(sys.argv)
if len(sys.argv) < 2:
    exit("Please provide a PCAN trace file to play back")
fname = sys.argv[2]
#
# fname = '/scratch/Dropbox/obd/lonsdale_Test/scania_2450_loop.trc'
# fname = '/scratch/Dropbox/obd/tesla.trc'
last_sleep = 0
i = 0
with open(fname, 'r') as infile:
    print("Playing back", infile.name)
    [infile.readline() for _ in range(16)]
    for row in infile:
        row = re.split(r'\s+', row.strip())
        ts = float(row[1])
        sleep_ms = ts - last_sleep
        actual_sleep = max(0, sleep_ms / 1000.)
        print("sleeping for ", round(sleep_ms, 3), "ms")
        time.sleep(actual_sleep)
        last_sleep = ts
        msg = can.Message(data=list(map(lambda x: int(x, 16), row[5:])),
                          timestamp=ts,
                          arbitration_id=int(row[3], 16),
                          extended_id=0)
        bus.send(msg)
        i += 1
        print("S>",i, msg)
