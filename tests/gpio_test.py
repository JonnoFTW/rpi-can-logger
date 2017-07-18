#!/usr/bin/env python3
import serial
import atexit
import sys

# should be ttyUSB0 or 1, tty AMA0
port = '/dev/ttyAMA0'
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
print("Reading from", s.portstr)
while 1:
    try:
        print("R>", s.readline().decode('ASCII'), end='')
    except serial.SerialException as e:
        print(e)
    except KeyboardInterrupt:
        print("\nTerminating")
        break
