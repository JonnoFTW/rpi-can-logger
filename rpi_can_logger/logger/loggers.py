import can
import logging

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
        return ((msg.data[1] - 0x40) * 256) + msg.data[2], msg.data[3:]


class SniffingOBDLogger(BaseOBDLogger, BaseSnifferLogger):
    pass


class QueryingOBDLogger(BaseOBDLogger):
    def log(self):
        # send a message asking for those requested pids
        out = {}
        for m in self.pids2log:
            out_msg = self.make_msg(m)
            logging.debug("S> {}".format(out_msg))
            self.bus.send(self.make_msg(m))
            # receive the pid back, (hoping it's the right one)
            msg = self.bus.recv()
            logging.debug("R> {}".format(msg))
            pid, obd_data = self.separate_can_msg(msg)
            # try and receive
            if pid in self.pids2log:
                out.update(self.pids[pid]['parse'](obd_data))
        return out

    @staticmethod
    def make_msg(m):
        """
        :param m: the pid to make a CAN OBD request for
        :return: can.Message
        """
        mode, pid = divmod(m, 0x100)
        return can.Message(
            arbitration_id=0x7df,
            data=[2, mode, pid, 0, 0, 0, 0, 0],
            extended_id=False
        )
