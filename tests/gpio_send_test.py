#!/usr/bin/env python3
import serial
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

print("Writing to", s.portstr)
sout = b"hello there!\n"
count = 0
while 1:
    try:
        sout = "hello {}\n".format(count)
        s.write(bytes(sout, 'ascii'))
        count += 1
        print("S>", sout, end='')
        time.sleep(1)
    except KeyboardInterrupt:
        print("\nTerminating")
        break
