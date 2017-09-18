#!/usr/bin/env python3
from rpi_can_logger.logger import fms_pids, fms_name2pid
import can
import atexit
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
    can_type = sys.argv[2].lower()
    if can_type not in ['tesla', 'obd', 'fms']:
        exit('Invalid CAN type')

bus = can.interface.Bus(channel=channel, bustype=interface, bitrate=250000)
atexit.register(bus.shutdown)
print("Sniffing CAN:", bus)
# for f in fms_pids:
#     print(hex(f))
# exit()
read = set()
reader_err = set()
while 1:
    msg = bus.recv()
    # print("R>", hex(msg.arbitration_id))
    pid = (msg.arbitration_id >> 8) & 0xffff
    # print(int(hex(pid),16))
    # print(i, end='')
    # print(hex(pid))
    if pid == 0xF004:
        try:
            val = (fms_pids[pid]['parse'](msg.data))
            read.add(pid)
            print(val)
        except Exception as e:
            print("ERROR", hex(pid), fms_pids[pid]['name'], e)
            reader_err.add(pid)
            # print()
            pass
# for f in read:
#     print(f)
print("good", list(fms_pids[p]['name'] for p in read if p in fms_pids))
print("Err", list(fms_pids[p]['name'] for p in reader_err if p in fms_pids))