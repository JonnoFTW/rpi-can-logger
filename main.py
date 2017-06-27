import csv
import can
import optparse
import os
import gps
from datetime import datetime, timedelta
from collections import defaultdict
from tesla_can import pids, name2pid

# PCAN conf
can.rc['interface'] = 'pcan'
can.rc['channel'] = 'PCAN_USBBUS1'

# PiCAN2 conf
# need to use these steps: http://skpang.co.uk/blog/archives/1220
# import subprocess
# subprocess.exec('/sbin/ip link set can0 up type can bitrate 500000'.split(' '))
# can.rc['interface'] = 'socketcan_native'
# can.rc['channel'] = 'can0'

# log folder
log_folder = '/var/log/can-log'
# log file size in MB
log_size = 32
# log frequency
log_freq = 5  # 5 times per second
log_delay = timedelta(seconds=1. / log_freq)
# pids to log
log_pids = ['PID_TESLA_REAR_DRIVE_UNIT_POWER',
            'PID_TESLA_FRONT_DRIVE_UNIT_POWER',
            'PID_TESLA_BATTERY_STATE_OF_CHARGE',
            'PID_TESLA_DC_DC_CONVERTER_STATUS'
            ]

if not os.path.exists(log_folder):
    os.makedirs(log_folder)
    print("Created log folder", log_folder)

if any([pid not in name2pid for pid in log_pids]):
    exit("Unrecognised Tesla CAN PID(s) {}".format([pid for pid in log_pids if pid not in name2pid]))
pid_ids = set([name2pid[pid] for pid in log_pids])


def do_log():
    bus = can.interface.Bus()
    buff = defaultdict(list)
    log_at = datetime.now() + log_delay
    while 1:
        msg = bus.recv()
        if msg.arbitration_id in pid_ids:
            parsed = pids[msg.arbitration_id](msg.data)
            for k, v in parsed.items():
                buff[k].append(v)
        # read in the gps data
        gps_data = gps.read()
        for k, v in gps_data.items():
            buff[k].append(v)
        # put that in the buffer, if there's existing values in there, average them out
        if datetime.now() >= log_at:
            log_at = datetime.now() + log_delay
            # put the buffer into the csv logs



# read frames of the bus and put them in the buffer



if __name__ == "__main__":
    # start logging loop
    do_log()
