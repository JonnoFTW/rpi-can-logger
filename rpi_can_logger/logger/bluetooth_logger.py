import bluetooth as bt
import logging
from twisted.internet import abstract, fdesc


class BluetoothLogger:
    uuid = "08be0e96-6ab4-11e7-907b-a6006ad3dba0"

    def __init__(self):

        server_sock = bt.BluetoothSocket(bt.RFCOMM)
        server_sock.bind(("", bt.PORT_ANY))
        server_sock.listen(1)

        self.port = server_sock.getsockname()[1]

        bt.advertise_service(server_sock, "RPi-Logger",
                                    service_id=self.uuid,
                                    service_classes=[self.uuid, bt.SERIAL_PORT_CLASS],
                                    profiles=[bt.SERIAL_PORT_PROFILE],
                                    )

        self.server_sock = server_sock

    def accept(self):
        print("Waiting for connection on RFCOMM channel {}".format(self.port))
        self.client_sock, client_info = self.server_sock.accept()
        logging.warning("Accepted connection from: {}".format(client_info))

    def send(self, msg):
        self.client_sock.send(msg+"!")

    def close(self):
        self.server_sock.close()


class BluezSocket(abstract.FileDescriptor):
    """
    Beware: This class might throw bluetooth.BluetoothError Exceptions under several circumstances
    (e.g. when the other end is out of range).
    So you might want to catch these or they may crash your program.
    """

    def __init__(self, protocol, device_id, reactor):
        """
        protocol: A twisted IProtocol instance
        device_id: A Bluetooth "mac-address" as string (e.g. '00:11:22:33:44:55')
        reactor: a reactor
        """
        self.connected = False
        self.device_id = device_id
        self.protocol = protocol
        self.reactor = reactor

        abstract.FileDescriptor.__init__(self, reactor)

        self.sock = bt.BluetoothSocket(bt.RFCOMM)
        self.sock.connect((self.device_id, 1))
        self.connected = True
        self.sock.setblocking(0)

        self.protocol.makeConnection(self)
        self.startReading()

    def fileno(self):
        return self.sock.fileno()

    def writeSomeData(self, data):
        return fdesc.writeToFD(self.fileno(), data)

    def doRead(self):
        return fdesc.readFromFD(self.fileno(), self.protocol.dataReceived)

    def connectionLost(self, reason):
        abstract.FileDescriptor.connectionLost(self, reason)
        self.sock.close()
        self.connected = False
        self.protocol.connectionLost(reason)

if __name__ == "__main__":
    from math import sin, pi
    from itertools import cycle
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
