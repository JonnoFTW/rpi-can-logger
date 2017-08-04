#!/usr/bin/env python3
import argparse
import atexit
import logging
import os
import subprocess
from datetime import datetime
from yaml import load, dump
import can

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    from rpi_can_logger.stubs import GPIO
from rpi_can_logger.gps import GPS
from rpi_can_logger.util import get_serial, get_ip, list_log, OBD_REQUEST, OBD_RESPONSE
from rpi_can_logger.logger import CSVLogRotator, TeslaSniffingLogger, SniffingOBDLogger, QueryingOBDLogger, \
    BluetoothLogger

parser = argparse.ArgumentParser(description='Log Data from a PiCAN2 Shield and GPS')
parser.add_argument('--interface', '-i', default='can1', help='CAN Interface to use')
parser.add_argument('--channel', '-c', default='socketcan_native', help='CAN Channel to use')
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
parser.add_argument('--conf', default=False, type=str,
                    help='Override options given here with those in the provided config file')
parser.add_argument('--verbose', '-v', action='store_true', help='Show rows on the stdout')
parser.add_argument('--log-bluetooth', action='store_true', help='Log to Bluetooth if Available')
parser.add_argument('--vid', help='Vehicle Identifier, will try to fetch the VIN, otherwise will a RPi identifier')
parser.add_argument('--log-level', '-ll', help='Logging level', default='warning', choices=['warning', 'debug'])
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

log_bluetooth = args.log_bluetooth
log_level = args.log_level
is_tesla = args.tesla
if is_tesla:
    from rpi_can_logger.logger import tesla_pids as pids, tesla_name2pid as name2pid

    args.sniffing = True
else:
    from rpi_can_logger.logger import obd_pids as pids, obd_name2pid as name2pid

can.rc['interface'] = args.interface
can.rc['channel'] = args.channel

log_messages = args.log_messages
# log folder
log_folder = args.log_folder
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
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(7, GPIO.OUT)
    GPIO.setup(37, GPIO.OUT)


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
    return subprocess.check_output(['tail', '-n', '20', log_file])

bt_commands = {
    '$ip': get_ip,
    '$serial': get_serial,
    '$list_log': lambda: list_log(log_folder),
    '$echo': lambda x: x,
    '$btlog': btlog,
    '$err': get_error,
    '$systime': lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
}

def init_sniff(bus):
    bus.send(can.Message(extended_id=False, data=[2, 1, 0, 0, 0, 0, 0, 0], arbitration_id=OBD_REQUEST))


def do_log(sniffing, tesla):
    try:
        if log_bluetooth:
            logging.warning("Starting BT")
            btl = BluetoothLogger(fields=all_fields, bt_commands=bt_commands)
            btl.start()
        logging.warning("Waiting for CAN Bus channel={} interface={}".format(args.channel, args.interface))
        led1(1)
        led2(1)
        bus = can.interface.Bus(channel=args.channel, bustype=args.interface)
        gps = GPS(args.gps_port)
        led2(0)
        led1(0)
        logging.warning("Connected CAN Bus and GPS")

    except can.CanError as err:
        logging.error('Failed to initialise CAN BUS: ' + str(err))
        return
    if tesla:
        logger_c = TeslaSniffingLogger
    elif sniffing:
        logger_c = SniffingOBDLogger
    else:
        logger_c = QueryingOBDLogger
        init_sniff(bus)

    logger = logger_c(bus, pid_ids, pids, log_trigger)
    buff = {}
    if sniffing or is_tesla:
        vin = get_serial()
    else:
        vin = get_vin(bus)
    csv_writer = CSVLogRotator(log_folder=log_folder, maxbytes=bytes_per_log, fieldnames=all_fields, vin=vin)
    err_count = 0
    while 1:
        led1(1)
        new_log = logger.log()
        if not new_log:
            err_count += 1
            if err_count == 5:
                shutdown_msg = "Shutting down after failing to get OBD data"
                logging.warning(shutdown_msg)
                btl.send(shutdown_msg)
                os.system('sudo shutdown - h now')
        buff.update(new_log)
        for k,v in buff.items():
            if type(v) is float:
                buff[k] = round(v, 2)
        led1(0)
        if not args.disable_gps:
            led2(1)
#            logging.warning("Reading gps")
            gps_data = gps.read()
 #           logging.warning("read gps")
            if gps_data is not None:
                buff.update(gps_data)
            led2(0)
        if args.verbose:
            print(buff)
        # put the buffer into the csv logs
        row_txt = csv_writer.writerow(buff)
        if log_bluetooth:
            led2(1)
            if bt_log:
                btl.send(row_txt)
            led2(0)

        buff = {}


def shutdown():
    GPIO.cleanup()


atexit.register(shutdown)

if __name__ == "__main__":
    # start logging loop
    import time

    setup_GPIO()
    sleep_time = 10
    err_count = 0
    logging.warning("Starting logging")
    while 1:
        do_log(args.sniffing, args.tesla)
        led1(1)
        led2(1)
        logging.warning("Sleeping for {}s".format(sleep_time))
        time.sleep(sleep_time)
        led2(0)
        led1(0)
        err_count += 1
