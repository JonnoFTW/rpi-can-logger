#!/usr/bin/env python3
import argparse
import atexit
import gzip
import base64
import logging
import os
import subprocess
from datetime import datetime
from glob import glob
import struct

from yaml import load, dump
import can
from os.path import expanduser
import pathlib

try:
    import RPi.GPIO as GPIO
except ImportError:
    from rpi_can_logger.stubs import GPIO
from rpi_can_logger.gps import GPS
from rpi_can_logger.util import get_serial, get_ip, list_log, OBD_REQUEST, OBD_RESPONSE, sudo
from rpi_can_logger.logger import JSONLogRotator, TeslaSniffingLogger, SniffingOBDLogger, QueryingOBDLogger, \
    BluetoothLogger, FMSLogger, BustechLogger

parser = argparse.ArgumentParser(description='Log Data from a PiCAN2 Shield and GPS')
parser.add_argument('--interface', '-i', default='can0', help='CAN Interface to use')
parser.add_argument('--channel', '-c', default='socketcan_native', help='CAN Channel to use')
parser.add_argument('--pid-file', '-pf', default='/var/log/can-log/can_log.pid',
                    help='PID file to record what file we are currently writing to')
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
parser.add_argument('--disable-gps', '-dg', action='store_true', help='Explicitly disable GPS logging')
parser.add_argument('--gps-port', '-gp', default='/dev/ttyS0', help='GPS serial port')
parser.add_argument('--gps-baud', '-gb', default=9600, type=int, help='Baud rate of GPS serial')
parser.add_argument('--conf', default=False, type=str,
                    help='Override options given here with those in the provided config file')
parser.add_argument('--verbose', '-v', action='store_true', help='Show rows on the stdout')
parser.add_argument('--log-bluetooth', action='store_true', help='Log to Bluetooth if Available')
parser.add_argument('--log-level', '-ll', help='Logging level', default='warning', choices=['warning', 'debug'])
parser.add_argument('--vehicle-id', '-vh', help='Unique identifier for the vehicle')
parser.add_argument('--bluetooth-pass', '-btp', help='Bluetooth password')
parser.add_argument('--fms', action='store_true', help='Indicate that we are using a FMS CAN')
parser.add_argument('--bustech', action='store_true', help='Indicate that we are using a Bustech Electric CAN')

parser.add_argument('--obd-query', action='store_true', help='Indicate we are querying OBD')
args = parser.parse_args()

if args.conf:

    with open(args.conf, 'r') as conf_fh:
        new_args = load(conf_fh)
    # should validate the config here...
    out_args = {}
    for arg in parser._actions:
        if arg.dest.replace('_', '-') not in new_args:
            out_args[arg.dest] = arg.default
        else:
            out_args[arg.dest] = new_args[arg.dest.replace('_', '-')]


    class ArgStruct:
        def __init__(self, **entries):
            self.__dict__.update(entries)


    args = ArgStruct(**out_args)
if args.verbose:
    print(dump(args))
disable_gps = args.disable_gps
log_bluetooth = args.log_bluetooth
log_level = args.log_level
is_tesla = args.tesla
is_fms = args.fms
is_obd_query = args.obd_query
is_bustech = args.bustech
if is_tesla:
    from rpi_can_logger.logger import tesla_pids as pids, tesla_name2pid as name2pid

    logging.warning("USING TESLA")
elif is_fms:
    args.sniffing = True
    logging.warning("USING FMS")
    from rpi_can_logger.logger import fms_pids as pids, fms_name2pid as name2pid
elif is_bustech:
    args.sniffing = True
    logging.warning("USING BUSTECH")
    from rpi_can_logger.logger import bustech_pids as pids, bustech_name2pid as name2pid
elif is_obd_query:
    print("USING OBD QUERY")
    from rpi_can_logger.logger import obd_pids as pids, obd_name2pid as name2pid
    args.sniffing = True
else:
    logging.error("Please specify what kind of CAN logging you want")
    exit("Please specify what kind of CAN logging you want")

can.rc['interface'] = args.interface
can.rc['channel'] = args.channel

log_messages = expanduser(args.log_messages)
# log folder
log_folder = expanduser(args.log_folder)
log_pid_location = expanduser(args.pid_file)
for p in [log_messages, log_folder]:
    if not os.path.exists(p):
        os.makedirs(p)
        print("Created log folder", p)

