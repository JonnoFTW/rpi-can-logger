import inspect
import re
from itertools import cycle


def PID_TESLA_BMS_CUR_VOLTAGE(msg):
    return [
        (msg[1] * 256 + msg[0]) / 100.,
        (msg[3] & 0x100000) * msg[3] * 256 + msg[2],
        ((msg[6] + (msg[7] & 0x07) << 8)) * 0.1
    ]


def PID_TESLA_REAR_DRIVE_UNIT_INFO(msg):
    return [
        (msg[4] + (msg[5] << 8)) - (512 * (msg[5] & 0x80)),
        msg[6] * 0.4
    ]


def PID_TESLA_REAR_DRIVE_UNIT_TORQUE_STATUS(msg):
    return [
        (msg[1] & 0x70) >> 4,
        (msg[3] & 0x70) >> 4,
        ((msg[0] + ((msg[1] & 0xF) << 8)) - (512 * (msg[1] & 0x8))) / 2,
        (((msg[2] + ((msg[3] & 0xf) << 8)) - 500) / 20) * 1.60934  # convert to a superior unit
    ]


def PID_TESLA_FRONT_DRIVE_UNIT(msg):
    return [
        (msg[5] + ((msg[6] & 0x1f) << 8) - (512 * (msg[6] & 0x10))) / 4.
    ]


def PID_TESLA_FRONT_DRIVE_UNIT_POWER(msg):
    return [
        msg[0] / 10.,
        msg[1] * 125,
        (((msg[6] & 0x3F) << 5) + ((msg[5] & 0xF0) >> 3)) + 1,
        ((msg[2] + ((msg[3] & 0x7) << 8)) - (512 * (msg[3] & 0x4))) / 2.,
        msg[4] + ((msg[5] & 0x7) << 8),
    ]


def PID_TESLA_FRONT_DRIVE_UNIT_TORQUE(msg):
    return [
        ((msg[0] + ((msg[1] & 0xf) << 8)) - (512 * (msg[1] & 0x8))) / 2.
    ]


def PID_TESLA_BATTERY_POWER_LIMITS(msg):
    return [
        (msg[2] + (msg[3] << 8)) / 100.,
        (msg[0] + (msg[1] << 8)) / 100.
    ]


def PID_TESLA_BATTERY_ODOMETER(msg):
    return [
        (msg[0] + (msg[1] << 8) + (msg[2] << 16) + (msg[3] << 24)) / 1000.0
    ]


def PID_TESLA_BATTERY_LIFETIME_ENERGY_STATS(msg):
    return [
        (msg[4] + (msg[5] << 8) + (msg[6] << 16) + (msg[7] << 24)) / 1000.0,
        (msg[0] + (msg[1] << 8) + (msg[2] << 16) + (msg[3] << 24)) / 1000.0
    ]


def PID_TESLA_BATTERY_STATE_OF_CHARGE(msg):
    return [
        (msg[0] + ((msg[1] & 0x3) << 8)) / 10.,
        ((msg[1] >> 2) + ((msg[2] & 0xf) << 6)) / 10.
    ]


def PID_TESLA_BATTERY_ENERGY_STATUS(msg):
    return [
        (msg[0] + ((msg[1] & 0x3) << 8)) / 10.0,
        ((msg[1] >> 2) + ((msg[2] & 0xf) * 64)) / 10.,
        ((msg[2] >> 4) + ((msg[3] & 0x3f) * 16)) / 10.,
        ((msg[3] >> 6) + ((msg[4] & 0xff) * 4)) / 10.,
        ((msg[6] >> 2) + ((msg[7] & 0x03) * 64)) / 10.,
        (msg[5] + ((msg[6] & 0x03) << 8)) / 10.
    ]


def PID_TESLA_DC_DC_CONVERTER_STATUS(msg):
    return [
        ((msg[2] - (2 * (msg[2] & 0x80))) / 2) + 40,
        msg[3] * 16,
        msg[4],
        msg[4] * (msg[5] / 10.),
        msg[5] / 10
    ]


def PID_TESLA_CRUISE_CONTROL(msg):
    return {}


def PID_TESLA_REAR_DRIVE_UNIT_MEASUREMENT(msg):
    return [
        (msg[5] + ((msg[6] & 0x1f) << 8) - (512 * (msg[6] & 0x10))) / 4,
        msg[2] * 0.4,
        msg[3] * 0.4
    ]


def PID_TESLA_REAR_DRIVE_UNIT_POWER(msg):
    return [
        msg[0] / 10.,
        msg[1] * 125,
        (((msg[6] & 0x3F) << 5) + ((msg[5] & 0xF0) >> 3)) + 1,
        ((msg[2] + ((msg[3] & 0x7) << 8)) - (512 * (msg[3] & 0x4))) / 2.,
        msg[4] + ((msg[5] & 0x7) << 8),
        (msg[7] * 4) - 200
    ]


