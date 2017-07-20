import bluetooth as bt
import logging
import threading
import queue


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
        self.queue = queue.Queue(maxsize=queue_size)
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
            if not self._is_connected():
                return
            self.queue_lock.acquire()
            msg = self.queue.get()
            self.queue_lock.release()
            self.client_sock.send("{}!\n".format(msg))

    def _is_connected(self):
        try:
            self.client_sock.getpeername()
            return True
        except (bt.BluetoothError, AttributeError):
            return False

    def send(self, msg):
        if not self._is_connected():
            return
        print("putting message:", msg)
        self.queue_lock.acquire()
        self.queue.put(msg)
        self.queue_lock.release()

    def close(self):
        self.join()


if __name__ == "__main__":
    from math import sin, pi
    from itertools import cycle

    btl = BluetoothLogger(fields=["speed", "rpm", "soc"])
    btl.start()

    # generate some data and send it
    x = range(1000)
    y = map(lambda v: sin(v * pi / 45) * 5000 + 5000, x)
    speeds = cycle(y)
    print("Sending dummy data")
    while 1:
        try:
            row = map(str, [next(speeds), 5000, 50])
            btl.send(",".join(row))
        except KeyboardInterrupt:
            print("Terminating")
            break
    btl.join()
