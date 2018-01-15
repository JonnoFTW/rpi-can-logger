import can
import time
import logging
from datetime import datetime

try:
    import RPi.GPIO as GPIO
except ImportError:
    from rpi_can_logger.stubs import GPIO

from rpi_can_logger.util import OBD_REQUEST, OBD_RESPONSE, sudo
from rpi_can_logger.logger import obd_pids, outlander_pids


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
        self.responds_to = []
        self.buff = {}

    def _make_buff(self):
        return {k: None for k in self.pids2log}


class BaseSnifferLogger(BaseLogger):
    @staticmethod
    def separate_can_msg(msg):
        raise NotImplementedError("Please use a subclass")

    def log(self):
        # keep reading until we get a log_trigger
        timeout = 0.5
        start_time = datetime.now()
        while 1:
            if (datetime.now() - start_time).total_seconds() > timeout:
                return self.buff
            msg = self.bus.recv(0.5)
            if msg is None:
                continue
            pid, obd_data = self.separate_can_msg(msg)

            if pid in self.pids2log:
                parsed = self.pids[pid]['parse'](obd_data)
                self.buff.update(parsed)
                # if pid == self.trigger:
                #     return buff


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
        self.responds_to = set()
        self.first_log = True
        self.log_timeout_first = 4
        self.log_timeout = self.log_timeout_first
        self.log_timeout_tail = 1.5
        self.errors = 0

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
        support_check = [0, 32, 64, 96]
        logging.warning("Determining supported PIDs")
        start = datetime.now()
        count = 0
        max_wait_sec = 2
        while len(support_check):
            msg = can.Message(extended_id=0, data=[2, 1, support_check[0], 0, 0, 0, 0, 0], arbitration_id=OBD_REQUEST)
            logging.warning("S> {}".format(msg))
            self.bus.send(msg)
            while 1:
                recvd = self.bus.recv(0.2)
                if recvd is None:
                    if (datetime.now() - start).total_seconds() > max_wait_sec:
                        logging.warning("Could not determine PIDs in time")
                        return
                    continue
                if recvd.arbitration_id == OBD_RESPONSE and list(recvd.data[:2]) == [6, 0x41] and recvd.data[
                    2] in support_check:
                    logging.warning("R> {}".format(recvd))
                    self._parse_support_frame(recvd)
                    support_check.remove(recvd.data[2])
                    break

        logging.warning(
            "Supported PIDs are: {}".format(','.join([obd_pids[x]['name'] for x in sorted(self.responds_to)])))
        # self.pids2log = self.pids2log & self.responds_to
        # logging.warning("Only logging: {}".format(','.join([obd_pids[x]['name'] for x in sorted(self.pids2log)])))

    def log(self):
        # send a message asking for those requested pids
        out = {}
        time.sleep(0.5)
        pids_responded = []
        for m in self.pids2log:
            if m in outlander_pids:
                outlander_data = self._log_outlander(m)
                if outlander_data != {}:
                    pids_responded.append(m)
                    out.update(outlander_data)
            else:
                self.bus.set_filters([{'can_id': 0x07e8, 'can_mask': 0xffff}])

                # if self.responds_to is not None and m in self.responds_to:
                out_msg = self.make_msg(m)
                # logging.warning("S> {}".format(out_msg))
                # self.bus.send(out_msg)

                # receive the pid back, (hoping it's the right one)
                #
                count = 0
                start = datetime.now()
                while count < 5:
                    count += 1
                    self.bus.send(out_msg)
                    msg = self.bus.recv(0.4)
                    # logging.warning(self.pids[m]['name']+str(msg))
                    if msg is None:
                        # logging.warning("No message")
                        if (datetime.now() - start).total_seconds() > self.log_timeout:
                            print("Query timeout")
                            break
                        continue
                    if msg.arbitration_id == OBD_RESPONSE:
                        #                       logging.warning("R> {}".format(msg))

                        pid, obd_data = self.separate_can_msg(msg)
                        #  logging.warning("PID={}, pids2log={}, pid in?={}".format(pid, self.pids2log, pid in self.pids2log))
                        # try and receive
                        if pid in self.pids2log:
                            out.update(self.pids[pid]['parse'](obd_data))
                            pids_responded.append(pid)
                            break
                            #                           logging.warning(out)
                        if len(out) == len(self.pids2log):
                            logging.debug("got all PIDs")
                            break
                            #      logging.warning(out)
                            #        logging.warning("finished log loop")
        if self.first_log:
            # only log those that get a response the first time around
            # self.pids2log = set(pids_responded)
            logging.warning("Setting PIDs to {}".format(",".join(self.pids[p]['name'] for p in self.pids2log)))
            self.first_log = False
            self.log_timeout = self.log_timeout_tail
        #        print(out)
        if out == {}:
            self.errors += 1
            if self.errors == 5:
                logging.warning("Shutting down after failing to receive CAN data")
                sudo("shutdown -h 0")
        else:
            self.errors = 0
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

    def _log_outlander(self, request_arb_id):
        p = outlander_pids[request_arb_id]
        pid = p['pid']
        req_msg = can.Message(extended_id=0, data=[2, 0x21, pid, 0, 0, 0, 0, 0],
                              arbitration_id=request_arb_id)

        ctl_msg = can.Message(arbitration_id=request_arb_id, extended_id=0,
                              data=[0x30, 0x0, 0x0, 0, 0, 0, 0, 0])

        buf = bytes()
        num_bytes = 0
        multiline = True

        # print("S>", req_msg)
        #        self.bus.set_filters()
        self.bus.set_filters([{'can_id': p['response'], 'can_mask': 0xffff}])

        self.bus.send(req_msg)

        for i in range(1000):

            recvd = self.bus.recv(0.5)
            if recvd is None:
                #                print("got none")
                continue

            if recvd.arbitration_id == p['response']:
                #               print("R>",i, recvd)

                sequence = recvd.data[0]
                if sequence == 0x10:
                    self.bus.send(ctl_msg)
                    self.bus.send(req_msg)

                    buf = recvd.data[4:]
                    multiline = True
                    num_bytes = recvd.data[1] - 2
                    #                  print("Multiline bytes expected", num_bytes)
                    # send control frame to receive rest of multiline message
                elif multiline:
                    buf += recvd.data[1:]
                    #                 print(len(buf), buf)
                    if len(buf) >= num_bytes:
                        return p['parse'](buf)
                else:
                    return p['parse'](recvd.data)
                    # print("nothing")
        return {}


