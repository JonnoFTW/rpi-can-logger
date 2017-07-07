import inspect
import re


def PID_TESLA_BMS_CUR_VOLTAGE(msg):
    return {
        'battery_voltage': (msg[1] * 256 + msg[0]) / 100.,
        # 'regen_current': (msg[3]&0x100000) * msg[3]*256 + msg[2],
        'temp': ((msg[6] + (msg[7] & 0x07) << 8)) * 0.1
    }


def PID_TESLA_REAR_DRIVE_UNIT_INFO(msg):
    return {
        'motorRPM': (msg[4] + (msg[5] << 8)) - (512 * (msg[5] & 0x80)),
        'pedalPos': msg[6] * 0.4
    }


def PID_TESLA_REAR_DRIVE_UNIT_TORQUE_STATUS(msg):
    return {
        'gear': (msg[1] & 0x70) >> 4,
        'gearRequest': (msg[3] & 0x70) >> 4,
        'torqueEstimate': ((msg[0] + ((msg[1] & 0xF) << 8)) - (512 * (msg[1] & 0x8))) / 2,
        'vehicleSpeed': ((msg[2] + ((msg[3] & 0xf) << 8)) - 500) / 20
    }


def PID_TESLA_FRONT_DRIVE_UNIT(msg):
    return {
        'torqueMeasured': (msg[5] + ((msg[6] & 0x1f) << 8) - (512 * (msg[6] & 0x10))) / 4.
    }


def PID_TESLA_FRONT_DRIVE_UNIT_POWER(msg):
    return {
        'inverter12V': msg[0] / 10.,
        'dissipation': msg[1] * 125,
        'drivePowerMax': (((msg[6] & 0x3F) << 5) + ((msg[5] & 0xF0) >> 3)) + 1,
        'mechPower': ((msg[2] + ((msg[3] & 0x7) << 8)) - (512 * (msg[3] & 0x4))) / 2.,
        'statorCurrent': msg[4] + ((msg[5] & 0x7) << 8),
    }


def PID_TESLA_FRONT_DRIVE_UNIT_TORQUE(msg):
    return {
        'torqueEstimate': ((msg[0] + ((msg[1] & 0xf) << 8)) - (512 * (msg[1] & 0x8))) / 2.
    }


def PID_TESLA_BATTERY_POWER_LIMITS(msg):
    return {
        'maxDischargePower': (msg[2] + (msg[3] << 8)) / 100.,
        'maxRegenPower': (msg[0] + (msg[1] << 8)) / 100.
    }


def PID_TESLA_BATTERY_ODOMETER(msg):
    return {
        'batteryOdometer': (msg[0] + (msg[1] << 8) + (msg[2] << 16) + (msg[3] << 24)) / 1000.0
    }


def PID_TESLA_BATTERY_LIFETIME_ENERGY_STATS(msg):
    return {
        'kwhChargeTotal': (msg[4] + (msg[5] << 8) + (msg[6] << 16) + (msg[7] << 24)) / 1000.0,
        'kwhDischargeTotal': (msg[0] + (msg[1] << 8) + (msg[2] << 16) + (msg[3] << 24)) / 1000.0
    }


def PID_TESLA_BATTERY_STATE_OF_CHARGE(msg):
    return {
        'socMin': (msg[0] + ((msg[1] & 0x3) << 8)) / 10.,
        'socUI': ((msg[1] >> 2) + ((msg[2] & 0xf) << 6)) / 10.
    }


def PID_TESLA_BATTERY_ENERGY_STATUS(msg):
    return {
        'nominalFullPackEnergy': (msg[0] + ((msg[1] & 0x3) << 8)) / 10.0,
        'nominalEnergyRemaining': ((msg[1] >> 2) + ((msg[2] & 0xf) * 64)) / 10.,
        'expectedEnergyRemaining': ((msg[2] >> 4) + ((msg[3] & 0x3f) * 16)) / 10.,
        'idealEnergyRemaining': ((msg[3] >> 6) + ((msg[4] & 0xff) * 4)) / 10.,
        'energyBuffer': ((msg[6] >> 2) + ((msg[7] & 0x03) * 64)) / 10.,
        'energyToChargeComplete': (msg[5] + ((msg[6] & 0x03) << 8)) / 10.
    }


