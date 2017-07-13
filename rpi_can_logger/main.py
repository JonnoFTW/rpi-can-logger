#!/usr/bin/env python3
import argparse
import atexit
import logging
import os
import subprocess

import can

from rpi_can_logger.gps import GPS
from rpi_can_logger.logger import CSVLogRotator

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
parser.add_argument('--sniffing', action='store_true',
                    help='Set sniffing mode on, otherwise the logger will poll. Setting --tesla will make this true by default')
parser.add_argument('--log-trigger', '-lg', help='PID to trigger logging event.')
parser.add_argument('--disable-gps', '-dg', action='store_false', help='Explicitly disable GPS logging')
parser.add_argument('--conf', default=False, type=str,
                    help='Override options given here with those in the provided config file')

args = parser.parse_args()

if args.conf:
    from yaml import load

    with open(args.conf, 'r') as conf_fh:
        new_args = load(conf_fh)
        # should validate the config here...
    args = new_args

is_tesla = args.tesla
if is_tesla:
    from rpi_can_logger.logger import tesla_pids as pids, tesla_name2pid as name2pid

    args.sniffing = True
else:
    from rpi_can_logger.logger import obd_pids as pids, obd_name2pid as name2pid
# PCAN conf
can.rc['interface'] = args.interface
can.rc['channel'] = args.channel

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
    level=logging.WARNING,
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
gps_fields = GPS.FIELDS
all_fields = fields + gps_fields
if args.disable_gps:
    all_fields = fields


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
        gps = GPS('/dev/ttyUSB0')
        atexit.register(bus.shutdown)
    except can.CanError as err:
        logging.error('Failed to initialise CAN BUS: ' + str(err))
        return
    buff = {}
    csv_writer = CSVLogRotator(maxbytes=bytes_per_log)
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

        if msg.arbitration_id == OBD_RESPONSE and pid == log_trigger:
            # get GPS readings then log
            if not args.disable_gps:
                buff.update(GPS.read())
            # put the buffer into the csv logs
            csv_writer.writerow(buff)
            buff = {}


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
