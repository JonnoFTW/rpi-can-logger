#!/usr/bin/env python3
from rpi_can_logger.logger import TeslaSniffingLogger, SniffingOBDLogger, QueryingOBDLogger, tesla_pids, obd_pids
import can

OBD_REQUEST = 0x07DF
OBD_RESPONSE = 0x07E8


class Bus:
    """
    Custom bus
    """
    def __init__(self, msgs):
        self.msgs = msgs

    def recv(self):
        return self.msgs.pop()

    def send(self, msg):
        new_data = [0x04, 0x41, 0x0c, 0x84, 0x64, 00, 00, 00]
        self.msgs.insert(0, can.Message(arbitration_id=OBD_RESPONSE, data=new_data))


def test_tesla():
    print("running tesla test")
    pid2log = 0x0562
    msg = can.Message(data=[0x11, 0x52, 0x8E, 00], arbitration_id=pid2log)
    logger = TeslaSniffingLogger(Bus([msg]), [pid2log], tesla_pids, pid2log)
    print(logger.log())


def test_obd_query():
    print("running obd query test")
    msg = can.Message(data=[0x02, 0x01, 0x0c, 00, 00, 00, 00, 00], arbitration_id=OBD_REQUEST)
    logger = QueryingOBDLogger(Bus([msg]), [0x10c], obd_pids, 0x10c)
    print(logger.log())


def test_obd_sniff():
    print("Running obd sniff test")
    msg = can.Message(data=[0x02, 0x01, 0x0c, 00, 00, 00, 00, 00], arbitration_id=OBD_REQUEST)
    msg2 = can.Message(data=[0x04, 0x41, 0x0c, 0x84, 0x64, 00, 00, 00], arbitration_id=OBD_RESPONSE)
    logger = SniffingOBDLogger(Bus([msg, msg2]), [0x10c], obd_pids, 0x10c)
    print(logger.log())
