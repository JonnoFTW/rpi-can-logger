#!/usr/bin/env python3
import os

print(os.environ['PYTHONPATH'])

from rpi_can_logger.logger import BluetoothLogger
from math import sin, pi
from itertools import cycle
import time

import yaml

with open('../example_obd_querying_conf.yaml', 'r') as infile:
    conf = yaml.load(infile)

password = conf['bluetooth-pass']


def test_send():
    btl = BluetoothLogger(fields=["speed", "rpm", "soc"], password=password)
    btl.start()

    # generate some data and send it
    x = range(1000)
    y = map(lambda v: sin(v * pi / 45) * 5000 + 5000, x)
    speeds = cycle(y)
    print("Sending dummy data")
    while 1:
        try:
            row = map(str, [round(next(speeds), 2), 5000, 50])
            btl.send(",".join(row))
            time.sleep(1)
        except KeyboardInterrupt:
            print("Terminating")
            break
    btl.join()


if __name__ == "__main__":
    test_send()
