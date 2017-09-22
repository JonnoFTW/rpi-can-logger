def toInt(bs, a):
    return bs[a] * 256 + bs[a + 1]


def outlander_battery_health(bs):
    return [
        (bs[0] / 2) - 5,  # SOC (%)
        toInt(bs, 27) / 10,  # Batt Health (Ah)
        toInt(bs, 29) / 10,  # Current Charge (Ah)
        toInt(bs, 14) - 400,  # Charge Current (A)
        toInt(bs, 8) / 10,  # Battery Voltage (V)
        bs[31]/4,  # BatMaxIn (kW)
        bs[32]/4,  # BatMaxOut (kW)
        bs[37]/10,  # OR Power Supply (V)
        bs[38]/10,  # IGCT Power Supply
        bs[52]/10,  # Int Resistance dif Max (MOhm)
        ((toInt(bs, 14) - 400) * (toInt(bs, 8)))/1000  # Power (kW)
    ]


def outlander_charges(bs):
    return [
        toInt(bs, 0),
        toInt(bs, 2),
    ]


def outlander_front_rpm(bs):
    return [
        toInt(bs, 2) - 20000
    ]


def outlander_rear_rpm(bs):
    return [
        toInt(bs, 2) - 20000
    ]


# functions to return  value, name and unit
# map the response address to
class PID:
    def __init__(self, name, request, response, pid, parser, fields):
        self.name = name
        self.pid = pid
        self.request = request
        self.response = response
        self.parser = parser
        self.fields = fields

    def __call__(self, bs):
        return dict(zip(self.fields, self.parser(bs)))


_pids = [
    PID('OUTLANDER_BATTERY_HEALTH', 0x761, 0x762, 1, outlander_battery_health,
        ['SOC (%)',
         'Batt Health (Ah)',
         'Current Charge (Ah)',
         'Charge Current (A)',
         'Battery Voltage (V)',
         'BatMaxIn (kW)',
         'BatMaxOut (kW)',
         'OR Power Supply (V)',
         'IGCT Power Supply (V)',
         'Int Resistance dif Max (MOhm)',
         'Power (kW)'
         ]),
    PID('OUTLANDER_CHARGES', 0x765, 0x766, 1, outlander_charges, ['100V Charges (count)', '200V Charges (count)']),
    PID('OUTLANDER_FRONT_RPM', 0x753, 0x754, 2, outlander_front_rpm, ['Front (RPM)']),
    PID('OUTLANDER_REAR_RPM', 0x755, 0x756, 2, outlander_rear_rpm, ['Rear RPM']),

]
pids = {
    p.request:
        {
            'response': p.response,
            'parse': p,
            'name': p.name,
            'pidobj': p,
            'fields': p.fields,
            'pid': p.pid
        } for p in _pids
}