log_levels = {
    'warning': logging.WARNING,
    'debug': logging.DEBUG
}
log_file = log_messages + '/messages.log'
logging.basicConfig(
    filename=log_file,
    level=log_levels.get(log_level, logging.WARNING),
    filemode='a',
    format='%(asctime)s:%(levelname)s: %(message)s'
)
logging.getLogger().addHandler(logging.StreamHandler())
# log file size in MB
log_size = args.log_size

# pids to log
if type(args.log_pids[0]) is list:
    log_pids = args.log_pids[0]
else:
    log_pids = args.log_pids

if any([pid not in name2pid for pid in log_pids]):
    exit("Unrecognised CAN PID(s) {}".format([pid for pid in log_pids if pid not in name2pid]))
pid_ids = set([name2pid[pid] for pid in log_pids])

log_trigger = name2pid[args.log_trigger]
bytes_per_log = 2 ** 20 * log_size

fields = list(set([val for sublist in [pids[p]['fields'] for p in pid_ids] for val in sublist]))
gps_fields = GPS.FIELDS
all_fields = gps_fields + sorted(fields)
if args.disable_gps:
    all_fields = fields

all_fields += ['vid']


def setup_GPIO():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(7, GPIO.OUT)
    GPIO.setup(37, GPIO.OUT)
    GPIO.setup(35, GPIO.IN)


def led1(on_off):
    GPIO.output(7, bool(on_off))


def led2(on_off):
    GPIO.output(37, bool(on_off))


def get_vin(bus):
    vin_request_message = can.Message(data=[2, 9, 0x02, 0, 0, 0, 0, 0],
                                      arbitration_id=OBD_REQUEST,
                                      extended_id=0)
    bus.send(vin_request_message)
    # keep receiving otherwise timeout
    vin = ""

    def makeVin(data):
        return ''.join(map(chr, data))

    for i in range(128):
        msg = bus.recv()
        if msg.arbitration_id == OBD_RESPONSE and msg.data[2:4] == bytearray([0x49, 0x02]):
            vin += makeVin(msg.data[-3:])
            nxtmsg = can.Message(extended_id=0, arbitration_id=0x07e0, data=[0x30, 0, 4, 0, 0, 0, 0, 0])
            bus.send(nxtmsg)
        elif msg.arbitration_id == 0x07e8 and msg.data[0] == 0x21:
            vin += makeVin(msg.data[1:])
        elif msg.arbitration_id == 0x07e8 and msg.data[0] == 0x22:
            vin += makeVin(msg.data[1:])
            return vin
    return False


bt_log = True


def btlog(opt):
    global bt_log
    bt_log = opt == 'on'
    return "{}".format(bt_log)


def get_error():
    return subprocess.check_output(['/usr/bin/tail', '-n', '20', log_file])


def reset():
    return sudo('shutdown -r now')


def reset_wifi():
    for cmd in ['ifdown', 'ifup']:
        sudo('/sbin/{} wlan0'.format(cmd))


def set_vid(val):
    if not args.conf:
        return "no conf file"
    fname = args.conf
    with open(fname, 'r') as inf:
        data = load(inf)
    data['vehicle-id'] = val
    with open(fname, 'w') as outf:
        dump(data, outf, default_flow_style=False)
    return val


responds_to = set()

writing_to = {}


def get_responds():
    return ','.join([pids[x]['name'] for x in sorted(responds_to)])


def export_files(sock):
    print("currently writing", writing_to['name'])
    for fname in sorted(glob(log_folder + "/*.json*")):
        if fname.endswith(writing_to['name']):
            print(fname, "is currently being written to")
            continue
        if fname.endswith('.done'):
            print("Skipping", fname)
            sock.send("$skipping={}!\n".format(fname))
            continue
        # we will send base64 encoded gzipped json
        with open(fname, 'rb') as infile:
            file_bytes = infile.read()
            if fname.endswith(".json"):
                if len(file_bytes) == 0:
                    print("Skipping empty file:", fname)
                    os.remove(fname)
                    continue
                json_gzip_bytes = gzip.compress(file_bytes)
            else:
                json_gzip_bytes = file_bytes
            json_gzip_base64 = base64.b64encode(json_gzip_bytes)
            try:

                if struct.unpack('I', json_gzip_bytes[-4:])[0] == 0:
                    # don't send empty files
                    logging.warning("Skipping empty file: " + pathlib.Path(fname).name)
                    os.remove(fname)
                    continue
            except:
                logging.warning("Not a GZIP file: " + fname)
                continue
            msg = '$export={}={}!\n'.format(len(json_gzip_bytes), pathlib.Path(fname).name)
            print(msg, end='')
            sock.send(msg)
            n = 900
            to_send_str = str(json_gzip_base64, 'ascii')
            lines = [to_send_str[i:i + n] for i in range(0, len(to_send_str), n)]
            for line in lines:
                sock.send("$export={}\n".format(line))
            sock.send("$done\n")
            os.rename(fname, fname+'.done')
        sock.send('$export=done\n')


