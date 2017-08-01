import can
import logging
import time
from rpi_can_logger.util import OBD_REQUEST, OBD_RESPONSE
from rpi_can_logger.logger import obd_pids

class BaseLogger:
    def __init__(self, bus, pids2log, pids, trigger):
        """
        :param bus: The CAN bus to read from
        :param pids2log:  The pids we want to read off the CAN bus
        :param pids: Information about all the pids
        :param trigger: The pid that when seen, will return everything seen on the buffer up until this point
        """
        self.bus = bus
        self.pids2log = pids2log
        self.pids = pids
        self.trigger = trigger

    def _make_buff(self):
        return {k: None for k in self.pids2log}


class BaseSnifferLogger(BaseLogger):
    @staticmethod
    def separate_can_msg(msg):
        raise NotImplementedError("Please use a subclass")

    def log(self):
        # keep reading until we get a log_trigger
        buff = {}
        while 1:
            msg = self.bus.recv()
            pid, obd_data = self.separate_can_msg(msg)

            if pid in self.pids2log:
                parsed = self.pids[pid]['parse'](obd_data)
                buff.update(parsed)
            if pid == self.trigger:
                return buff


class TeslaSniffingLogger(BaseSnifferLogger):
    @staticmethod
    def separate_can_msg(msg):
        return msg.arbitration_id, msg.data


class BaseOBDLogger(BaseLogger):
    @staticmethod
    def separate_can_msg(msg):
        try:
            return ((msg.data[1] - 0x40) * 256) + msg.data[2], msg.data[3:]
        except:
            return False, False


class SniffingOBDLogger(BaseOBDLogger, BaseSnifferLogger):
    pass


class QueryingOBDLogger(BaseOBDLogger):
    def __init__(self, bus, pids2log, pids, trigger):
        super().__init__(bus, pids2log, pids, trigger)
        self._determine_pids()

    def _parse_support_frame(self, msg):
        by = 0
        base = msg.data[2]
        for data in msg.data[3:7]:
            bits = format(data, '08b')
            for idx, v in enumerate(bits):
                if v == '1':
                    self.responds_to.add(0x0100 + base + idx + 1 + by * 8)
            by += 1

    def _determine_pids(self):
        """
        Determine which PIDs this vehicle will respond with
        :return:
        """
        self.responds_to = set()
        support_check = [0, 32, 64, 96]
        for i in support_check:
            msg = can.Message(extended_id=0, data=[2, 1, i, 0, 0, 0, 0, 0], arbitration_id=OBD_REQUEST)
            self.bus.send(msg)
            time.sleep(0.5)
            logging.warning("S> {}".format(msg))
        # read in the responses until you get them all
        logging.warning("Determining supported PIDs")
        count = 0
        while support_check:

            msg = self.bus.recv()
            logging.warning("R> {}".format(msg))
            count += 1
            if msg.arbitration_id == OBD_RESPONSE and list(msg.data[:2]) == [6, 0x41] and msg.data[2] in support_check:
                self._parse_support_frame(msg)
                logging.warning("support={} recv=".format(support_check, msg.data[2]))
                support_check.remove(msg.data[2])
            if count > 500:
                logging.warning("Could not determine PIDs in time")
                self.responds_to = None
        logging.warning("Supported PIDs are: {}".format([obd_pids[x]['name'] for x in sorted(self.responds_to)]))

    def log(self):
        # send a message asking for those requested pids
        out = {}
        for m in self.pids2log:
            if self.responds_to is not None and m in self.responds_to:
                out_msg = self.make_msg(m)
                logging.debug("S> {}".format(out_msg))
                self.bus.send(self.make_msg(m))

        # receive the pid back, (hoping it's the right one)
        #
        for i in range(128):
            msg = self.bus.recv()
            if msg.arbitration_id != 0x7e8:
                continue
            logging.debug("R> {}".format(msg))
            pid, obd_data = self.separate_can_msg(msg)

            # try and receive
            if pid in self.pids2log:
                out.update(self.pids[pid]['parse'](obd_data))
                break
        return out

    @staticmethod
    def make_msg(m):
        """
        :param m: the pid to make a CAN OBD request for
        :return: can.Message
        """
        mode, pid = divmod(m, 0x100)
        return can.Message(
            arbitration_id=OBD_REQUEST,
            data=[2, mode, pid, 0, 0, 0, 0, 0],
            extended_id=False
        )
