def toInt(bs, a):
    return bs[a] * 256 + bs[a + 1]


def outlander_battery_health(bs):
    return {
        'SOC (%)': (bs[0] / 2) - 5,
        'Batt Health (Ah)': toInt(bs, 27) / 10,
        'Current Charge (Ah)': toInt(bs, 29) / 10,
        'Charge Current  (V)': toInt(bs, 14) - 1,
        'Battery Total Voltage (V)': toInt(bs, 8) / 10
    }


def outlander_charges(bs):
    return {
        '100V Charges (count)': toInt(bs, 0),
        '200V Charges (count)': toInt(bs, 2),
    }


def outlander_front_rpm(bs):
    return {
        'Front (RPM)': toInt(bs, 2) - 20000
    }


def outlander_rear_rpm(bs):
    return {
        'Rear (RPM)': toInt(bs, 2) - 20000
    }


# functions to return  value, name and unit
# map the response address to
class PID:
    def __init__(self, name, request, response, pid, parser):
        self.name = name
        self.pid = pid
        self.request = request
        self.response = response
        self.parser = parser

    def __call__(self, bs):
        return self.parser(bs)


_pids = [
    PID('outlander_battery_health', 0x761, 0x762, 1, outlander_battery_health),
    PID('outlander_charges', 0x765, 0x766, 1, outlander_charges),
    PID('outlander_front_rpm', 0x753, 0x754, 2, outlander_front_rpm),
    PID('outlander_rear_rpm', 0x755, 0x756, 2, outlander_rear_rpm),

]
pids = {
    p.response:
        {
            'request': p.request,
            'parse': p.parser,
            'name': p.name,
            'pidobj': p,
            'pid': p.pid
        } for p in _pids
}
