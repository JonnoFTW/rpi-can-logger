import can
import logging
import time
from datetime import datetime
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
#        self._determine_pids()
        self.responds_to = None

    def _parse_support_frame(self, msg):
        by = 0
        base = msg.data[2]
        for data in msg.data[3:7]:
            bits = format(data, '08b')
            for idx, v in enumerate(bits):
                if v == '1':
                    pid = 0x0100 + base + idx + 1 + by * 8
                    if pid in obd_pids:
                        self.responds_to.add(pid)
            by += 1

    def _determine_pids(self):
        """
        Determine which PIDs this vehicle will respond with
        :return:
        """
        self.responds_to = set()
        support_check = [0, 32, 64]
        logging.warning("Determining supported PIDs")
        start = datetime.now()
        count = 0
        while len(support_check):
            time.sleep(0.5)
            msg = can.Message(extended_id=0, data=[2, 1, support_check[0], 0, 0, 0, 0, 0], arbitration_id=OBD_REQUEST)
            logging.warning("S> {}".format(msg))
            self.bus.send(msg)
            while 1:
                recvd = self.bus.recv()
                if recvd.arbitration_id == OBD_RESPONSE:
#                    logging.warning("R> {}".format(recvd))
                    break
                if recvd.arbitration_id == OBD_RESPONSE and list(recvd.data[:2]) == [6, 0x41] and recvd.data[2] in support_check:
                    self._parse_support_frame(msg)
                    support_check.remove(msg.data[2])
                if (datetime.now() - start).total_seconds() > max_wait_sec:
                    logging.warning("Could not determine PIDs in time")
                    self.responds_to = None
                    return
        logging.warning("Supported PIDs are: {}".format(','.join([obd_pids[x]['name'] for x in sorted(self.responds_to)])))
        self.pids2log = self.pids2log & self.responds_to
        logging.warning("Only logging: {}".format(','.join([obd_pids[x]['name'] for x in sorted(self.pids2log)])))

    def log(self):
        # send a message asking for those requested pids
        out = {}
        for m in self.pids2log:
            #if self.responds_to is not None and m in self.responds_to:
                out_msg = self.make_msg(m)
                logging.debug("S> {}".format(out_msg))
                self.bus.send(self.make_msg(m))

        # receive the pid back, (hoping it's the right one)
        #
                count = 0
                while count < 128:
                    count += 1
                    msg = self.bus.recv(timeout=0.1)
                    if msg is None:
                        continue
                    if msg.arbitration_id == OBD_RESPONSE:
                        logging.warning("R> {}".format(msg))
     
                        pid, obd_data = self.separate_can_msg(msg)
    
                        # try and receive
                        if pid in self.pids2log:
                            out.update(self.pids[pid]['parse'](obd_data))
    
                        if len(out) == len(self.pids2log):
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
