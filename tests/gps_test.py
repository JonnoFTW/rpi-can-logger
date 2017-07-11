#!/usr/bin/env python3
import serial

s = serial.Serial(
    port='/dev/ttyUSB0',
    baudrate=115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)
print("Reading from", s.portstr)
while 1:
    print(s.readline())