bt_commands = {
    '$ip': get_ip,
    '$serial': get_serial,
    '$list_log': lambda: list_log(log_folder),
    '$echo': lambda x: x,
    '$btlog': btlog,
    '$err': get_error,
    '$systime': lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
    '$reset': reset,
    '$resetwifi': reset_wifi,
    '$setvid': set_vid,
    '$respondsto': get_responds,
    '$export': export_files,
    '$login': lambda x: "IDENTIFIED"
}


def init_sniff(bus):
    bus.send(can.Message(extended_id=False, data=[2, 1, 0, 0, 0, 0, 0, 0], arbitration_id=OBD_REQUEST))


def reset_can_interface(interface):
    sudo('ifdown ' + interface)
    sudo('ifup ' + interface)


def do_log():
    try:

        if log_bluetooth:
            logging.warning("Starting BT")
            btl = BluetoothLogger(fields=all_fields, bt_commands=bt_commands, password=args.bluetooth_pass)
            btl.start()
        logging.warning("Waiting for CAN Bus channel={} interface={}".format(args.channel, args.interface))
        led1(1)
        led2(1)
        if is_fms:
            baud = 250000
        else:
            baud = 500000
        # Reset the CAN interface just in case it doesn't come up
        reset_can_interface(args.channel)
        bus = can.interface.Bus(channel=args.channel, bustype=args.interface, bitrate=baud)
        if not disable_gps:
            gps = GPS(args.gps_port, args.gps_baud)
        led2(0)
        led1(0)
        logging.warning("Connected CAN Bus and GPS")

    except can.CanError as err:
        logging.error('Failed to initialise CAN BUS: ' + str(err))
        return
    if is_tesla:
        logging.warning("Using TeslaSnifferLogger")
        logger_c = TeslaSniffingLogger
    elif is_bustech:
        logger_c = BustechLogger
    elif is_obd_query:
        logging.warning("Using QueryingOBDLogger")
        logger_c = QueryingOBDLogger
        init_sniff(bus)

    elif is_fms:
        logging.warning("Using FMSLogger")
        logger_c = FMSLogger
    else:
        logging.warning("Using SnifferLogger")
        logger_c = SniffingOBDLogger
    logger = logger_c(bus, pid_ids, pids, log_trigger)
    responds_to.update(logger.responds_to)
    trip_sequence = 0
    vid = args.vehicle_id
    json_writer = JSONLogRotator(log_folder=log_folder, maxbytes=bytes_per_log, fieldnames=all_fields, vin=vid,
                                 pid_file=log_pid_location)
    path = pathlib.Path(json_writer._out_fh.name)
    writing_to['name'] = path.name
    trip_id = '{}_{}'.format(path.stem, vid)

    def make_buff():
        return {
            'vid': vid,
            'trip_id': trip_id,
            'trip_sequence': trip_sequence
        }

    while 1:
        buff = make_buff()
        led1(1)
        new_log = logger.log()
        if GPIO.input(35) == 1:
            shutdown_msg = "$status=Received shutdown signal"
            logging.warning(shutdown_msg)
            if log_bluetooth:
                btl.send(shutdown_msg)
            sudo('shutdown -h 0')

        buff.update(new_log)
        for k, v in buff.items():
            if type(v) is float:
                buff[k] = round(v, 2)
        led1(0)
        if not args.disable_gps:
            led2(1)
            gps_data = gps.read()
            if gps_data is not None:
                buff.update(gps_data)
            led2(0)
        if args.verbose:
            print(buff)
        # put the buffer into the logs
        row_txt = json_writer.writerow(buff)
        trip_sequence += 1
        if log_bluetooth:
            led2(1)
            if bt_log and btl.identified:
                btl.send(row_txt)
            led2(0)


def shutdown():
    GPIO.cleanup()


atexit.register(shutdown)

if __name__ == "__main__":
    # start logging loop
    import time

    setup_GPIO()
    sleep_time = 10
    log_err_count = 0
    logging.warning("Starting logging")
    while 1:
        try:
            do_log()
        except Exception as e:
            logging.error(e, exc_info=True)
        led1(1)
        led2(1)
        logging.warning("Sleeping for {}s".format(sleep_time))
        time.sleep(sleep_time)
        led2(0)
        led1(0)
        log_err_count += 1
        if log_err_count == 3:
            sudo('reboot')
