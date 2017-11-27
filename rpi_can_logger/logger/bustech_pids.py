from .fms_pids import FMSPID, _fms


def speed(args):
    pass


def state_of_charge(args):
    pass


def torque(args):
    pass


def ready_green(args):
    pass


def voltage(args):
    pass


def accel_pos(args):
    pass


def power(args):
    pass


_pids = [
    FMSPID(0xFe00, 'BUSTECH_SPEED', speed, 'km/h'),
    FMSPID(0xFE01, 'BUSTECH_SOC', state_of_charge, '%'),
    FMSPID(0xFE02, 'BUSTECH_TORQUE', torque, '%'),
    FMSPID(0xFE03, 'BUSTECH_ACCEL', accel_pos, '%'),
    FMSPID(0xFE04, 'BUSTECH_READY', ready_green, 'on/off'),
    FMSPID(0xFE05, 'BUSTECH_VOLTAGE', voltage, 'V'),
    FMSPID(0xFE06, 'BUSTECH_POWER', power, 'A'),
]
pids = {
    p.pid: {
        'name': p.name,
        'fields': p.fieldnames,
        'parse': p,
    } for p in _pids
}