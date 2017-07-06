import csv
import can
import argparse
import os
import gps
import logging
from datetime import datetime
import subprocess
import atexit
from pathlib import Path

parser = argparse.ArgumentParser(description='Log Data from a PiCAN2 Shield and GPS')
parser.add_argument('--interface', '-i', default='pcan', help='CAN Interface to use')
parser.add_argument('--channel', '-c', default='PCAN_USBBUS1', help='CAN Channel to use')
parser.add_argument('--log-messages', '-lm', default='/var/log/can-log/messages/',
                    help='Folder where debug messages are store')
parser.add_argument('--log-folder', '-lf', default='/var/log/can-log/', help='Where logged CAN/GPS data is stored')
parser.add_argument('--log-size', '-ls', default=32, type=int, help='Size of log data files in MB')
parser.add_argument('--log-pids', '-lp', nargs='+', help='PID names to log',
                    default=['PID_TESLA_REAR_DRIVE_UNIT_POWER',
                             'PID_TESLA_FRONT_DRIVE_UNIT_POWER',
                             'PID_TESLA_BATTERY_STATE_OF_CHARGE',
                             'PID_TESLA_DC_DC_CONVERTER_STATUS'
                             ])
parser.add_argument('--tesla', action='store_true', help='Indicate that we are logging a tesla')
parser.add_argument('--log-trigger', '-lg', help='PID to trigger logging event.')

args = parser.parse_args()
print (args)
is_tesla = args.tesla
if is_tesla:
    from logger import tesla_pids as pids, tesla_name2pid as name2pid
else:
    from logger import obd_pids as pids, obd_name2pid as name2pid
# PCAN conf
can.rc['interface'] = args.interface
can.rc['channel'] = args.channel
print(can.rc)
can.rc['interface'] = 'pcan'
can.rc['channel'] = 'PCAN_USBBUS1'
print(can.rc)
# PiCAN2 conf
# need to use these steps: http://skpang.co.uk/blog/archives/1220
if can.rc['interface'] == 'socketcan_native':
    subprocess.call('/sbin/ip link set can0 up type can bitrate 500000'.split(' '))

log_messages = args.log_messages
# log folder
log_folder = args.log_folder
for p in [log_messages, log_folder]:
    if not os.path.exists(p):
        os.makedirs(p)
        print("Created log folder", p)

logging.basicConfig(
    # filename=log_messages + '/messages.log',
    level=logging.DEBUG,
    filemode='a',
    format='%(asctime)s:%(levelname)s: %(message)s'
)
# log file size in MB
log_size = args.log_size

# log frequency
# log_freq = 5  # 5 times per second
# log_delay = timedelta(seconds=1. / log_freq)
OBD_REQUEST = 0x07DF
OBD_RESPONSE = 0x07E8

# pids to log
log_pids = args.log_pids


if any([pid not in name2pid for pid in log_pids]):
    exit("Unrecognised Tesla CAN PID(s) {}".format([pid for pid in log_pids if pid not in name2pid]))
pid_ids = set([name2pid[pid] for pid in log_pids])

log_trigger = name2pid[args.log_trigger]
bytes_per_log = 2 ** 20 * log_size

fields = list(set([val for sublist in [pids[p]['fields'] for p in pid_ids] for val in sublist]))
gps_fields = ['lat', 'lng', 'alt', 'spd']
all_fields = fields + gps_fields


def make_writer(now):
    out_csv = open(now.strftime('%Y%m%d_%H%M.csv'), 'w')
    out_writer = csv.DictWriter(out_csv, fieldnames=all_fields, restval=None)
    out_writer.writeheader()
    return out_writer, out_csv


def make_msg(m):
    """

    :param m: the pid to make a CAN OBD request for
    :return: can.Message
    """
    mode, pid = divmod(m, 0x100)
    return can.Message(
        arbitration_id=0x7df,
        data=[2, mode, pid, 0, 0, 0, 0, 0],
        extended_id=False
    )


def get_vin(bus):
    vin_request_message = can.Message(data=[2, 9, 0x02, 0, 0, 0, 0, 0],
                                      arbitration_id=0x7df,
                                      extended_id=0)
    bus.send(vin_request_message)
    # keep receving otherwise timeout
    vin = ""

    def makeVin(data):
        return ''.join(map(chr, data))

    for i in range(128):
        msg = bus.recv()
        if msg.arbitration_id == 0x07e8 and msg.data[2:4] == bytearray([0x49, 0x02]):
            vin += makeVin(msg.data[-3:])
            nxtmsg = can.Message(extended_id=0, arbitration_id=0x07e0, data=[0x30, 0, 4, 0, 0, 0, 0, 0])
            bus.send(nxtmsg)
        elif msg.arbitration_id == 0x07e8 and msg.data[0] == 0x21:
            vin += makeVin(msg.data[1:])
        elif msg.arbitration_id == 0x07e8 and msg.data[0] == 0x22:
            vin += makeVin(msg.data[1:])
            return vin
    return "NO_VIN"


def do_log(sniffing):
    try:
        bus = can.interface.Bus()
        atexit.register(bus.shutdown)
    except can.CanError as err:
        logging.error('Failed to initialise CAN BUS: '+str(err))
        return
    buff = {}
    # log_at = datetime.now() + log_delay
    bytes_written = 0
    out_writer, out_file = make_writer(datetime.now())
    while 1:
        if not sniffing:
            # send a message asking for those requested pids
            for m in pid_ids:
                bus.send(make_msg(m))
                # if not sniffing:
                # keep receving can packets until we get everything

        try:
            # should try to receive as many pids as asked for
            msg = bus.recv()
        except can.CanError as e:
            # error receiving on the can bus
            #
            continue
            pass
        if is_tesla:
            pid = msg.arbitration_id
            obd_data = msg.data
        else:
            pid = ((msg.data[1] - 0x40) * 256) + msg.data[2]
            obd_data = msg.data[3:]

        if pid in pid_ids:
            parsed = pids[pid]['parse'](obd_data)
            buff.update(parsed)
        # read in the gps data
        now = datetime.now()

        if msg.arbitration_id == OBD_RESPONSE:
            # get GPS readings then log
            buff.update(gps.read())
            # put the buffer into the csv logs
            bytes_written += out_writer.writerow(buff)
            buff = {}
            if bytes_written >= bytes_per_log:
                # open a new file
                out_file.close()
                out_name = str(Path(out_file.name).absolute())
                subprocess.Popen(['7zr', 'a', '-m0=lzma', '-mx=9', '-mfb=64', '-md=16m',
                                  out_name + '.7z',
                                  out_name])
                # should gzip the file (on a new process)
                out_writer, out_file = make_writer(now)


def determine_sniff_query():
    # try sending a regular old query for standard RPM
    bus = can.interface.Bus()
    bus.shutdown()
    return True


if __name__ == "__main__":
    # start logging loop
    import time
    is_sniff = determine_sniff_query()
    sleep_time = 10
    err_count = 0
    while 1:
        do_log(is_sniff)
        logging.debug("Sleeping for {}s".format(sleep_time))
        time.sleep(sleep_time)
        err_count += 1