class PID:
    def __init__(self, pid, name, parse, fields):
        self.pid = pid
        self.name = name
        self.parser = parse
        self.fields = fields

    def __call__(self, msg):
        parsed = self.parser(msg)
        if type(parsed) not in [tuple, list]:
            parsed = (parsed,)
        return {'{} ({})'.format(pid_name, unit): val for pid_name, val, unit in
                zip(cycle([self.name]), parsed, self.fields)}


_pids = [
    PID(0x0102, 'PID_TESLA_BMS_CUR_VOLTAGE', PID_TESLA_BMS_CUR_VOLTAGE, ['battery_voltage',
                                                                         'regen_current',
                                                                         'temp']),
    PID(0x0106, 'PID_TESLA_REAR_DRIVE_UNIT_INFO', PID_TESLA_REAR_DRIVE_UNIT_INFO, ['motorRPM',
                                                                                   'pedalPos']),
    PID(0x0154, 'PID_TESLA_REAR_DRIVE_UNIT_MEASUREMENT', PID_TESLA_REAR_DRIVE_UNIT_MEASUREMENT, ['torqueMeasured'
                                                                                                 'pedalPosA'
                                                                                                 'pedalPosB']),
    PID(0x0266, 'PID_TESLA_REAR_DRIVE_UNIT_POWER', PID_TESLA_REAR_DRIVE_UNIT_POWER,
        ['inverter12V', 'dissipation', 'drivePowerMax', 'mechPower', 'statorCurrent', 'regenPowerMax']),
    PID(0x0116, 'PID_TESLA_REAR_DRIVE_UNIT_TORQUE_STATUS', PID_TESLA_REAR_DRIVE_UNIT_TORQUE_STATUS, ['gear',
                                                                                                     'gearRequest',
                                                                                                     'torqueEstimate',
                                                                                                     'vehicleSpeed']),
    PID(0x01D4, 'PID_TESLA_FRONT_DRIVE_UNIT', PID_TESLA_FRONT_DRIVE_UNIT, ['torqueMeasured']),
    PID(0x02E5, 'PID_TESLA_FRONT_DRIVE_UNIT_POWER', PID_TESLA_FRONT_DRIVE_UNIT_POWER, ['inverter12V',
                                                                                       'dissipation',
                                                                                       'drivePowerMax',
                                                                                       'mechPower',
                                                                                       'statorCurrent']),
    PID(0x0145, 'PID_TESLA_FRONT_DRIVE_UNIT_TORQUE', PID_TESLA_FRONT_DRIVE_UNIT_TORQUE, ['torqueEstimate']),
    PID(0x0232, 'PID_TESLA_BATTERY_POWER_LIMITS', PID_TESLA_BATTERY_POWER_LIMITS, ['maxDischargePower'
                                                                                   'maxRegenPower']),
    PID(0x0562, 'PID_TESLA_BATTERY_ODOMETER', PID_TESLA_BATTERY_ODOMETER, ['batteryOdometer']),
    PID(0x03D2, 'PID_TESLA_BATTERY_LIFETIME_ENERGY_STATS', PID_TESLA_BATTERY_LIFETIME_ENERGY_STATS, ['kwhChargeTotal',
                                                                                                     'kwhDischargeTotal']),
    PID(0x0302, 'PID_TESLA_BATTERY_STATE_OF_CHARGE', PID_TESLA_BATTERY_STATE_OF_CHARGE, ['socMin',
                                                                                         'socUI']),
    PID(0x0382, 'PID_TESLA_BATTERY_ENERGY_STATUS', PID_TESLA_BATTERY_ENERGY_STATUS, ['nominalFullPackEnergy',
                                                                                     'nominalEnergyRemaining',
                                                                                     'expectedEnergyRemaining',
                                                                                     'idealEnergyRemaining',
                                                                                     'energyBuffer',
                                                                                     'energyToChargeComplete']),
    PID(0x0210, 'PID_TESLA_DC_DC_CONVERTER_STATUS', PID_TESLA_DC_DC_CONVERTER_STATUS, ['inletTemperature',
                                                                                       'inputPower',
                                                                                       'outputCurrent',
                                                                                       'outputPower',
                                                                                       'outputVoltage']),
    PID(0x0256, 'PID_TESLA_CRUISE_CONTROL', PID_TESLA_CRUISE_CONTROL, [])
]

pids = {
    p.pid: {
        'name': p.name,
        'fields': p.fields,
        'parse': p,
    } for p in _pids
}
