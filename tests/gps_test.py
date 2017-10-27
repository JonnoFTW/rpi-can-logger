#!/usr/bin/env python3
from io import StringIO
from rpi_can_logger.gps import GPS
import sys

# should be ttyUSB0 or 1, tty AMA0
port = '/dev/ttyS0'
if len(sys.argv) >= 2:
    port = sys.argv[1]

gps = GPS(port, 9600)
print("Reading from", gps.ser.portstr)

buff = StringIO()
while 1:
    try:
        print("R>", gps.read())
    except KeyboardInterrupt:
        print("\nTerminating")
        break
