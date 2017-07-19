from rpi_can_logger.logger import BluetoothLogger
from itertools import cycle
from math import sin, pi


def test_send():
    # make a new BluetoothLogger and send some OBD data
    btl = BluetoothLogger()
    btl.accept()

    # generate some data and send it

    btl.send("#speed,rpm,soc")

    x = range(1000)
    y = map(lambda v: sin(v * pi / 45) * 5000 + 5000, x)
    speeds = cycle(y)

    while 1:
        try:
            row = map(str, [next(speeds), 5000, 50])
            btl.send(",".join(row))
        except KeyboardInterrupt:
            print("Terminating")
            break

if __name__ == "__main__":
    test_send()