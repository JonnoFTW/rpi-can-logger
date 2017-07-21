import bluetooth as bt
import logging
import threading
import queue
import time
from collections import deque


class BluetoothLogger(threading.Thread):
    uuid = "08be0e96-6ab4-11e7-907b-a6006ad3dba0"

    def __init__(self, queue_size=512, fields=[]):
        """
        This should be in its own thread
        """
        threading.Thread.__init__(self)
        server_sock = bt.BluetoothSocket(bt.RFCOMM)
        server_sock.bind(("", bt.PORT_ANY))
        server_sock.listen(1)
        self.fields = fields
        self.queue = deque(maxlen=queue_size) # queue.Queue(maxsize=queue_size)
        self.port = server_sock.getsockname()[1]
        self.queue_lock = threading.Lock()
        bt.advertise_service(server_sock, "RPi-Logger",
                             service_id=self.uuid,
                             service_classes=[self.uuid, bt.SERIAL_PORT_CLASS],
                             profiles=[bt.SERIAL_PORT_PROFILE],
                             )

        self.server_sock = server_sock

    def run(self):
        while 1:
            self._accept_and_send()

    def _accept_and_send(self):
        print("Waiting for connection on RFCOMM channel {}".format(self.port))
        self.client_sock, client_info = self.server_sock.accept()
        logging.warning("Accepted connection from: {}".format(client_info))

        self.client_sock.send("RPI-CAN-LOGGER!\n#{}!\n".format(','.join(self.fields)))
        while 1:
            msg = None
            if len(self.queue) > 0:
                msg = self.queue.popleft()
            else:
                time.sleep(0.01)
                continue
            if msg and self._is_connected():
                self.client_sock.send("{}!\n".format(msg))
            else:
                print("Disconnected from {} msg={} connected={}", format(client_info, msg, self.server_sock.connected))

    def _is_connected(self):
        try:
            self.client_sock.getpeername()
            return True
        except (bt.BluetoothError, AttributeError):
            return False

    def send(self, msg):
        self.queue.append(msg)

    def close(self):
        self.join()
