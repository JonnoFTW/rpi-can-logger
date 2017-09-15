#!/usr/bin/env python3
import can
import csv
import datetime
import sys

if len(sys.argv) > 2:
    arg1 = sys.argv[1].lower()
    if arg1 == 'pcan':
        # PCAN
        interface = 'pcan'
        channel = 'PCAN_USBBUS1'
    elif arg1 in ['can1', 'can0']:
        # pican
        channel = arg1
        interface = 'socketcan_native'
    else:
        exit("Invalid CAN bus specified")
channel = "can1"
interface = "socketcan_native"
with open('/home/pi/log/can-dumps/can_dump_{}.csv'.format(datetime.datetime.now().timestamp()), 'w') as outf:
    fields = ['seq', 'arb_id', 'bytes']
    i = 0
    writer = csv.DictWriter(outf, fieldnames=fields)
    writer.writeheader()
    bus = can.interface.Bus(channel=channel, bustype=interface)
    while True:
        i +=1
        msg = bus.recv()
        row = {
            'seq': i,
            'arb_id': hex(msg.arbitration_id),
            'bytes': ','.join(hex(x) for x in msg.data)
        }
        print(row)
        writer.writerow(row)
