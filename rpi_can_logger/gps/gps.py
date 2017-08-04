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
            line = self._readline()
            # logging.warning("Read from GPS> {}".format(ins.decode('ascii', 'ignore')))
            if (datetime.now() - start).total_seconds() > self.timeout:
                break
            line = re.sub(r'[\x00-\x1F]|\r|\n|\t', "", line.decode('ASCII', 'ignore'))
            #if ins == '$':
            #    break
            #if ins != '':
            #    buff.write(ins)
            try:
                #if buff.getvalue():
                msg = pynmea2.parse(line)                    
                for key in out:
                    if hasattr(msg, key):
                            out[key] = getattr(msg, key)
            except pynmea2.ParseError as e:
                print("Parse error:", e)
                
        for f in ['lat', 'lon']:
            if type(out[f]) == float:
                out[f] /= 100.
        return out

    def _readline(self, eol=b'\r'):
        leneol = len(eol)
        line = bytearray()
        while True:
            c = self.ser.read(1)
            if c:
                line += c
                if line[-leneol:] == eol:
                    break
            else:
                break
        return bytes(line)
    def readline(self):
        return self.ser.readline().decode('ascii').strip()
