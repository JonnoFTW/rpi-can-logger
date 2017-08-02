from datetime import datetime
import logging
import serial
import pynmea2
import re
from io import StringIO
import atexit

"""
Wrapper for the NMEA GPS device
"""


class GPS:
    FIELDS = ['timestamp', 'lat', 'lon', 'altitude', 'spd_over_grnd_kmph']

    def __init__(self, port, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                 bytesize=serial.EIGHTBITS, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.parity = parity
        self.stopbits = stopbits
        self.bytesize = bytesize
        self.timeout = timeout
        self.ser = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            parity=self.parity,
            stopbits=self.stopbits,
            bytesize=self.bytesize,
            timeout=self.timeout
        )
        atexit.register(self.close)

    def close(self):
        self.ser.close()

    def read(self):
        # read until the next $ and check if its a GPGGA
        buff = StringIO()
        out = {k: None for k in self.FIELDS}
        start = datetime.now()
        while not all(out.values()):
            ins = self.ser.read(96)
            logging.warning("Read from GPS> {}".format(ins.decode('ascii','ignore')))
            if (datetime.now() - start).total_seconds() > self.timeout:
                break
            ins = re.sub(r'[\x00-\x1F]|\r|\n|\t', '', ins.decode('ASCII', 'ignore'))
            if ins == '$':
                break
            if ins != '':
                buff.write(ins)
        try:
            if buff.getvalue():
                msg = pynmea2.parse(buff.getvalue())
                for key in out:
                    if hasattr(msg, key):
                        out[key] = getattr(msg, key)
        except pynmea2.ParseError as e:
            print("Parse error:", e)
            return None
        for f in ['lat','lon']:
            if type(out[f]) == float:
                out[f] /= 100
        return out

    def readline(self):
        return self.ser.readline().decode('ascii').strip()
