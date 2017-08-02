import bluetooth as bt
import logging
import threading
import queue
import time
from collections import deque
from rpi_can_logger.util import get_ip


class BluetoothLogger(threading.Thread):
    uuid = "08be0e96-6ab4-11e7-907b-a6006ad3dba0"

    def __init__(self, queue_size=512, fields=[], bt_commands={}):
        """
        This should be in its own thread
        """
        threading.Thread.__init__(self)
        self.fields = fields
        self.queue_size = queue_size
        self.bt_commands = bt_commands
        self._finished = False

    def run(self):
        self.recv_queue = deque(maxlen=self.queue_size)
        self.queue = deque(maxlen=self.queue_size)  # queue.Queue(maxsize=queue_size)
        self._recv_thread = BluetoothReceiver(self.recv_queue, bt_commands=self.bt_commands, btl=self)
        self._recv_thread.start()
        while 1:
            if self._finished:
                break
            self._accept_and_send()

    def _accept_and_send(self):
        server_sock = bt.BluetoothSocket(bt.RFCOMM)
        server_sock.bind(("", bt.PORT_ANY))
        server_sock.listen(1)

        self.fields = self.fields

        self.port = server_sock.getsockname()[1]
        self.queue_lock = threading.Lock()
        try:
            bt.advertise_service(server_sock, "RPi-Logger",
                                 service_id=self.uuid,
                                 service_classes=[self.uuid, bt.SERIAL_PORT_CLASS],
                                 profiles=[bt.SERIAL_PORT_PROFILE],
                                 )
        except bt.BluetoothError as e:
            logging.warning("Failed to start bluetooth: {}".format(e))
            import _thread
            _thread.interrupt_main()

        self.server_sock = server_sock
        print("Waiting for connection on RFCOMM channel {}".format(self.port))
        self.client_sock, client_info = self.server_sock.accept()
        logging.warning("Accepted connection from: {}".format(client_info))
        self.client_sock.settimeout(0.3)
        self.client_sock.send("RPI-CAN-LOGGER!\n#{}!\n".format(','.join(self.fields)))
        self.send("$ip={}".format(get_ip()))
        while 1:
            connected = self._is_connected()
            if self._finished:
                return
            if connected:
                # Try and receive for a little bit
                received = None
                try:
                    received = self.client_sock.recv(512)
                except bt.BluetoothError as e:
                    pass
                if received:
                    received = received.decode('ascii', 'ignore')
                    print("BTR>", received)
                    self.recv_queue.append(received)
                while len(self.queue) > 0:
                    msg = self.queue.popleft()
                    if msg:
                        try:
                            self.client_sock.send("{}!\n".format(msg.strip()))
                        except bt.BluetoothError as e:
                            pass
            else:
                print("Disconnected from {}".format(client_info))
                break

    def _is_connected(self):
        try:
            self.client_sock.getpeername()
            return True
        except (bt.BluetoothError, AttributeError):
            return False

    def send(self, msg):
        self.queue.append(msg)

    def close(self):
        self._finished = True
        self._recv_thread.close()
        self.join()


class BluetoothReceiver(threading.Thread):

    def __init__(self, recv_queue, bt_commands, btl):
        super().__init__()
        self.btl = btl
        self.bt_commands = bt_commands
        self._finished = False
        self.recv_queue = recv_queue

    def run(self):
        while not self._finished:
            while len(self.recv_queue) > 0:
                cmd = self.recv_queue.popleft()
                pieces = cmd.split('=')
                try:
                    bt_reply = self.bt_commands.get(pieces[0].lower().strip(), None)(*pieces[1:])
                    if bt_reply is not None:
                        self.btl.send("{}={}".format(pieces[0], bt_reply))
                except TypeError as e:
                    print(e)
                    self.btl.send("{}=INVALID_ARG".format(pieces[0]))
            time.sleep(1)

    def close(self):
        self._finished = True
