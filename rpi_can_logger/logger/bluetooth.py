import bluetooth as bt
from twisted.internet import abstract, fdesc

class BluetoothLogger:
    uuid = "08be0e96-6ab4-11e7-907b-a6006ad3dba0"

    def __init__(self):
        server_sock = bt.BluetoothSocket(bt.RFCOMM)
        server_sock.bind(("", bt.PORT_ANY))
        server_sock.listen(1)

        port = server_sock.getsockname()[1]

        bt.advertise_service(server_sock, "RPi-Logger",
                             service_id=self.uuid,
                             service_classes=[self.uuid, bt.SERIAL_PORT_CLASS],
                             profiles=[bt.SERIAL_PORT_PROFILE],
                             )

        print("Waiting for connection on RFCOMM channel {}".format(port))
