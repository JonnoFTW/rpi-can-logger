import sys
import time
import can
import atexit
import re


can.rc['interface'] = 'pcan'
can.rc['channel'] = 'PCAN_USBBUS1'

bus = can.interface.Bus(channel=can.rc['channel'], interface=can.rc['interface'])
atexit.register(bus.shutdown)
if len(sys.argv) != 2:
    exit("Please provide a pcan trace file to play back")
#
fname = '/scratch/Dropbox/obd/lonsdale_Test/scania_2450_loop.trc'
fname = '/scratch/Dropbox/obd/tesla.trc'
last_sleep = 0
with open(sys.argv[1], 'r') as infile:
    print("Playing back", infile.name)
    [infile.readline() for _ in range(16)]
    for row in infile:
        row = re.split(r'\s+', row.strip())
        ts = float(row[1])
        sleep_ms = ts-last_sleep
        actual_sleep = max(0, sleep_ms/1000.)
        print("sleeping for ", round(sleep_ms, 3), "ms")
        time.sleep(actual_sleep)
        last_sleep = ts
        msg = can.Message(data=list(map(lambda x: int(x, 16), row[5:])),
                          timestamp=ts,
                          arbitration_id=int(row[3], 16),
                          extended_id=0)
        bus.send(msg)
        print("S>", msg)