def PID_TESLA_DC_DC_CONVERTER_STATUS(msg):
    return {
        'inletTemperature': ((msg[2] - (2 * (msg[2] & 0x80))) / 2) + 40,
        'inputPower': msg[3] * 16,
        'outputCurrent': msg[4],
        'outputPower': msg[4] * (msg[5] / 10.),
        'outputVoltage': msg[5] / 10
    }


def PID_TESLA_CRUISE_CONTROL(msg):
    return {}


def PID_TESLA_REAR_DRIVE_UNIT_MEASUREMENT(msg):
    return {
        'torqueMeasured': (msg[5] + ((msg[6] & 0x1f) << 8) - (512 * (msg[6] & 0x10))) / 4,
        'pedalPosA': msg[2] * 0.4,
        'pedalPosB': msg[3] * 0.4
    }


def PID_TESLA_REAR_DRIVE_UNIT_POWER(msg):
    return {
        'inverter12V': msg[0] / 10.,
        'dissipation': msg[1] * 125,
        'drivePowerMax': (((msg[6] & 0x3F) << 5) + ((msg[5] & 0xF0) >> 3)) + 1,
        'mechPower': ((msg[2] + ((msg[3] & 0x7) << 8)) - (512 * (msg[3] & 0x4))) / 2.,
        'statorCurrent': msg[4] + ((msg[5] & 0x7) << 8),
        'regenPowerMax': (msg[7] * 4) - 200
    }


pids = {
    0x0102: {
        'name': 'PID_TESLA_BMS_CUR_VOLTAGE',
        'parse': PID_TESLA_BMS_CUR_VOLTAGE
    },
    0x0106: {
        'name': 'PID_TESLA_REAR_DRIVE_UNIT_INFO',
        'parse': PID_TESLA_REAR_DRIVE_UNIT_INFO
    },
    0x0154: {
        'name': 'PID_TESLA_REAR_DRIVE_UNIT_MEASUREMENT',
        'parse': PID_TESLA_REAR_DRIVE_UNIT_MEASUREMENT}
    ,
    0x0266: {
        'name': 'PID_TESLA_REAR_DRIVE_UNIT_POWER',
        'parse': PID_TESLA_REAR_DRIVE_UNIT_POWER
    },
    0x0116: {
        'name': 'PID_TESLA_REAR_DRIVE_UNIT_TORQUE_STATUS',
        'parse': PID_TESLA_REAR_DRIVE_UNIT_TORQUE_STATUS
    },
    0x01D4: {
        'name': 'PID_TESLA_FRONT_DRIVE_UNIT',
        'parse': PID_TESLA_FRONT_DRIVE_UNIT
    },
    0x02E5: {
        'name': 'PID_TESLA_FRONT_DRIVE_UNIT_POWER',
        'parse': PID_TESLA_FRONT_DRIVE_UNIT_POWER
    },
    0x0145: {
        'name': 'PID_TESLA_FRONT_DRIVE_UNIT_TORQUE',
        'parse': PID_TESLA_FRONT_DRIVE_UNIT_TORQUE
    },
    0x0232: {
        'name': 'PID_TESLA_BATTERY_POWER_LIMITS',
        'parse': PID_TESLA_BATTERY_POWER_LIMITS
    },
    0x0562: {
        'name': 'PID_TESLA_BATTERY_ODOMETER',
        'parse': PID_TESLA_BATTERY_ODOMETER
    },
    0x03D2: {
        'name': 'PID_TESLA_BATTERY_LIFETIME_ENERGY_STATS',
        'parse': PID_TESLA_BATTERY_LIFETIME_ENERGY_STATS
    },
    0x0302: {
        'name': 'PID_TESLA_BATTERY_STATE_OF_CHARGE',
        'parse': PID_TESLA_BATTERY_STATE_OF_CHARGE
    },
    0x0382: {
        'name': 'PID_TESLA_BATTERY_ENERGY_STATUS',
        'parse': PID_TESLA_BATTERY_ENERGY_STATUS
    },
    0x0210: {
        'name': 'PID_TESLA_DC_DC_CONVERTER_STATUS',
        'parse': PID_TESLA_DC_DC_CONVERTER_STATUS
    },
    0x0256: {
        'name': 'PID_TESLA_CRUISE_CONTROL',
        'parse': PID_TESLA_CRUISE_CONTROL
    },
}

for pid, data in pids.items():
    pids[pid]['fields'] = re.findall(r"\s[^#]\s*'(.*)'", inspect.getsource(data['parse']))
