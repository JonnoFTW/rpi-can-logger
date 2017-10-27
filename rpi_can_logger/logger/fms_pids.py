from itertools import cycle
from datetime import datetime, timezone
import struct

"""
FMS Bus PIDs as described in:
http://www.fms-standard.com/Bus/down_load/fms_document_ver03_vers_14_09_2012.pdf

"""


class FMSPID:

    def __init__(self, pid: int, name: str, parser, fields: [list, str]):
        """
        A class representing an FMSPID and its conversion
        :param pid: The PID
        :param name:  A friendly name of this PID
        :param parser: a function that turns a byte array of at most length 8 into one or more readable values
        :param fields: the friendly name of the outputs of this PID eg. 'RPM'
        """
        self.pid = pid
        self.name = name
        self.parser = parser
        if type(fields) is str:
            self.fields = [fields]
        else:
            self.fields = fields
        self.fieldnames = ['{} ({})'.format(name, unit) for pid_name, unit in
                           zip(cycle([self.name]), self.fields)]

    def __call__(self, msg):
        parsed = self.parser(msg)
        # if parsed is None:
        #     return None
        if type(parsed) not in [tuple, list]:
            parsed = (parsed,)
        return {'{} ({})'.format(pid_name, unit): val for pid_name, val, unit in
                zip(cycle([self.name]), parsed, self.fields)}


def _fms(msg, gain, offset, sbyte, ebyte=None):
    """
    Extract a number from a series of bytes, a number 1,2,4 bytes long
    :param msg: the series of bytes
    :param gain: the  value to multiply the value by
    :param offset: the offset of the value
    :param sbyte:  the start byte of the value (indexed from 1)
    :param ebyte:  the end byte of the value (indexed from 1), if None, assume the value is 1 byte long
    :return:
    """
    if ebyte is None:
        return msg[sbyte - 1] * gain + offset
    if ebyte is None:
        ebyte = sbyte + 1
    sbyte -= 1
    # interpret bytes as n-byte unsigned int,
    # multiply by gain + offset
    byte_len = ebyte - sbyte
    fmt = {
        1: '>B',
        2: '<H',
        4: '<I'
    }

    return struct.unpack(fmt[byte_len], msg[sbyte: ebyte])[0] * gain + offset


def fuel_consumption(msg):
    return _fms(msg, 0.5, 0, 5, 8)


def dash_display(msg):
    return msg[1] * 0.4


def eec1(msg):
    return _fms(msg, 1, -125, 3), _fms(msg, 1, 0, 4, 5) // 8


def engine_hours(msg):
    return _fms(msg, 0.05, 0, 1, 4)


def vehicle_id(msg):
    return msg.decode('ascii')


def hr_distance(msg):
    return _fms(msg, 5, 0, 1, 4)


def tachograph(msg):
    return _fms(msg, 1, 0, 7, 8) // 256


def engine_temp(msg):
    return _fms(msg, 1, -40, 1)


def eec2(msg):
    return _fms(msg, 0.4, 0, 2)


def vw(msg):
    return _fms(msg, 0.5, 0, 2, 3)


def ambient_conditions(msg):
    return _fms(msg, 0.03125, -273, 4, 5)


def driver_id(msg):
    return "NOT IMPLEMENTED"


def fuel_economy(msg):
    return _fms(msg, 0.05, 0, 1, 2), _fms(msg, 1 / 512., 0, 3, 4)


def air_supply_pressure(msg):
    return _fms(msg, 8, 0, 3), _fms(msg, 8, 0, 4)


def hr_fuel_consumption(msg):
    return _fms(msg, 0.001, 0, 5, 8)


def at1t1i(msg):
    return _fms(msg, 0.4, 0, 1)


conds = {
    x: c for x, c in [
        ((0, 0, 0), 'off'),
        ((0, 0, 1), 'Cond_red'),
        ((0, 1, 0), 'Cond_yellow'),
        ((0, 1, 1), 'Cond_info'),
        ((1, 0, 0), 'reserved'),
        ((1, 0, 1), 'reserved'),
        ((1, 1, 0), 'reserved'),
        ((1, 1, 1), 'not_available')]
}


def bits_from_byte(bt, s, e):
    return conds[list(bin(int.from_bytes(bt, 'big'))[2:])]


def tts(msg):
    return [1111] + [x for t in
                     [(bits_from_byte(msg[i], 1, 4), msg[i], 5, 8) for i in range(16)]
                     for x in t
                     ]


def ccvs(msg):
    return _fms(msg, 1 / 256., 0, 2, 3)


def serv(msg):
    return _fms(msg, 5, -160635, 2, 3)


def ptode(msg):
    return bin(msg[6])[-2:]


def cvw(msg):
    return _fms(msg, 10, 0, 3, 4)


def acc_ped_pos(msg):
    return _fms(msg, 1, -125, 2)


def erc1(msg):
    return _fms(msg, 1, -125, 2)


def door_control_1(msg):
    return bin(msg[0])[2:]


def door_control_2(msg):
    return ' '.join(map(hex, msg))


def time_date(msg):
    if msg == b'\xff\xff\xff\xff\xff\xff\xff\xff':
        return 'err'
    return datetime(
        year=msg[5] + 1985,
        month=msg[3],
        day=msg[4] // 4 + 1,
        hour=msg[2],
        minute=msg[1],
        second=msg[0] // 4,
        tzinfo=timezone.utc

    ).isoformat()


def alternator_speed(msg):
    return bin(msg[3])[2:]


def asc4(msg):
    return list(_fms(msg, 0.1, 0, i) for i in range(1, 9))


