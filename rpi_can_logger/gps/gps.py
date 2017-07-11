import serial
import pynmea2
"""
Wrapper for the NEAMS thingo

"""


class GPS:
    def __init__(self, port, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                 bytesize=serial.EIGHTBITS, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.parity = parity
        self.stopbits = stopbits
        self.bytesize = bytesize
        self.timeout = timeout

    def connect(self):
        self.ser = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            parity=self.parity,
            stopbits=self.stopbits,
            bytesize=self.bytesize,
            timeout=self.timeout
        )

    def close(self):
        self.ser.close()


    def read(self):
        msg = pynmea2.parse(self.ser.readline())
        return {
            'time': msg.time,
            'lat': msg.latitude,
            'lng': msg.longitude,
            'alt': msg.altitude,
            'spd': msg.speed
        }
