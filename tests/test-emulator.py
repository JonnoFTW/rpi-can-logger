#!/usr/bin/env python3
import can
import atexit
from matplotlib import pyplot as plt

can.rc['interface'] = 'pcan'
can.rc['channel'] = 'PCAN_USBBUS1'

bus = can.interface.Bus()
atexit.register(bus.shutdown)

# send a message on the bus and hope that they emulator sends it back
out_msg = can.Message(data=[2, 9, 0x02, 0, 0, 0, 0, 0],
                      arbitration_id=0x7df,
                      extended_id=0)

"""
Queries are sent on 07df
Responses are on    07e8

"""


# plt.ion()
# from collections import deque
# import numpy as np
# xmax = 300
# xs = np.arange(xmax)
# ydata = deque([0], maxlen=xmax)
# ax1 = plt.axes()
# line, = plt.plot(ydata)
# plt.xlim(0,xmax)
# plt.ylim(0, 10000)
# plt.show()
# bus.send(out_msg)
# print("S>", out_msg)
def get_vin(bus):
    vin_request_message = can.Message(data=[2, 9, 0x02, 0, 0, 0, 0, 0],
                                      arbitration_id=0x7df,
                                      extended_id=0)
    bus.send(vin_request_message)
    # keep receving otherwise timeout
    vin = ""

    def makeVin(data):
        return ''.join(map(chr, data))

    for i in range(128):
        msg = bus.recv()
        if msg.arbitration_id == 0x07e8 and msg.data[2:4] == bytearray([0x49, 0x02]):
            vin += makeVin(msg.data[-3:])
            nxtmsg = can.Message(extended_id=0, arbitration_id=0x07e0, data=[0x30, 0, 4, 0, 0, 0, 0, 0])
            bus.send(nxtmsg)
        elif msg.arbitration_id == 0x07e8 and msg.data[0] == 0x21:
            vin += makeVin(msg.data[1:])
        elif msg.arbitration_id == 0x07e8 and msg.data[0] == 0x22:
            vin += makeVin(msg.data[1:])
            return vin
    return "NO VIN"


print(get_vin(bus))

while 1:
    msg = bus.recv()
    print(msg)

    # print(list(map(hex, msg.data)))
    # if msg.arbitration_id == 0x07e8:
    #     pid = msg.data[2]
    #     val = msg.data[3:1+msg.data[0]]
    #     # print("R>", msg)
    #     if pid == 0x0c:
    #         rpm = (val[0]*256 + val[1]) / 4
    #         ydata.append(rpm)
    #         line.set_xdata(np.arange(len(ydata)))
    #         line.set_ydata(ydata)
    #         plt.draw()
    #         plt.pause(0.01)
