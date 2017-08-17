# coding=utf-8
from itertools import cycle


def toInt(x):
    return x[0] * 256 + x[1]


class Unit:
    def __call__(self):
        raise NotImplementedError("Please use a Unit.* unit")

    class Special:
        units = ['']

        def __call__(self, bs):
            return bs[0]

    class FuelInjectionDegrees:
        units = ['o']

        def __call__(self, bs):
            return (toInt(bs) / 128) - 210

    class LitresPerHour:
        units = ['L/h']

        def __call__(self, bs):
            return toInt(bs) / 20

    class Percentage:
        units = ['%']

        def __call__(self, bs):
            return bs[0] / 2.55

    class PercentageLoad:
        units = ['%']

        def __call__(self, bs):
            return 100 / 255 * toInt(bs)

    class PercentageHigh:
        units = ['%']

        def __call__(self, bs):
            return (bs[0] / 1.28) - 100

    class Temp:
        units = ['°C']

        def __call__(self, bs):
            return bs[0] - 40

    class TempHigh:
        units = ['°C']

        def __call__(self, bs):
            return toInt(bs) / 10. - 40

    class KiloPascals:
        units = ['kPa']

        def __call__(self, bs):
            return bs[0]

    class KiloPascalsHigh:
        units = ['kPa']

        def __call__(self, bs):
            return bs[0] * 3

    class EvapKiloPascals:
        units = ['Pa']

        def __call__(self, bs):
            return toInt(bs) / 4

    class RPM:
        units = ['RPM']

        def __call__(self, bs):
            return toInt(bs) / 4

    class KilometersPerHour:
        units = ['km/h']

        def __call__(self, bs):
            return bs[0]

    class Degrees:
        units = ['°']

        def __call__(self, bs):
            return (bs[0] / 2) - 64

    class GramsPerSecond:
        units = ['grams/sec']

        def __call__(self, bs):
            return toInt(bs) / 100

    class Voltage:
        units = ['V']

        def __call__(self, bs):
            if bs[1] == 0xff:
                return bs[0] / 200
            else:
                return ((100 / 128) * bs[1]) - 100

    class VoltageHigh:
        units = ['V']

        def __call__(self, bs):
            return toInt(bs) / 1000.

    class Seconds:
        units = ['sec']

        def __call__(self, bs):
            return toInt(bs)

    class Kilometers:
        units = ['km']

        def __call__(self, bs):
            return toInt(bs)

    class OxygenRatioVoltage:
        units = ['ration', 'V']

        def __call__(self, bs):
            return (2 / 65536) * toInt(bs), (8 / 65536.) * toInt(bs[2:4])

    class Count:
        units = ['count']

        def __call__(self, bs):
            return bs[0]

    class FuelAirRatio:
        units = ['ratio']

        def __call__(self, bs):
            return (2 / 65536) * toInt(bs)

    class Pascals:
        units = ['Pa']

        def __call__(self, bs):
            return toInt(bs) / 4

    class OxygenRatioCurrent:
        units = ['ratio', 'mA']

        def __call__(self, bs):
            return (2 / 65536) * toInt(bs), bs[2] + bs[3] / 256. - 128

    class OxygenVoltageTrim:
        units = ['V', '%']

        def __call__(self, bs):
            return bs[0] / 200., 100 / 128 * bs[1] - 100

    class CatalystTemp:
        units = ['°C']

        def __call__(self, bs):
            return toInt(bs) / 10 - 40

    class FuelRailPressure:
        units = ['kPa']

        def __call__(self, bs):
            return 0.079 * toInt(bs)

    class FuelRailGaugePressure:
        units = ['kPa']

        def __call__(self, bs):
            return 10 * toInt(bs)

    class TorquePercentage:
        units = ['%']

        def __call__(self, bs):
            return bs[0] - 125

    class TorqueReference:
        units = ['Nm']

        def __call__(self, bs):
            return toInt(bs)

    class EvapSystemVaporPressureAbs:
        units = ['kPa']

        def __call__(self, bs):
            return toInt(bs) / 200

    class EvapSystemVaporPressure:
        units = ['Pa']

        def __call__(self, bs):
            return toInt(bs) - 32767

    class FuelRailPressureAbsolute:
        units = ['kPa']

        def __call__(self, bs):
            return 10 * toInt(bs)


class PID:
    def __init__(self, pid, name, dtype, fields=None):
        self.pid = pid
        self.name = name
        self.dtype = dtype()
        self.fields = ['{} ({})'.format(name, u) for u in self.dtype.units]
        # if type(fields) in [list, tuple]:
        #     self.fields = fields
        # else:
        #     self.fields = [fields]

    def __call__(self, bs):
        vals = self.dtype(bs)
        if type(vals) not in (tuple, list):
            vals = (vals,)
        return {'{} ({})'.format(pid_name, unit): val for pid_name, val, unit in
                zip(cycle([self.name]), vals, self.dtype.units)}