class FMSLogger(BaseSnifferLogger):
    @staticmethod
    def separate_can_msg(msg):
        return (msg.arbitration_id >> 8) & 0xffff, msg.data

    def __init__(self, bus, pids2log, pids, trigger):
        super().__init__(bus, pids2log, pids, trigger)
        # put the CAN loggers in 250k mode
        # need to use extended ID
        self.shutdown = False
        self.buff = {}

    def log(self):
        # keep reading until we get a log_trigger
        timeout = 1
        start_time = datetime.now()
        fms_ccvs = 'FMS_CRUISE_CONTROL_VEHICLE_SPEED (km/h)'
        time.sleep(0.5)
        while 1:
            if (datetime.now() - start_time).total_seconds() > timeout:
                return self.buff
            msg = self.bus.recv(0.5)
            if msg is None:
                continue
            pid, obd_data = self.separate_can_msg(msg)

            if pid in self.pids2log:
                parsed = self.pids[pid]['parse'](obd_data)
                self.buff.update(parsed)
                if fms_ccvs in self.buff and self.buff[fms_ccvs] > 200:
                    del self.buff[fms_ccvs]
                    # don't trigger a log if we get an invalid value
                    continue

            if pid == self.trigger:
                return self.buff


class BustechLogger(BaseSnifferLogger):
    def __init__(self, bus, pids2log, pids, trigger):
        super().__init__(bus, pids2log, pids, trigger)
        self.shutdown = False
        print("Logging bustech")
        self.fast_log = True

    @staticmethod
    def separate_can_msg(msg):
        return msg.arbitration_id, msg.data

    def log(self):
        buff = {}
#        self.bus.set_filter([
#            {'can_id': 0x0109, 'can_mask': 0xffff},
#             {'can_id': 0x0110, 'can_mask': 0xffff}])
        start = datetime.now()
        timeout = 0.5
        bustech_ready_pid = "BUSTECH_BATTERY (Ready)"

        while 1:
            if (datetime.now() - start).total_seconds() > timeout:
                return buff
            msg = self.bus.recv(0.1)
#            print(msg)
            if msg is None:
                continue
            pid, can_bytes = self.separate_can_msg(msg)
            if pid in self.pids2log:
                parsed = self.pids[pid]['parse'](can_bytes)
                buff.update(parsed)
                if bustech_ready_pid in buff:
                    self.fast_log = buff[bustech_ready_pid] == 1
                    # if we are switching from slow to fast logging, we need to log it as a new trip
                    buff['_reset_trip'] = 1
 #           if self.fast_log == 0:
#                time.sleep(10)