def etc2(msg):
    return _fms(msg, 1, -125, 1), _fms(msg, 1, -125, 4)


def fms_sw(msg):
    return "{}{}.{}{}".format(*msg[1:5].decode('ascii'))


vin_len = None
vin_packets = None
vin_str = ""


def vehicle_id_bam(msg):
    global vin_len, vin_packets, vin_str
    vin_len = msg[1]
    vin_packets = msg[3]
    vin_str = ""


def vehicle_id_part(msg):
    global vin_str
    return
    if vin_len is not None:
        if msg[0] == vin_packets:
            vin_str += msg[1:vin_len - len(vin_str) + 1].decode('ascii')
            return vin_str
        else:
            # find the index of 0xff and go to there
            try:
                last_index = msg.index(b'\xff')
                vin_str += msg[1:last_index-1].decode('ascii')
            except ValueError:
                vin_str += msg[1:].decode('ascii')

_pids = [
    FMSPID(0xFEE9, 'FMS_FUEL_CONSUMPTION', fuel_consumption, 'L'),
    FMSPID(0xFEFC, 'FMS_DASH_DISPLAY', dash_display, 'FuelLvl%'),
    FMSPID(0xF004, 'FMS_ELECTRONIC_ENGINE_CONTROLLER_1', eec1, ['EngineTorque%', 'RPM']),
    FMSPID(0xF003, 'FMS_ELECTRONIC_ENGINE_CONTROLLER_2', eec2, 'AccPedalPos%'),
    FMSPID(0xFEE5, 'FMS_ENGINE_HOURS', engine_hours, 'H'),
    FMSPID(0xFEEC, 'FMS_VEHICLE_IDENTIFICATION', vehicle_id, ''),
    FMSPID(0xFEC1, 'FMS_HIGH_RESOLUTION_DISTANCE', hr_distance, 'm'),
    FMSPID(0xFE6C, 'FMS_TACHOGRAPH', tachograph, 'km/h'),
    FMSPID(0xFEEE, 'FMS_ENGINE_TEMP', engine_temp, '°C'),
    FMSPID(0xFEF5, 'FMS_AMBIENT_CONDITIONS', ambient_conditions, '°C'),
    FMSPID(0xFE6B, 'FMS_DRIVER_IDENTIFICATION', driver_id, ''),
    FMSPID(0xFEF2, 'FMS_FUEL_ECONOMY', fuel_economy, ['L/h', 'km/L']),
    FMSPID(0xFEAE, 'FMS_AIR_SUPPLY_PRESSURE', air_supply_pressure, ['kPa', 'kPa']),
    FMSPID(0xFD09, 'FMS_HIGH_RESOLUTION_FUEL_CONSUMPTION', hr_fuel_consumption, 'L'),
    FMSPID(0xFE56, 'FMS_AFTERTREATMENT_1_DIESEL_EXHAUST_FLUID_TANK_1_INFORMATION', at1t1i, '%'),
    FMSPID(0xFD7D, 'FMS_TELL_TALE_STATUS', tts, ['TTS_{}'.format(i) for i in range(16)]),
    FMSPID(0xFEF1, 'FMS_CRUISE_CONTROL_VEHICLE_SPEED', ccvs, 'km/h'),
    FMSPID(0xFEEA, 'FMS_VEHICLE_WEIGHT', vw, 'kg'),
    FMSPID(0xFEC0, 'FMS_SERVICE_INFORMATION', serv, 'km'),
    FMSPID(0xFDA4, 'FMS_PTO_DRIVE_ENGAGEMENT', ptode, 'bits'),
    FMSPID(0xFE70, 'FMS_COMBINATION_VEHICLE_WEIGHT', cvw, 'kg'),
    FMSPID(0xF000, 'FMS_ELECTRONIC_RETARDER_CONTROLLER_1', erc1, 'RetarderTorque%'),
    FMSPID(0xFE4E, 'FMS_DOOR_CONTROL_1', door_control_1, 'bytes'),
    FMSPID(0xFDA5, 'FMS_DOOR_CONTROL_2', door_control_2, 'bytes'),
    FMSPID(0xFEE6, 'FMS_TIME_DATE', time_date, 'datetime'),
    FMSPID(0xFDD1, 'FMS_CAPABILITIES', fms_sw, 'SWvers'),
    FMSPID(0xFED5, 'FMS_ALTERNATOR_SPEED', alternator_speed, 'str'),
    FMSPID(0xECFF, 'FMS_BAM', vehicle_id_bam, ''),
    FMSPID(0xEBFF, 'FMS_VEHICLE_ID', vehicle_id_part, 'str'),
    FMSPID(0xF005, 'FMS_ELECTRONIC_TRANSMISSION_CONTROL_2', etc2, ['SelectedGear', 'CurrentGear']),
    FMSPID(0xFE58, 'FMS_AIR_SUSPENSION_CONTROL_4', asc4, ['Bellow Pressure Front Axle Left',
                                                            'Bellow Pressure Front Axle Left',
                                                            'Bellow Pressure Front Axle Right',
                                                            'Bellow Pressure Front Axle Right',
                                                            'Bellow Pressure Rear Axle Left',
                                                            'Bellow Pressure Rear Axle Left',
                                                            'Bellow Pressure Rear Axle Right',
                                                            'Bellow Pressure Rear Axle Right'
                                                            ]),
]

pids = {
    p.pid: {
        'name': p.name,
        'fields': p.fieldnames,
        # 'fieldnames': p.fieldnames,
        'parse': p,
    } for p in _pids
}