_pids = [
    PID(0x0103, 'PID_FUEL_SYSTEM_STATUS', Unit.Special, 'fuel_status'),
    PID(0x0104, 'PID_ENGINE_LOAD', Unit.Percentage, 'engine_load'),
    PID(0x0105, 'PID_COOLANT_TEMP', Unit.Temp, 'coolant_temp'),
    PID(0x0106, 'PID_SHORT_TERM_FUEL_TRIM_1', Unit.PercentageHigh, 'field'),
    PID(0x0107, 'PID_LONG_TERM_FUEL_TRIM_1', Unit.PercentageHigh, 'field'),
    PID(0x0108, 'PID_SHORT_TERM_FUEL_TRIM_2', Unit.PercentageHigh, 'field'),
    PID(0x0109, 'PID_LONG_TERM_FUEL_TRIM_2', Unit.PercentageHigh, 'field'),
    PID(0x010A, 'PID_FUEL_PRESSURE', Unit.KiloPascalsHigh, 'field'),
    PID(0x010B, 'PID_INTAKE_MAP', Unit.KiloPascals, 'field'),
    PID(0x010C, 'PID_RPM', Unit.RPM, 'field'),
    PID(0x010D, 'PID_SPEED', Unit.KilometersPerHour, 'field'),
    PID(0x010E, 'PID_TIMING_ADVANCE', Unit.Degrees, 'field'),
    PID(0x010F, 'PID_THROTTLE', Unit.Temp, 'field'),
    PID(0x0110, 'PID_MAF_FLOW', Unit.GramsPerSecond, 'field'),
    PID(0x0111, 'PID_THROTTLE', Unit.Percentage, 'field'),

    PID(0x0112, 'PID_OXYGEN_SENSOR_1', Unit.OxygenVoltageTrim, ['voltage', 'short_term_fuel_trim']),
    PID(0x0113, 'PID_OXYGEN_SENSOR_2', Unit.OxygenVoltageTrim, ['voltage', 'short_term_fuel_trim']),
    PID(0x0114, 'PID_OXYGEN_SENSOR_3', Unit.OxygenVoltageTrim, ['voltage', 'short_term_fuel_trim']),
    PID(0x0115, 'PID_OXYGEN_SENSOR_4', Unit.OxygenVoltageTrim, ['voltage', 'short_term_fuel_trim']),
    PID(0x0116, 'PID_OXYGEN_SENSOR_5', Unit.OxygenVoltageTrim, ['voltage', 'short_term_fuel_trim']),
    PID(0x0117, 'PID_OXYGEN_SENSOR_6', Unit.OxygenVoltageTrim, ['voltage', 'short_term_fuel_trim']),
    PID(0x0118, 'PID_OXYGEN_SENSOR_7', Unit.OxygenVoltageTrim, ['voltage', 'short_term_fuel_trim']),
    PID(0x0119, 'PID_OXYGEN_SENSOR_8', Unit.OxygenVoltageTrim, ['voltage', 'short_term_fuel_trim']),

    PID(0x011E, 'PID_AUX_INPUT', Unit.Special, 'field'),
    PID(0x011F, 'PID_RUNTIME', Unit.Seconds, 'field'),
    PID(0x0121, 'PID_DISTANCE_WITH_MIL', Unit.Kilometers, 'field'),
    PID(0x0122, 'PID_FUEL_RAIL_PRESSURE', Unit.FuelRailPressure, 'fuel'),
    PID(0x0123, 'PID_FUEL_RAIL_GAUGE_PRESSURE', Unit.FuelRailGaugePressure, 'fuel'),
    PID(0x012C, 'PID_COMMANDED_EGR', Unit.Percentage, 'field'),
    PID(0x012D, 'PID_EGR_ERROR', Unit.PercentageHigh, 'field'),
    PID(0x012E, 'PID_COMMANDED_EVAPORATIVE_PURGE', Unit.Percentage, 'field'),
    PID(0x012F, 'PID_FUEL_LEVEL', Unit.Percentage, 'field'),
    PID(0x0130, 'PID_WARMS_UPS', Unit.Count, 'field'),
    PID(0x0131, 'PID_DISTANCE_SINCE_CODES_CLEARED', Unit.Kilometers, 'field'),
    PID(0x0132, 'PID_EVAP_SYS_VAPOR_PRESSURE', Unit.EvapKiloPascals, 'field'),
    PID(0x0133, 'PID_BAROMETRIC', Unit.KiloPascals, 'field'),

    PID(0x0134, 'PID_OXYGEN_SENSOR_1_FUEL', Unit.OxygenRatioCurrent, ['fuel-air_equivalence_ratio', 'current']),
    PID(0x0135, 'PID_OXYGEN_SENSOR_2_FUEL', Unit.OxygenRatioCurrent, ['fuel-air_equivalence_ratio', 'current']),
    PID(0x0136, 'PID_OXYGEN_SENSOR_3_FUEL', Unit.OxygenRatioCurrent, ['fuel-air_equivalence_ratio', 'current']),
    PID(0x0137, 'PID_OXYGEN_SENSOR_4_FUEL', Unit.OxygenRatioCurrent, ['fuel-air_equivalence_ratio', 'current']),
    PID(0x0138, 'PID_OXYGEN_SENSOR_5_FUEL', Unit.OxygenRatioCurrent, ['fuel-air_equivalence_ratio', 'current']),
    PID(0x0139, 'PID_OXYGEN_SENSOR_6_FUEL', Unit.OxygenRatioCurrent, ['fuel-air_equivalence_ratio', 'current']),
    PID(0x013A, 'PID_OXYGEN_SENSOR_7_FUEL', Unit.OxygenRatioCurrent, ['fuel-air_equivalence_ratio', 'current']),
    PID(0x013B, 'PID_OXYGEN_SENSOR_8_FUEL', Unit.OxygenRatioCurrent, ['fuel-air_equivalence_ratio', 'current']),

    PID(0x013C, 'PID_CATALYST_TEMP_B1S1', Unit.CatalystTemp, 'field'),
    PID(0x013D, 'PID_CATALYST_TEMP_B2S1', Unit.CatalystTemp, 'field'),
    PID(0x013E, 'PID_CATALYST_TEMP_B1S2', Unit.CatalystTemp, 'field'),
    PID(0x013F, 'PID_CATALYST_TEMP_B2S2', Unit.CatalystTemp, 'field'),

    PID(0x0142, 'PID_CONTROL_MODULE_VOLTAGE', Unit.VoltageHigh, 'field'),
    PID(0x0143, 'PID_ABSOLUTE_ENGINE_LOAD', Unit.PercentageLoad, 'field'),
    PID(0x0144, 'PID_AIR_FUEL_EQUIV_RATIO', Unit.FuelAirRatio, 'field'),
    PID(0x0145, 'PID_RELATIVE_THROTTLE_POS', Unit.Percentage, 'field'),
    PID(0x0146, 'PID_AMBIENT_TEMP', Unit.Temp, 'field'),
    PID(0x0147, 'PID_ABSOLUTE_THROTTLE_POS_B', Unit.Percentage, 'field'),
    PID(0x0148, 'PID_ABSOLUTE_THROTTLE_POS_C', Unit.Percentage, 'field'),
    PID(0x0149, 'PID_ACC_PEDAL_POS_D', Unit.Percentage, 'field'),
    PID(0x014A, 'PID_ACC_PEDAL_POS_E', Unit.Percentage, 'field'),
    PID(0x014B, 'PID_ACC_PEDAL_POS_F', Unit.Percentage, 'field'),
    PID(0x014C, 'PID_COMMANDED_THROTTLE_ACTUATOR', Unit.Percentage, 'field'),
    PID(0x014D, 'PID_TIME_WITH_MIL', Unit.Seconds, 'minutes'),
    PID(0x014E, 'PID_TIME_SINCE_CODES_CLEARED', Unit.Seconds, 'minutes'),
    PID(0x0152, 'PID_ETHANOL_FUEL', Unit.Percentage, 'field'),
    PID(0x0153, 'PID_EVAP_SYSTEM_VAPOR_PRESSURE_ABS', Unit.EvapSystemVaporPressureAbs, 'field'),
    PID(0x0154, 'PID_EVAP_SYSTEM_VAPOR_PRESSURE', Unit.EvapSystemVaporPressure, 'field'),
    PID(0x0159, 'PID_FUEL_RAIL_PRESSURE_ABS', Unit.FuelRailPressureAbsolute, 'field'),
    PID(0x015B, 'PID_HYBRID_BATTERY_PERCENTAGE', Unit.Percentage, 'field'),
    PID(0x015C, 'PID_ENGINE_OIL_TEMP', Unit.Temp, 'field'),
    PID(0x015D, 'PID_FUEL_INJECTION_TIMING', Unit.FuelInjectionDegrees, 'field'),
    PID(0x015E, 'PID_ENGINE_FUEL_RATE', Unit.LitresPerHour, 'field'),
    PID(0x0161, 'PID_ENGINE_TORQUE_DEMANDED', Unit.TorquePercentage, 'field'),
    PID(0x0162, 'PID_ENGINE_TORQUE_PERCENTAGE', Unit.TorquePercentage, 'field'),
    PID(0x0163, 'PID_ENGINE_REFERENCE_TORQUE', Unit.TorqueReference, 'field'),
]

pids = {
    p.pid: {
        'name': p.name,
        'fields': p.fields,
        'parse': p,
    } for p in _pids
}
