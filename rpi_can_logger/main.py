#!/usr/bin/env python3
import argparse
import atexit
import logging
import os
from yaml import load, dump
import can
import RPi.GPIO as GPIO
from rpi_can_logger.gps import GPS
from rpi_can_logger.logger import CSVLogRotator, TeslaSniffingLogger, SniffingOBDLogger, QueryingOBDLogger

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

args = parser.parse_args()

if args.conf:

    with open(args.conf, 'r') as conf_fh:
        new_args = load(conf_fh)
        # should validate the config here...
    store_bool = set([action.option_strings[0] for action in parser._actions if isinstance(action.default, bool)])


    def is_store_true(k, v):
        if type(v) not in [list, str]:
            v = str(v)
        if k in store_bool:
            return (k,)
        else:
            return (k, v)


    largs = [item for k in new_args for item in is_store_true('--' + k, new_args[k])]

    # args = parser.parse_args(largs)
    args = new_args
if args.verbose:
    print(dump(args))
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

logging.basicConfig(
    filename=log_messages + '/messages.log',
    level=logging.WARNING,
    filemode='a',
    format='%(asctime)s:%(levelname)s: %(message)s'
)
logging.getLogger().addHandler(logging.StreamHandler())
# log file size in MB
log_size = args.log_size

OBD_REQUEST = 0x07DF
OBD_RESPONSE = 0x07E8

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
all_fields = fields + gps_fields
if args.disable_gps:
    all_fields = fields


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
    return "NO_VIN"


def do_log(sniffing, tesla):
    try:
        bus = can.interface.Bus(channel=args.channel, bustype=args.interface)
        gps = GPS(args.gps_port)
        led2(0)
        led1(0)
    except can.CanError as err:
        logging.error('Failed to initialise CAN BUS: ' + str(err))
        return
    if tesla:
        logger_c = TeslaSniffingLogger
    elif sniffing:
        logger_c = SniffingOBDLogger
    else:
        logger_c = QueryingOBDLogger
    logger = logger_c(bus, pid_ids, pids, log_trigger)
    buff = {}
    csv_writer = CSVLogRotator(log_folder=log_folder, maxbytes=bytes_per_log, fieldnames=all_fields)
    while 1:
        led1(1)
        buff.update(logger.log())
        led1(0)
        if not args.disable_gps:
            led2(1)
            buff.update(gps.read())
            led2(0)
        if args.verbose:
            print(buff)
        # put the buffer into the csv logs
        csv_writer.writerow(buff)
        buff = {}


# def determine_sniff_query():
#     # try sending a regular old query for standard RPM
#     bus = can.interface.Bus()
#     bus.shutdown()
#     return True


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
