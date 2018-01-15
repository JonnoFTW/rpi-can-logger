from .fms_pids import FMSPID, _fms


def battery(args):
    return [
        _fms(args, 0.01, 0, 1, 2),
        _fms(args, 0.05, -1000, 3, 4),
        _fms(args, 0.02, 0, 5, 6),
        _fms(args, 1,    0, 7, 7),
    ]


def engine(args):
    return [
        _fms(args, 0.1, -100, 1, 2),
        _fms(args, 0.01, 0, 3, 4),
        _fms(args, 0.1, -500, 5, 6),
    ]


_pids = [
    FMSPID(0x0109, 'BUSTECH_BATTERY', battery, ['SOC %', 'Current A', 'Voltage V', 'Ready']),
    FMSPID(0x0110, 'BUSTECH_ENGINE', engine, ['Speed km/h', 'Accel Pedal Pos %', 'Torque %']),
]
# max reference torque is 411Nm

pids = {
    p.pid: {
        'name': p.name,
        'fields': p.fieldnames,
        'parse': p,
    } for p in _pids
}

if __name__ == "__main__":
    # make up some frames
    battery_frame = bytearray([0, 0xff, 0x20, 0x16, 0xa, 0x32, 0x7, 1])
    engine_frame = bytearray([0, 0x43, 0x3, 0x33, 0x3, 0x64, 1, 0])
    import json
    print(json.dumps(pids[0x0109]['parse'](battery_frame),indent=4))
    print(json.dumps(pids[0x0110]['parse'](engine_frame),indent=4))
