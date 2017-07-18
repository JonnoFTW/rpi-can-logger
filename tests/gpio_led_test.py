#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time


def setup_GPIO():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(7, GPIO.OUT)
    GPIO.setup(37, GPIO.OUT)


def led1(on_off):
    GPIO.output(7, bool(on_off))


def led2(on_off):
    GPIO.output(37, bool(on_off))


if __name__ == "__main__":
    sleep_time = 0.25
    setup_GPIO()
    while 1:
        try:
            led1(1)
            led2(1)
            print("Sleeping for {}s".format(sleep_time))
            time.sleep(sleep_time)
            led2(0)
            led1(0)
            print("Sleeping for {}s".format(sleep_time))
            time.sleep(sleep_time)
        except KeyboardInterrupt:
            break

GPIO.cleanup()
