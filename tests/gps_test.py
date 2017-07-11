#!/usr/bin/env python3
import serial
import pynmea2
import atexit
import time
import sys
# should be ttyUSB0 or 1, tty AMA0
port = '/dev/ttyUSB1'
if len(sys.argv) >= 2:
    port = sys.argv[1]
s = serial.Serial(
    port=port,
    baudrate=115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)
atexit.register(s.close)
for i in [
    '24 45 49 47 50 51 2c 44 54 4d 2a 33 42 0d 0a b5 62 06 01 03 00 f0 0a 00 04 23',
    '24 45 49 47 50 51 2c 47 42 53 2a 33 30 0d 0a b5 62 06 01 03 00 f0 09 00 03 21',
    '24 45 49 47 50 51 2c 47 4c 4c 2a 32 31 0d 0a b5 62 06 01 03 00 f0 01 00 fb 11',
    '24 45 49 47 50 51 2c 47 52 53 2a 32 30 0d 0a b5 62 06 01 03 00 f0 06 00 00 1b',
    '24 45 49 47 50 51 2c 47 53 41 2a 33 33 0d 0a b5 62 06 01 03 00 f0 02 00 fc 13',
    '24 45 49 47 50 51 2c 47 53 54 2a 32 36 0d 0a b5 62 06 01 03 00 f0 07 00 01 1d',
    '24 45 49 47 50 51 2c 47 53 56 2a 32 34 0d 0a b5 62 06 01 03 00 f0 03 00 fd 15',
    '24 45 49 47 50 51 2c 52 4d 43 2a 33 41 0d 0a b5 62 06 01 03 00 f0 04 00 fe 17',
    '24 45 49 47 50 51 2c 56 54 47 2a 32 33 0d 0a b5 62 06 01 03 00 f0 05 00 ff 19',
    '24 45 49 47 50 51 2c 5a 44 41 2a 33 39 0d 0a b5 62 06 01 03 00 f0 08 00 02 1f',
]:
    s.write(map(lambda x: int(x, 16), i.split(' ')))
    print("writing", i)
    time.sleep(0.5)
print("Reading from", s.portstr)
from io import StringIO
buff = StringIO()
while 1:
    try:
        ins = s.read()
        ins = ins.decode('ASCII')
    except:
        print("Couldn't decode", ins)
    # print(ins)
    if ins == '$':
        print("R>", pynmea2.parse(buff.getvalue()))
        buff = StringIO()
    elif isinstance(ins, str):
        buff.write(ins)
