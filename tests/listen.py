import can
import atexit

bus = can.interface.Bus(channel='can0', bustype='socketcan_native')
atexit.register(bus.shutdown)
while 1:
    print(bus.recv())
