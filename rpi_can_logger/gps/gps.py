from datetime import datetime
import serial
import pynmea2
import re
import atexit
import time

"""
Wrapper for the NMEA GPS device
"""


class GPS:
    FIELDS = ['timestamp', 'latitude', 'longitude', 'altitude', 'spd_over_grnd']
    EXTRA_FIELD = ['datestamp']
    KNOTS_PER_KMPH = 1.852

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
        for msg in """
24 45 49 47 50 51 2c 44 54 4d 2a 33 42 0d 0a b5 62 06 01 03 00 f0 0a 00 04 23
24 45 49 47 50 51 2c 47 42 53 2a 33 30 0d 0a b5 62 06 01 03 00 f0 09 00 03 21
24 45 49 47 50 51 2c 47 4c 4c 2a 32 31 0d 0a b5 62 06 01 03 00 f0 01 00 fb 11
24 45 49 47 50 51 2c 47 52 53 2a 32 30 0d 0a b5 62 06 01 03 00 f0 06 00 00 1b
24 45 49 47 50 51 2c 47 53 41 2a 33 33 0d 0a b5 62 06 01 03 00 f0 02 00 fc 13 
24 45 49 47 50 51 2c 47 53 54 2a 32 36 0d 0a b5 62 06 01 03 00 f0 07 00 01 1d
24 45 49 47 50 51 2c 47 53 56 2a 32 34 0d 0a b5 62 06 01 03 00 f0 03 00 fd 15
24 45 49 47 50 51 2c 56 54 47 2a 32 33 0d 0a b5 62 06 01 03 00 f0 05 00 ff 19
24 45 49 47 50 51 2c 5a 44 41 2a 33 39 0d 0a b5 62 06 01 03 00 f0 08 00 02 1f
24 45 49 47 50 51 2c 47 47 41 2a 32 37 0d 0a b5 62 06 01 03 00 f0 00 01 fb 10
24 45 49 47 50 51 2c 52 4d 43 2a 33 41 0d 0a b5 62 06 01 03 00 f0 04 01 ff 18
B5 62 06 08 06 00 C8 00 01 00 01 00 DE 6A B5 62 06 08 00 00 0E 30
""".splitlines():
            self.ser.write(bytes(map(lambda x: int(x, 16), msg.split(' '))))
            time.sleep(0.1)

    def close(self):
        self.ser.close()

    def read(self):
        out = {k: None for k in self.FIELDS + self.EXTRA_FIELD}
        start = datetime.now()
        while not all(out.values()):
            line = self._readline()
            if (datetime.now() - start).total_seconds() > self.timeout:
                break
            line = re.sub(r'[\x00-\x1F]|\r|\n|\t', "", line.decode('ascii', 'ignore'))
            cmd = line.split(',')[0]
            if cmd not in ['$GNGGA', '$GNRMC']:
                continue
            try:
                msg = pynmea2.parse(line)
                for key in out:
                    if hasattr(msg, key):
                        out[key] = getattr(msg, key)
            except pynmea2.ParseError as e:
                print("Parse error:", e)

        if out['datestamp'] is not None and out['timestamp'] is not None:
            out['timestamp'] = datetime.combine(out['datestamp'], out['timestamp'])
            del out['datestamp']
        if out['speed_over_grnd'] is not None:
            out['speed_over_grnd'] *= self.KNOTS_PER_KMPH
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
        return self._readline(b'$').decode('ascii', 'ignore').strip()
